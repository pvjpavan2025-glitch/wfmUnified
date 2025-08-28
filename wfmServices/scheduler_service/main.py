"""
Intelligent Scheduler Service main application.
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
from .service import SchedulerService
from .repository import JobRepository, AnalystRepository
from .models import JobCreate, JobUpdate, JobResponse, AnalystCreate, AnalystUpdate, AnalystResponse
from typing import Dict, Any

# Setup logging
logger = setup_logging("scheduler-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Intelligent Scheduler Service")
    await db_manager.connect_mongodb()
    await db_manager.connect_redis()
    logger.info("Intelligent Scheduler Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Intelligent Scheduler Service")
    await db_manager.close()
    logger.info("Intelligent Scheduler Service shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="WFM Intelligent Scheduler Service",
    description="Job scheduling and resource allocation service for Workforce Management",
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
async def get_scheduler_service() -> SchedulerService:
    """Get scheduler service instance."""
    database = await db_manager.get_database()
    redis_client = await db_manager.get_redis()
    job_repo = JobRepository(database)
    analyst_repo = AnalystRepository(database)
    return SchedulerService(job_repo, analyst_repo, redis_client)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "scheduler-service"}


# Job endpoints
@app.post("/jobs", response_model=JobResponse)
async def create_job(
    job_data: JobCreate,
    scheduler_service: SchedulerService = Depends(get_scheduler_service),
    current_user: TokenData = Depends(get_current_user)
):
    """Create a new job."""
    try:
        job = await scheduler_service.create_job(job_data, current_user.user_id)
        return JobResponse(**job)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Create job failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    scheduler_service: SchedulerService = Depends(get_scheduler_service),
    current_user: TokenData = Depends(get_current_user)
):
    """Get job by ID."""
    job = await scheduler_service.get_job(job_id, current_user.tenant_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    return JobResponse(**job)


@app.put("/jobs/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: str,
    job_data: JobUpdate,
    scheduler_service: SchedulerService = Depends(get_scheduler_service),
    current_user: TokenData = Depends(get_current_user)
):
    """Update job."""
    job = await scheduler_service.update_job(
        job_id,
        current_user.tenant_id,
        job_data,
        current_user.user_id,
    )
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    return JobResponse(**job)


@app.delete("/jobs/{job_id}")
async def delete_job(
    job_id: str,
    scheduler_service: SchedulerService = Depends(get_scheduler_service),
    current_user: TokenData = Depends(get_current_user)
):
    """Delete job."""
    success = await scheduler_service.delete_job(job_id, current_user.tenant_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    return {"message": "Job deleted successfully"}


@app.get("/jobs", response_model=list[JobResponse])
async def list_jobs(
    skip: int = 0,
    limit: int = 100,
    scheduler_service: SchedulerService = Depends(get_scheduler_service),
    current_user: TokenData = Depends(get_current_user)
):
    """List jobs."""
    jobs = await scheduler_service.list_jobs(current_user.tenant_id, skip, limit)
    return [JobResponse(**job) for job in jobs]


@app.post("/jobs/{job_id}/schedule")
async def schedule_job(
    job_id: str,
    scheduler_service: SchedulerService = Depends(get_scheduler_service),
    current_user: TokenData = Depends(get_current_user)
):
    """Schedule a job."""
    try:
        result = await scheduler_service.schedule_job(job_id, current_user.tenant_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Job scheduling failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Job scheduling failed"
        )


# Analyst endpoints
@app.post("/analysts", response_model=AnalystResponse)
async def create_analyst(
    analyst_data: AnalystCreate,
    scheduler_service: SchedulerService = Depends(get_scheduler_service),
    current_user: TokenData = Depends(get_current_user)
):
    """Create a new analyst."""
    try:
        analyst = await scheduler_service.create_analyst(analyst_data, current_user.user_id)
        return AnalystResponse(**analyst)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Create analyst failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.get("/analysts/{analyst_id}", response_model=AnalystResponse)
async def get_analyst(
    analyst_id: str,
    scheduler_service: SchedulerService = Depends(get_scheduler_service),
    current_user: TokenData = Depends(get_current_user)
):
    """Get analyst by ID."""
    analyst = await scheduler_service.get_analyst(analyst_id, current_user.tenant_id)
    if not analyst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analyst not found"
        )
    return AnalystResponse(**analyst)


@app.put("/analysts/{analyst_id}", response_model=AnalystResponse)
async def update_analyst(
    analyst_id: str,
    analyst_data: AnalystUpdate,
    scheduler_service: SchedulerService = Depends(get_scheduler_service),
    current_user: TokenData = Depends(get_current_user)
):
    """Update analyst."""
    analyst = await scheduler_service.update_analyst(
    analyst_id, current_user.tenant_id, analyst_data, current_user.user_id
    )
    if not analyst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analyst not found"
        )
    return AnalystResponse(**analyst)


@app.delete("/analysts/{analyst_id}")
async def delete_analyst(
    analyst_id: str,
    scheduler_service: SchedulerService = Depends(get_scheduler_service),
    current_user: TokenData = Depends(get_current_user)
):
    """Delete analyst."""
    success = await scheduler_service.delete_analyst(analyst_id, current_user.tenant_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analyst not found"
        )
    return {"message": "Analyst deleted successfully"}


@app.get("/analysts", response_model=list[AnalystResponse])
async def list_analysts(
    skip: int = 0,
    limit: int = 100,
    scheduler_service: SchedulerService = Depends(get_scheduler_service),
    current_user: TokenData = Depends(get_current_user)
):
    """List analysts."""
    analysts = await scheduler_service.list_analysts(current_user.tenant_id, skip, limit)
    return [AnalystResponse(**analyst) for analyst in analysts]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "scheduler_service.main:app",
        host="0.0.0.0",
        port=8004,
        reload=True
    ) 

# Reporting endpoints
@app.get("/reports/orders/{order_id}/jobs-summary")
async def get_order_jobs_summary(
    order_id: str,
    scheduler_service: SchedulerService = Depends(get_scheduler_service),
    current_user: TokenData = Depends(get_current_user)
) -> Dict[str, Any]:
    """Return all jobs associated with an order and counts by status and assignment."""
    jobs = await scheduler_service.list_jobs(current_user.tenant_id, 0, 1000)
    # Filter by order_id
    related = [j for j in jobs if j.get("order_id") == order_id]
    status_counts: Dict[str, int] = {}
    assignment = {
        "assigned": sum(1 for j in related if j.get("assigned_analyst")),
        "unassigned": sum(1 for j in related if not j.get("assigned_analyst")),
    }
    for j in related:
        st = j.get("status", "unknown")
        status_counts[st] = status_counts.get(st, 0) + 1
    return {
        "order_id": order_id,
        "total_jobs": len(related),
        "status_counts": status_counts,
        "assignment": assignment,
        "jobs": related,
    }