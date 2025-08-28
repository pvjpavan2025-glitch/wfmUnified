"""
Rules Engine Service main application.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
import structlog

from shared.config import settings
from shared.database import db_manager
from shared.logging import setup_logging
from shared.auth import get_current_user, TokenData
from .service import RulesService
from .repository import RulesRepository
from .models import RuleCreate, RuleUpdate, RuleResponse, RuleEvaluationRequest
import httpx

# Setup logging
logger = setup_logging("rules-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Rules Engine Service")
    await db_manager.connect_mongodb()
    await db_manager.connect_redis()
    logger.info("Rules Engine Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Rules Engine Service")
    await db_manager.close()
    logger.info("Rules Engine Service shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="WFM Rules Engine Service",
    description="Rules engine and workflow processing service for Workforce Management",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging is now handled by structured logging setup


# Dependency to get service instance
async def get_rules_service() -> RulesService:
    """Get rules service instance."""
    database = await db_manager.get_database()
    redis_client = await db_manager.get_redis()
    rules_repo = RulesRepository(database)
    return RulesService(rules_repo, redis_client)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "rules-service"}


# Rules endpoints
@app.post("/rules", response_model=RuleResponse)
async def create_rule(
    rule_data: RuleCreate,
    rules_service: RulesService = Depends(get_rules_service),
    current_user: TokenData = Depends(get_current_user)
):
    """Create a new rule."""
    try:
        rule = await rules_service.create_rule(rule_data, current_user.user_id)
        return RuleResponse(**rule)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Create rule failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.get("/rules/{rule_id}", response_model=RuleResponse)
async def get_rule(
    rule_id: str,
    rules_service: RulesService = Depends(get_rules_service),
    current_user: TokenData = Depends(get_current_user)
):
    """Get rule by ID."""
    rule = await rules_service.get_rule(rule_id, current_user.tenant_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found"
        )
    return RuleResponse(**rule)


@app.put("/rules/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: str,
    rule_data: RuleUpdate,
    rules_service: RulesService = Depends(get_rules_service),
    current_user: TokenData = Depends(get_current_user)
):
    """Update rule."""
    rule = await rules_service.update_rule(
    rule_id, current_user.tenant_id, rule_data, current_user.user_id
    )
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found"
        )
    return RuleResponse(**rule)


@app.delete("/rules/{rule_id}")
async def delete_rule(
    rule_id: str,
    rules_service: RulesService = Depends(get_rules_service),
    current_user: TokenData = Depends(get_current_user)
):
    """Delete rule."""
    success = await rules_service.delete_rule(rule_id, current_user.tenant_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found"
        )
    return {"message": "Rule deleted successfully"}


@app.get("/rules", response_model=list[RuleResponse])
async def list_rules(
    skip: int = 0,
    limit: int = 100,
    rules_service: RulesService = Depends(get_rules_service),
    current_user: TokenData = Depends(get_current_user)
):
    """List rules."""
    rules = await rules_service.list_rules(current_user.tenant_id, skip, limit)
    return [RuleResponse(**rule) for rule in rules]


@app.post("/rules/evaluate")
async def evaluate_rules(
    evaluation_request: RuleEvaluationRequest,
    rules_service: RulesService = Depends(get_rules_service),
    current_user: TokenData = Depends(get_current_user)
):
    """Evaluate rules against input data."""
    try:
        result = await rules_service.evaluate_rules(
            evaluation_request.data,
            current_user.tenant_id,
            rule_ids=evaluation_request.rule_ids,
            category=evaluation_request.category,
            orchestrate=evaluation_request.orchestrate,
            split_jobs=evaluation_request.split_jobs,
            auto_schedule=evaluation_request.auto_schedule,
        )
        return result
    except Exception as e:
        logger.error(f"Rule evaluation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Rule evaluation failed"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "rules_service.main:app",
        host="0.0.0.0",
        port=8003,
        reload=True
    ) 


@app.post("/orders/process-ready")
async def process_ready_orders(
    rules_service: RulesService = Depends(get_rules_service),
    current_user: TokenData = Depends(get_current_user)
):
    """Fetch READY orders from Order Service and evaluate rules for each.
    Note: lightweight orchestrator; uses Scheduler via existing evaluate_rules path.
    """
    order_base = os.getenv("ORDER_SERVICE_URL", "http://order-service:8008").rstrip("/")
    # Mint token by reusing gateway-compatible token manager
    from shared.auth import token_manager
    access = token_manager.create_access_token({
        "user_id": "rules-service",
        "username": "rules",
        "tenant_id": current_user.tenant_id,
        "roles": ["admin"],
    })
    headers = {"Authorization": f"Bearer {access}"}
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(f"{order_base}/orders/ready", headers=headers)
        r.raise_for_status()
        orders = r.json()
    results = []
    for o in orders:
        data = o.get("payload", {})
        # ensure we carry the DB order id for correlation; also keep externalId for naming
        if not data.get("order_id"):
            data["order_id"] = o.get("id") or o.get("_id")
        if not data.get("externalId") and o.get("external_id"):
            data["externalId"] = o.get("external_id")
        res = await rules_service.evaluate_rules(data, current_user.tenant_id, orchestrate=True, split_jobs=False, auto_schedule=True)
        results.append({
            "order_id": data.get("order_id") or o.get("id") or o.get("_id"),
            "external_id": o.get("external_id"),
            "result": res
        })
    return {"processed": len(results), "results": results}