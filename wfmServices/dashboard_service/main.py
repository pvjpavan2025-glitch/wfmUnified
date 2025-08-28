"""
Dashboard Service main application.
"""
import os
from contextlib import asynccontextmanager
from fastapi import Body, FastAPI, HTTPException, status, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import structlog
from datetime import datetime, timedelta
from typing import Optional

from shared.config import settings
from shared.database import db_manager
from shared.logging import setup_logging
from shared.auth import get_current_user
from .service import DashboardService

# Setup logging
setup_logging()
logger = structlog.get_logger(__name__)

# Setup logging
logger = setup_logging("dashboard-service")

# Security
security = HTTPBearer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Dashboard Service")
    await db_manager.connect_mongodb()
    # Temporarily disable Redis for testing
    # await db_manager.connect_redis()
    logger.info("Dashboard Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Dashboard Service")
    await db_manager.close()
    logger.info("Dashboard Service shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="WFM Dashboard Service",
    description="Dashboard service for Workforce Management",
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


# Dependency to get service instance
async def get_dashboard_service() -> DashboardService:
    """Get dashboard service instance."""
    database = await db_manager.get_database()
    return DashboardService(database)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "dashboard-service"}


# Dashboard metrics endpoint
@app.get("/dashboard/metrics")
async def get_dashboard_metrics(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """Get dashboard metrics."""
    try:
        # First verify the token by calling the API Gateway directly
        import httpx
        token = credentials.credentials
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            verify_response = await client.post(
                "http://api-gateway:8000/auth/verify",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if verify_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token"
                )
            
            verify_data = verify_response.json()
            user_data = verify_data.get("user", {})
            tenant_id = user_data.get("tenant_id")
            
            if not tenant_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: no tenant ID"
                )
            
            metrics = await dashboard_service.get_dashboard_metrics(tenant_id)
            return metrics
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dashboard metrics: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard metrics: {str(e)}"
        )


# Temporary test endpoint without authentication
@app.get("/dashboard/metrics-test")
async def get_dashboard_metrics_test(
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """Get dashboard metrics without authentication for testing."""
    try:
        # Use the test tenant ID directly
        tenant_id = "689b4041eba2c2b9886c1b96"
        metrics = await dashboard_service.get_dashboard_metrics(tenant_id)
        return metrics
    except Exception as e:
        logger.error(f"Failed to get dashboard metrics (test): {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard metrics: {str(e)}"
        )


# Recent jobs endpoint
@app.get("/dashboard/recent-jobs")
async def get_recent_jobs(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """Get recent jobs for dashboard."""
    try:
        current_user = await get_current_user(credentials)
        tenant_id = current_user.tenant_id
        recent_jobs = await dashboard_service.get_recent_jobs(tenant_id)
        return recent_jobs
    except Exception as e:
        logger.error(f"Failed to get recent jobs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get recent jobs"
        )
    

@app.get("/dashboard/technicians")
async def get_technicians(
    status: str = None,
    sort_order: str = "asc",
    limit: int = 10,
    page: int = 1,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """Get technicians list for the dashboard."""
    try:
        current_user = await get_current_user(credentials)
        tenant_id = current_user.tenant_id
        technicians = await dashboard_service.get_technicians(
            tenant_id=tenant_id,
            status=status,
            sort_order=sort_order,
            limit=limit,
            page=page
        )
        return {"technicians": technicians}
    except Exception as e:
        logger.error(f"Failed to get technicians: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get technicians"
        )


@app.get("/orders", response_model=list[dict])
async def get_orders_endpoint(
    limit: int = Query(10, ge=1, le=50, description="Number of orders to return"),
    status: Optional[str] = Query(None, description="Optional filter by order status"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """
    Get list of orders with tasks and progress.
    - Includes nested tasks (jobs) with geolocation, description, and status.
    - Supports filtering by order status.
    - Returns progress percentage based on completed tasks.
    """
    try:
        current_user = await get_current_user(credentials)
        tenant_id = current_user.tenant_id
        return await dashboard_service.get_orders(
            tenant_id=tenant_id,
            limit=limit,
            status_filter=status
        )
    except Exception as e:
        logger.error(f"Failed to get orders: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get orders"
        )
    

@app.get("/dashboard/job_details/{tenant_id}/")
async def get_job_details(
    tenant_id: str,
    job_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """
    Get details of a specific job by ID.
    - Requires tenant ID and job ID.
    - Returns job details including tasks, status, and geolocation.
    """
    try:
        current_user = await get_current_user(credentials)
        if current_user.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this tenant"
            )
        
        job_details = await dashboard_service.get_job_details(tenant_id, job_id)
        return job_details
    except Exception as e:
        logger.error(f"Failed to get job details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get job details"
        )
    

# TASK endpoints

@app.get("/tasks/{task_id}")
async def get_task(
    task_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """Get detailed information for a single task."""
    current_user = await get_current_user(credentials)
    return await dashboard_service.get_task(current_user.tenant_id, task_id)


@app.put("/tasks/{task_id}")
async def update_task(
    task_id: str,
    updates: dict = Body(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """Update details of a task (progress, status, description, hours)."""
    current_user = await get_current_user(credentials)
    return await dashboard_service.update_task(current_user.tenant_id, task_id, updates)


@app.post("/tasks/{task_id}/assign")
async def assign_task(
    task_id: str,
    body: dict = Body(..., example={"analystId": "analyst-123"}),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """Assign an analyst to a task."""
    current_user = await get_current_user(credentials)
    return await dashboard_service.assign_task(current_user.tenant_id, task_id, body["analystId"])


@app.post("/tasks/{task_id}/complete")
async def complete_task(
    task_id: str,
    body: dict = Body({}, example={"actual_hours": "4.0h"}),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """Mark a task as completed (progress = 100%)."""
    current_user = await get_current_user(credentials)
    return await dashboard_service.complete_task(current_user.tenant_id, task_id, body.get("actual_hours"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "dashboard_service.main:app",
        host="0.0.0.0",
        port=8007,
        reload=True
    )
