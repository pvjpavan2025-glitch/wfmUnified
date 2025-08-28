"""
API Gateway main application.
"""
import os
from contextlib import asynccontextmanager
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, status, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import structlog
from jose import jwt
from passlib.hash import bcrypt
from datetime import datetime, timedelta

from shared.config import settings
from shared.database import db_manager
from shared.logging import setup_logging
# RequestLoggingMiddleware
from shared.auth import get_current_user, token_manager
from bson import ObjectId

from .router import APIRouter
from .middleware import RateLimitMiddleware, CorrelationMiddleware

# Setup logging
logger = setup_logging("api-gateway")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager.

    Always attempt to connect to external dependencies (MongoDB/Redis) on startup.
    Failures are logged but do not prevent the app from starting so that liveness
    checks remain responsive even if dependencies are temporarily unavailable.
    """
    logger.info("Starting API Gateway")
    try:
        await db_manager.connect_mongodb()
    except Exception as e:
        logger.error(f"MongoDB connect failed at startup: {e}")
    try:
        await db_manager.connect_redis()
    except Exception as e:
        logger.error(f"Redis connect failed at startup: {e}")
    logger.info("API Gateway startup sequence completed")

    yield

    logger.info("Shutting down API Gateway")
    try:
        await db_manager.close()
    except Exception as e:
        logger.error(f"Error during shutdown close: {e}")
    logger.info("API Gateway shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="WFM API Gateway",
    description="API Gateway for Workforce Management Microservices",
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

# Add custom middleware
app.middleware(CorrelationMiddleware)
app.middleware(RateLimitMiddleware)
# app.middleware(RequestLoggingMiddleware)


def _env(name: str, default: str) -> str:
    val = os.getenv(name, "").strip()
    return val or default

SERVICE_URLS = {
    # Defaults intentionally empty in Azure (no in-container DNS like docker-compose)
    "auth": _env("AUTH_SERVICE_URL", "http://localhost:8001"),
    "order": _env("ORDER_SERVICE_URL", "http://localhost:8002"),
    "config": _env("CONFIG_SERVICE_URL", "http://localhost:8008"),
    "rules": _env("RULES_SERVICE_URL", "http://localhost:8003"),
    "scheduler": _env("SCHEDULER_SERVICE_URL", "http://localhost:8004"),
    "issue": _env("ISSUE_SERVICE_URL", "http://localhost:8005"),
    "analytics": _env("ANALYTICS_SERVICE_URL", "http://localhost:8006"),
    "vendor": _env("VENDOR_SERVICE_URL", "http://localhost:8007"),
    "dashboard": _env("DASHBOARD_SERVICE_URL", ""),
}


# Health check endpoint (liveness)
@app.get("/health")
async def health_check():
    """Liveness probe: returns 200 if the process is up."""
    return {"status": "ok", "service": "api-gateway"}


# Readiness check endpoint (dependencies)
@app.get("/ready")
async def readiness_check():
    """Readiness probe: verify MongoDB and Redis connectivity."""
    status_map: Dict[str, Any] = {"mongo": "unknown", "redis": "unknown"}
    try:
        db = await db_manager.get_database()
        # Lightweight check: list collections command requires connectivity
        await db.command("ping")
        status_map["mongo"] = "ok"
    except Exception as e:
        status_map["mongo"] = f"error: {e}"
    try:
        r = await db_manager.get_redis()
        await r.ping()
        status_map["redis"] = "ok"
    except Exception as e:
        status_map["redis"] = f"error: {e}"
    http_status = status.HTTP_200_OK if all(v == "ok" for v in status_map.values()) else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(content={"status": status_map}, status_code=http_status)


# Service health check
@app.get("/health/services")
async def services_health_check():
    """Check health of all downstream services (best-effort)."""
    health_status = {}
    async with httpx.AsyncClient() as client:
        for service_name, service_url in SERVICE_URLS.items():
            try:
                response = await client.get(f"{service_url}/health", timeout=5.0)
                health_status[service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response_time": response.elapsed.total_seconds()
                }
            except Exception as e:
                health_status[service_name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
    return health_status


# Authentication endpoints - Direct implementation instead of forwarding
@app.post("/auth/login")
async def login(request: Request):
    """Login endpoint - direct implementation."""
    try:
        try:
            body = await request.json()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON body"
            )
        username = body.get("username")
        password = body.get("password")
        tenant_id = body.get("tenant_id")
        
        if not username or not password or not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username, password, and tenant_id are required"
            )
        
        # Get database connection
        database = await db_manager.get_database()
        if database is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection failed"
            )
        
        # Find user
        user = await database.users.find_one({
            "username": username,
            "tenant_id": ObjectId(tenant_id),
            "status": "active"
        })
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Verify password
        if not bcrypt.verify(password, user['password_hash']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Get user roles
        roles = []
        if user.get('role_ids'):
            role_cursor = database.roles.find({"_id": {"$in": user['role_ids']}})
            roles = [role['name'] async for role in role_cursor]
        
        # Debug: Log the user data being used for token creation
        logger.info(f"Login: User found in database: {user}")
        logger.info(f"Login: User ID type: {type(user['_id'])}")
        logger.info(f"Login: User ID value: {user['_id']}")
        logger.info(f"Login: User ID as string: {str(user['_id'])}")
        
        # Create JWT access token using shared token manager so it contains the required 'type' claim
        access_token_payload = {
            "user_id": str(user["_id"]),
            "username": user["username"],
            "tenant_id": str(user["tenant_id"]),
            "roles": roles
        }
        token = token_manager.create_access_token(access_token_payload)
        
        # Update last login
        await database.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.utcnow(), "failed_login_attempts": 0}}
        )
        
        # Return user info and token
        user_response = {
            "id": str(user["_id"]),
            "username": user["username"],
            "email": user["email"],
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "roles": roles,
            "tenant_id": str(user["tenant_id"]),
            "status": user["status"],
            "permissions": []  # TODO: Add permissions logic
        }
        
        return {
            "access_token": token,
            # Use configured expiration from shared settings
            "expires_in": settings.security.jwt_expiration_minutes * 60,
            "user": user_response
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.post("/auth/verify")
async def verify_token_endpoint(request: Request):
    """Verify token endpoint - direct implementation."""
    logger.info("🔍 VERIFY ENDPOINT CALLED - Starting token verification")
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header"
            )
        
        token = auth_header.split(" ")[1]
        
        # Decode and verify token
        logger.info(f"Verifying token: {token[:50]}...")
        logger.info(f"Using JWT secret: {settings.security.jwt_secret_key[:20]}...")
        logger.info(f"Using JWT algorithm: {settings.security.jwt_algorithm}")
        
        try:
            payload = jwt.decode(token, settings.security.jwt_secret_key, algorithms=[settings.security.jwt_algorithm])
            logger.info(f"JWT decode successful, payload: {payload}")
        except Exception as e:
            logger.error(f"JWT decode failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )
        
        # Get database connection
        database = await db_manager.get_database()
        if database is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection failed"
            )
        
        # Find user
        logger.info(f"Looking for user with ID: {payload['user_id']}")
        logger.info(f"User ID type: {type(payload['user_id'])}")
        
        # Check if collections exist
        collections = await database.list_collection_names()
        logger.info(f"Available collections: {collections}")
        
        if "users" not in collections:
            logger.error("Users collection does not exist")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Users collection not found"
            )
        
        # Convert string user_id to ObjectId
        from bson import ObjectId
        try:
            user_object_id = ObjectId(payload["user_id"])
        except Exception as e:
            logger.error(f"Invalid user ID format: {payload['user_id']}, error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user ID format"
            )
        
        user = await database.users.find_one({
            "_id": user_object_id
        })
        
        logger.info(f"User lookup result: {user}")
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Check if user is active (if status field exists)
        if user.get("status") and user["status"] != "active":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is not active"
            )
        
        # Get user roles
        roles = []
        if user.get('role_ids'):
            role_cursor = database.roles.find({"_id": {"$in": user['role_ids']}})
            roles = [role['name'] async for role in role_cursor]
        
        user_response = {
            "id": str(user["_id"]),
            "username": user["username"],
            "email": user["email"],
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "roles": roles,
            "tenant_id": str(user["tenant_id"]),
            "status": user["status"],
            "permissions": []
        }
        
        return {"valid": True, "user": user_response}
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# Local development helper: mint a test token signed with the container secret
@app.post("/auth/token/test")
async def mint_test_token(request: Request):
    """Mint a short-lived access token using the container's JWT secret for local testing.

    Body (optional): {"user_id", "username", "tenant_id", "roles", "expires_in_minutes"}
    Defaults: user_id="local-dev", username="devuser", tenant_id="default-tenant", roles=["admin"], expires_in_minutes=30
    """
    try:
        try:
            body = await request.json()
        except Exception:
            body = {}

        user_id = body.get("user_id", "local-dev")
        username = body.get("username", "devuser")
        tenant_id = body.get("tenant_id", "default-tenant")
        roles = body.get("roles", ["admin"]) or ["admin"]

        # Use token_manager to ensure correct claims including "type": "access"
        token = token_manager.create_access_token({
            "user_id": user_id,
            "username": username,
            "tenant_id": tenant_id,
            "roles": roles,
        })

        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": settings.security.jwt_expiration_minutes * 60,
            "user": {
                "id": user_id,
                "username": username,
                "tenant_id": tenant_id,
                "roles": roles,
            },
        }
    except Exception as e:
        logger.error(f"Token mint error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mint token"
        )


# User management endpoints
@app.post("/users")
async def create_user(request: Request):
    """Create user endpoint - forwards to auth service."""
    return await forward_request(request, "auth", "/users")


@app.get("/users/{user_id}")
async def get_user(user_id: str, request: Request):
    """Get user endpoint - forwards to auth service."""
    return await forward_request(request, "auth", f"/users/{user_id}")


@app.put("/users/{user_id}")
async def update_user(user_id: str, request: Request):
    """Update user endpoint - forwards to auth service."""
    return await forward_request(request, "auth", f"/users/{user_id}")


@app.delete("/users/{user_id}")
async def delete_user(user_id: str, request: Request):
    """Delete user endpoint - forwards to auth service."""
    return await forward_request(request, "auth", f"/users/{user_id}")


@app.get("/users")
async def list_users(request: Request):
    """List users endpoint - forwards to auth service."""
    return await forward_request(request, "auth", "/users")


# Configuration endpoints
@app.post("/configs")
async def create_config(request: Request):
    """Create config endpoint - forwards to config service."""
    return await forward_request(request, "config", "/configs")


@app.get("/configs/{config_id}")
async def get_config(config_id: str, request: Request):
    """Get config endpoint - forwards to config service."""
    return await forward_request(request, "config", f"/configs/{config_id}")


@app.put("/configs/{config_id}")
async def update_config(config_id: str, request: Request):
    """Update config endpoint - forwards to config service."""
    return await forward_request(request, "config", f"/configs/{config_id}")


@app.delete("/configs/{config_id}")
async def delete_config(config_id: str, request: Request):
    """Delete config endpoint - forwards to config service."""
    return await forward_request(request, "config", f"/configs/{config_id}")


@app.get("/configs")
async def list_configs(request: Request):
    """List configs endpoint - forwards to config service."""
    return await forward_request(request, "config", "/configs")


@app.get("/configs/key/{key}")
async def get_config_by_key(key: str, request: Request):
    """Get config by key endpoint - forwards to config service."""
    return await forward_request(request, "config", f"/configs/key/{key}")


# Rules service endpoints
@app.post("/rules")
async def create_rule(request: Request):
    """Create rule endpoint - forwards to rules service."""
    return await forward_request(request, "rules", "/rules")


@app.get("/rules/{rule_id}")
async def get_rule(rule_id: str, request: Request):
    """Get rule endpoint - forwards to rules service."""
    return await forward_request(request, "rules", f"/rules/{rule_id}")


@app.put("/rules/{rule_id}")
async def update_rule(rule_id: str, request: Request):
    """Update rule endpoint - forwards to rules service."""
    return await forward_request(request, "rules", f"/rules/{rule_id}")


@app.delete("/rules/{rule_id}")
async def delete_rule(rule_id: str, request: Request):
    """Delete rule endpoint - forwards to rules service."""
    return await forward_request(request, "rules", f"/rules/{rule_id}")


@app.get("/rules")
async def list_rules(request: Request):
    """List rules endpoint - forwards to rules service."""
    return await forward_request(request, "rules", "/rules")


@app.post("/rules/evaluate")
async def evaluate_rules(request: Request):
    """Evaluate rules endpoint - forwards to rules service."""
    return await forward_request(request, "rules", "/rules/evaluate")


# Scheduler service endpoints
@app.post("/jobs")
async def create_job(request: Request):
    """Create job endpoint - forwards to scheduler service."""
    return await forward_request(request, "scheduler", "/jobs")


@app.get("/jobs/{job_id}")
async def get_job(job_id: str, request: Request):
    """Get job endpoint - forwards to scheduler service."""
    return await forward_request(request, "scheduler", f"/jobs/{job_id}")


@app.put("/jobs/{job_id}")
async def update_job(job_id: str, request: Request):
    """Update job endpoint - forwards to scheduler service."""
    return await forward_request(request, "scheduler", f"/jobs/{job_id}")


@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str, request: Request):
    """Delete job endpoint - forwards to scheduler service."""
    return await forward_request(request, "scheduler", f"/jobs/{job_id}")


@app.get("/jobs")
async def list_jobs(request: Request):
    """List jobs endpoint - forwards to scheduler service."""
    return await forward_request(request, "scheduler", "/jobs")


@app.post("/jobs/{job_id}/schedule")
async def schedule_job(job_id: str, request: Request):
    """Schedule job endpoint - forwards to scheduler service."""
    return await forward_request(request, "scheduler", f"/jobs/{job_id}/schedule")


# Issue service endpoints
@app.post("/issues")
async def create_issue(request: Request):
    """Create issue endpoint - forwards to issue service."""
    return await forward_request(request, "issue", "/issues")


@app.get("/issues/{issue_id}")
async def get_issue(issue_id: str, request: Request):
    """Get issue endpoint - forwards to issue service."""
    return await forward_request(request, "issue", f"/issues/{issue_id}")


@app.put("/issues/{issue_id}")
async def update_issue(issue_id: str, request: Request):
    """Update issue endpoint - forwards to issue service."""
    return await forward_request(request, "issue", f"/issues/{issue_id}")


@app.delete("/issues/{issue_id}")
async def delete_issue(issue_id: str, request: Request):
    """Delete issue endpoint - forwards to issue service."""
    return await forward_request(request, "issue", f"/issues/{issue_id}")


@app.get("/issues")
async def list_issues(request: Request):
    """List issues endpoint - forwards to issue service."""
    return await forward_request(request, "issue", "/issues")


@app.post("/issues/{issue_id}/escalate")
async def escalate_issue(issue_id: str, request: Request):
    """Escalate issue endpoint - forwards to issue service."""
    return await forward_request(request, "issue", f"/issues/{issue_id}/escalate")


# Analytics service endpoints
@app.get("/reports")
async def list_reports(request: Request):
    """List reports endpoint - forwards to analytics service."""
    return await forward_request(request, "analytics", "/reports")


@app.get("/reports/{report_id}")
async def get_report(report_id: str, request: Request):
    """Get report endpoint - forwards to analytics service."""
    return await forward_request(request, "analytics", f"/reports/{report_id}")


@app.post("/reports")
async def create_report(request: Request):
    """Create report endpoint - forwards to analytics service."""
    return await forward_request(request, "analytics", "/reports")


@app.get("/metrics")
async def get_metrics(request: Request):
    """Get metrics endpoint - forwards to analytics service."""
    return await forward_request(request, "analytics", "/metrics")


# Order service endpoints
@app.post("/orders")
async def create_order(request: Request):
    """Create order endpoint - forwards to order service."""
    return await forward_request(request, "order", "/orders")


@app.get("/orders/{order_id}")
async def get_order(order_id: str, request: Request):
    """Get order endpoint - forwards to order service."""
    return await forward_request(request, "order", f"/orders/{order_id}")


@app.get("/orders")
async def list_orders(request: Request):
    """List orders endpoint - forwards to order service."""
    return await forward_request(request, "order", "/orders")


@app.put("/orders/{order_id}")
async def update_order(order_id: str, request: Request):
    """Update order endpoint - forwards to order service."""
    return await forward_request(request, "order", f"/orders/{order_id}")


@app.delete("/orders/{order_id}")
async def delete_order(order_id: str, request: Request):
    """Delete order endpoint - forwards to order service."""
    return await forward_request(request, "order", f"/orders/{order_id}")


@app.get("/orders/{order_id}/details")
async def get_order_details(order_id: str, request: Request):
    """Get order with processes and tasks - forwards to order service."""
    return await forward_request(request, "order", f"/orders/{order_id}/details")


@app.post("/orders/{order_id}/refresh-progress")
async def refresh_order_progress(order_id: str, request: Request):
    """Refresh order progress - forwards to order service."""
    return await forward_request(request, "order", f"/orders/{order_id}/refresh-progress")


# Vendor service endpoints
@app.post("/vendors")
async def create_vendor(request: Request):
    """Create vendor endpoint - forwards to vendor service."""
    return await forward_request(request, "vendor", "/vendors")


@app.get("/vendors/{vendor_id}")
async def get_vendor(vendor_id: str, request: Request):
    """Get vendor endpoint - forwards to vendor service."""
    return await forward_request(request, "vendor", f"/vendors/{vendor_id}")


@app.get("/vendors")
async def list_vendors(request: Request):
    """List vendors endpoint - forwards to vendor service."""
    return await forward_request(request, "vendor", "/vendors")


@app.put("/vendors/{vendor_id}")
async def update_vendor(vendor_id: str, request: Request):
    """Update vendor endpoint - forwards to vendor service."""
    return await forward_request(request, "vendor", f"/vendors/{vendor_id}")


@app.delete("/vendors/{vendor_id}")
async def delete_vendor(vendor_id: str, request: Request):
    """Delete vendor endpoint - forwards to vendor service."""
    return await forward_request(request, "vendor", f"/vendors/{vendor_id}")


# Technician endpoints
@app.post("/technicians")
async def create_technician(request: Request):
    """Create technician endpoint - forwards to vendor service."""
    return await forward_request(request, "vendor", "/technicians")


@app.get("/technicians/{technician_id}")
async def get_technician(technician_id: str, request: Request):
    """Get technician endpoint - forwards to vendor service."""
    return await forward_request(request, "vendor", f"/technicians/{technician_id}")


@app.get("/vendors/{vendor_id}/technicians")
async def get_technicians_by_vendor(vendor_id: str, request: Request):
    """Get technicians by vendor - forwards to vendor service."""
    return await forward_request(request, "vendor", f"/vendors/{vendor_id}/technicians")


@app.get("/technicians/available")
async def get_available_technicians(request: Request):
    """Get available technicians - forwards to vendor service."""
    return await forward_request(request, "vendor", "/technicians/available")


@app.put("/technicians/{technician_id}")
async def update_technician(technician_id: str, request: Request):
    """Update technician endpoint - forwards to vendor service."""
    return await forward_request(request, "vendor", f"/technicians/{technician_id}")


@app.delete("/technicians/{technician_id}")
async def delete_technician(technician_id: str, request: Request):
    """Delete technician endpoint - forwards to vendor service."""
    return await forward_request(request, "vendor", f"/technicians/{technician_id}")


# Lead endpoints
@app.post("/leads")
async def create_lead(request: Request):
    """Create lead endpoint - forwards to vendor service."""
    return await forward_request(request, "vendor", "/leads")


@app.get("/leads/{lead_id}")
async def get_lead(lead_id: str, request: Request):
    """Get lead endpoint - forwards to vendor service."""
    return await forward_request(request, "vendor", f"/leads/{lead_id}")


@app.get("/vendors/{vendor_id}/leads")
async def get_leads_by_vendor(vendor_id: str, request: Request):
    """Get leads by vendor - forwards to vendor service."""
    return await forward_request(request, "vendor", f"/vendors/{vendor_id}/leads")


@app.get("/technicians/{technician_id}/lead")
async def get_lead_for_technician(technician_id: str, request: Request):
    """Get lead for technician - forwards to vendor service."""
    return await forward_request(request, "vendor", f"/technicians/{technician_id}/lead")


@app.put("/leads/{lead_id}")
async def update_lead(lead_id: str, request: Request):
    """Update lead endpoint - forwards to vendor service."""
    return await forward_request(request, "vendor", f"/leads/{lead_id}")


@app.delete("/leads/{lead_id}")
async def delete_lead(lead_id: str, request: Request):
    """Delete lead endpoint - forwards to vendor service."""
    return await forward_request(request, "vendor", f"/leads/{lead_id}")


# Task assignment endpoints
@app.post("/tasks/{task_id}/assign")
async def assign_task(task_id: str, request: Request):
    """Assign task endpoint - forwards to vendor service."""
    return await forward_request(request, "vendor", f"/tasks/{task_id}/assign")


@app.delete("/tasks/{task_id}/unassign")
async def unassign_task(task_id: str, request: Request):
    """Unassign task endpoint - forwards to vendor service."""
    return await forward_request(request, "vendor", f"/tasks/{task_id}/unassign")


# Dashboard service endpoints
@app.get("/dashboard/metrics")
async def get_dashboard_metrics(request: Request):
    """Get dashboard metrics endpoint - forwards to dashboard service."""
    return await forward_request(request, "dashboard", "/dashboard/metrics")


@app.get("/dashboard/metrics-test")
async def get_dashboard_metrics_test(request: Request):
    """Get dashboard metrics test endpoint - forwards to dashboard service."""
    return await forward_request(request, "dashboard", "/dashboard/metrics-test")


@app.get("/dashboard/recent-jobs")
async def get_recent_jobs(request: Request):
    """Get recent jobs endpoint - forwards to dashboard service."""
    return await forward_request(request, "dashboard", "/dashboard/recent-jobs")


async def forward_request(request: Request, service: str, path: str):
    """Forward request to appropriate service."""
    try:
        # Get service URL
        service_url = SERVICE_URLS.get(service)
        if not service_url:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Service '{service}' is not configured (set {service.upper()}_SERVICE_URL)"
            )
        
        # Prepare request
        url = f"{service_url}{path}"
        method = request.method
        headers = dict(request.headers)
        
        # Remove host header to avoid conflicts
        headers.pop("host", None)
        
        # Get request body
        body = await request.body()
        
        # Forward request
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                content=body,
                timeout=30.0
            )
            
            # Return response
            return JSONResponse(
                content=response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            
    except httpx.RequestError as e:
        logger.error(f"Request error forwarding to {service}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service '{service}' is not available"
        )
    except HTTPException:
        # Propagate explicit HTTP errors (e.g., service not configured)
        raise
    except Exception as e:
        logger.error(f"Error forwarding request to {service}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


if __name__ == "__main__":
    import uvicorn
    reload_flag = os.getenv("UVICORN_RELOAD", "false").lower() == "true"
    uvicorn.run(
        "api_gateway.main:app",
        host="0.0.0.0",
        port=8000,
        reload=reload_flag,
    ) 