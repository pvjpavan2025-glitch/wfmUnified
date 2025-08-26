"""
Issue Handler Service main application.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
import structlog

from shared.config import settings
from shared.database import db_manager
from shared.logging import setup_logging
from shared.auth import get_current_user, TokenData
from .service import IssueService
from .repository import IssueRepository, IssueCommentRepository, IssueAttachmentRepository, IssueEscalationRepository
from .models import IssueCreate, IssueUpdate, IssueResponse, IssueCommentCreate, IssueCommentUpdate, IssueCommentResponse, IssueAttachmentCreate, IssueAttachmentResponse, IssueEscalationCreate, IssueEscalationResponse

logger = setup_logging("issue-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Issue Handler Service...")
    await db_manager.connect_mongodb()
    await db_manager.connect_redis()
    logger.info("Issue Handler Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Issue Handler Service...")
    await db_manager.close()
    logger.info("Issue Handler Service shutdown complete")


app = FastAPI(
    title="Issue Handler Service",
    description="Handles issue management, tracking, and resolution",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging is now handled by structured logging setup


async def get_issue_service() -> IssueService:
    """Dependency injection for IssueService."""
    database = await db_manager.get_database()
    redis_client = await db_manager.get_redis()
    
    issue_repo = IssueRepository(database)
    comment_repo = IssueCommentRepository(database)
    attachment_repo = IssueAttachmentRepository(database)
    escalation_repo = IssueEscalationRepository(database)
    
    return IssueService(issue_repo, comment_repo, attachment_repo, escalation_repo, redis_client)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "issue-service",
        "version": "1.0.0"
    }


# Issue endpoints
@app.post("/issues", response_model=IssueResponse)
async def create_issue(
    issue_data: IssueCreate,
    current_user: TokenData = Depends(get_current_user),
    issue_service: IssueService = Depends(get_issue_service)
):
    """Create a new issue."""
    try:
        issue = await issue_service.create_issue(issue_data, current_user.user_id)
        return IssueResponse(**issue)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create issue: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@app.get("/issues/{issue_id}", response_model=IssueResponse)
async def get_issue(
    issue_id: str,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: TokenData = Depends(get_current_user),
    issue_service: IssueService = Depends(get_issue_service)
):
    """Get issue by ID."""
    issue = await issue_service.get_issue(issue_id, tenant_id)
    if not issue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")
    return IssueResponse(**issue)


@app.put("/issues/{issue_id}", response_model=IssueResponse)
async def update_issue(
    issue_id: str,
    issue_data: IssueUpdate,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: TokenData = Depends(get_current_user),
    issue_service: IssueService = Depends(get_issue_service)
):
    """Update issue."""
    issue = await issue_service.update_issue(issue_id, tenant_id, issue_data, current_user.user_id)
    if not issue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")
    return IssueResponse(**issue)


@app.delete("/issues/{issue_id}")
async def delete_issue(
    issue_id: str,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: TokenData = Depends(get_current_user),
    issue_service: IssueService = Depends(get_issue_service)
):
    """Delete issue."""
    success = await issue_service.delete_issue(issue_id, tenant_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")
    return {"message": "Issue deleted successfully"}


@app.get("/issues")
async def list_issues(
    tenant_id: str = Query(..., description="Tenant ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: str = Query(None, description="Filter by status"),
    priority: str = Query(None, description="Filter by priority"),
    category: str = Query(None, description="Filter by category"),
    assigned_to: str = Query(None, description="Filter by assigned analyst"),
    current_user: TokenData = Depends(get_current_user),
    issue_service: IssueService = Depends(get_issue_service)
):
    """List issues with optional filters."""
    issues = await issue_service.list_issues(
        tenant_id, skip, limit, status, priority, category, assigned_to
    )
    return {"issues": issues, "total": len(issues)}


@app.get("/issues/assigned/{analyst_id}")
async def get_issues_by_assigned_to(
    analyst_id: str,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: TokenData = Depends(get_current_user),
    issue_service: IssueService = Depends(get_issue_service)
):
    """Get issues assigned to a specific analyst."""
    issues = await issue_service.get_issues_by_assigned_to(analyst_id, tenant_id)
    return {"issues": issues, "total": len(issues)}


@app.get("/issues/job/{job_id}")
async def get_issues_by_job(
    job_id: str,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: TokenData = Depends(get_current_user),
    issue_service: IssueService = Depends(get_issue_service)
):
    """Get issues related to a specific job."""
    issues = await issue_service.get_issues_by_job(job_id, tenant_id)
    return {"issues": issues, "total": len(issues)}


@app.get("/issues/sla-breached")
async def get_sla_breached_issues(
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: TokenData = Depends(get_current_user),
    issue_service: IssueService = Depends(get_issue_service)
):
    """Get issues that have breached SLA."""
    issues = await issue_service.get_sla_breached_issues(tenant_id)
    return {"issues": issues, "total": len(issues)}


# Comment endpoints
@app.post("/issues/{issue_id}/comments", response_model=IssueCommentResponse)
async def create_comment(
    issue_id: str,
    comment_data: IssueCommentCreate,
    current_user: TokenData = Depends(get_current_user),
    issue_service: IssueService = Depends(get_issue_service)
):
    """Create a new comment for an issue."""
    try:
        comment_data.issue_id = issue_id
        comment = await issue_service.create_comment(comment_data, current_user.user_id)
        return IssueCommentResponse(**comment)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create comment: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@app.get("/issues/{issue_id}/comments")
async def list_comments_by_issue(
    issue_id: str,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: TokenData = Depends(get_current_user),
    issue_service: IssueService = Depends(get_issue_service)
):
    """List comments for a specific issue."""
    comments = await issue_service.list_comments_by_issue(issue_id, tenant_id)
    return {"comments": comments, "total": len(comments)}


@app.get("/comments/{comment_id}", response_model=IssueCommentResponse)
async def get_comment(
    comment_id: str,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: TokenData = Depends(get_current_user),
    issue_service: IssueService = Depends(get_issue_service)
):
    """Get comment by ID."""
    comment = await issue_service.get_comment(comment_id, tenant_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    return IssueCommentResponse(**comment)


@app.put("/comments/{comment_id}", response_model=IssueCommentResponse)
async def update_comment(
    comment_id: str,
    comment_data: IssueCommentUpdate,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: TokenData = Depends(get_current_user),
    issue_service: IssueService = Depends(get_issue_service)
):
    """Update comment."""
    comment = await issue_service.update_comment(comment_id, tenant_id, comment_data, current_user.user_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    return IssueCommentResponse(**comment)


@app.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: str,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: TokenData = Depends(get_current_user),
    issue_service: IssueService = Depends(get_issue_service)
):
    """Delete comment."""
    success = await issue_service.delete_comment(comment_id, tenant_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    return {"message": "Comment deleted successfully"}


# Attachment endpoints
@app.post("/issues/{issue_id}/attachments", response_model=IssueAttachmentResponse)
async def create_attachment(
    issue_id: str,
    attachment_data: IssueAttachmentCreate,
    current_user: TokenData = Depends(get_current_user),
    issue_service: IssueService = Depends(get_issue_service)
):
    """Create a new attachment for an issue."""
    try:
        attachment_data.issue_id = issue_id
        attachment = await issue_service.create_attachment(attachment_data, current_user.user_id)
        return IssueAttachmentResponse(**attachment)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create attachment: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@app.get("/issues/{issue_id}/attachments")
async def list_attachments_by_issue(
    issue_id: str,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: TokenData = Depends(get_current_user),
    issue_service: IssueService = Depends(get_issue_service)
):
    """List attachments for a specific issue."""
    attachments = await issue_service.list_attachments_by_issue(issue_id, tenant_id)
    return {"attachments": attachments, "total": len(attachments)}


@app.get("/attachments/{attachment_id}", response_model=IssueAttachmentResponse)
async def get_attachment(
    attachment_id: str,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: TokenData = Depends(get_current_user),
    issue_service: IssueService = Depends(get_issue_service)
):
    """Get attachment by ID."""
    attachment = await issue_service.get_attachment(attachment_id, tenant_id)
    if not attachment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")
    return IssueAttachmentResponse(**attachment)


@app.delete("/attachments/{attachment_id}")
async def delete_attachment(
    attachment_id: str,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: TokenData = Depends(get_current_user),
    issue_service: IssueService = Depends(get_issue_service)
):
    """Delete attachment."""
    success = await issue_service.delete_attachment(attachment_id, tenant_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")
    return {"message": "Attachment deleted successfully"}


# Escalation endpoints
@app.post("/issues/{issue_id}/escalations", response_model=IssueEscalationResponse)
async def create_escalation(
    issue_id: str,
    escalation_data: IssueEscalationCreate,
    current_user: TokenData = Depends(get_current_user),
    issue_service: IssueService = Depends(get_issue_service)
):
    """Create a new escalation for an issue."""
    try:
        escalation_data.issue_id = issue_id
        escalation = await issue_service.create_escalation(escalation_data, current_user.user_id)
        return IssueEscalationResponse(**escalation)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create escalation: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@app.get("/issues/{issue_id}/escalations")
async def list_escalations_by_issue(
    issue_id: str,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: TokenData = Depends(get_current_user),
    issue_service: IssueService = Depends(get_issue_service)
):
    """List escalations for a specific issue."""
    escalations = await issue_service.list_escalations_by_issue(issue_id, tenant_id)
    return {"escalations": escalations, "total": len(escalations)}


@app.get("/escalations/{escalation_id}", response_model=IssueEscalationResponse)
async def get_escalation(
    escalation_id: str,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: TokenData = Depends(get_current_user),
    issue_service: IssueService = Depends(get_issue_service)
):
    """Get escalation by ID."""
    escalation = await issue_service.get_escalation(escalation_id, tenant_id)
    if not escalation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Escalation not found")
    return IssueEscalationResponse(**escalation)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "issue_service.main:app",
        host="0.0.0.0",
        port=int(os.getenv("SERVICE_PORT", 8005)),
        reload=True
    ) 