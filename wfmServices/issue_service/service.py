"""
Business logic layer for Issue Handler Service.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import structlog
import redis.asyncio as redis
from .repository import IssueRepository, IssueCommentRepository, IssueAttachmentRepository, IssueEscalationRepository
from .models import IssueCreate, IssueUpdate, IssueCommentCreate, IssueCommentUpdate, IssueAttachmentCreate, IssueEscalationCreate

logger = structlog.get_logger(__name__)


class IssueService:
    """Issue handler service business logic."""
    
    def __init__(self, issue_repo: IssueRepository, comment_repo: IssueCommentRepository, 
                 attachment_repo: IssueAttachmentRepository, escalation_repo: IssueEscalationRepository,
                 redis_client: redis.Redis):
        self.issue_repo = issue_repo
        self.comment_repo = comment_repo
        self.attachment_repo = attachment_repo
        self.escalation_repo = escalation_repo
        self.redis_client = redis_client
        self.cache_ttl = 300  # 5 minutes
    
    async def create_issue(self, issue_data: IssueCreate, created_by: str) -> Dict[str, Any]:
        """Create a new issue."""
        try:
            # Prepare issue data
            issue_dict = issue_data.dict()
            issue_dict["created_by"] = created_by
            issue_dict["updated_by"] = created_by
            
            # Create issue
            issue = await self.issue_repo.create_issue(issue_dict)
            
            # Check SLA and set breach flag if needed
            await self._check_sla_breach(issue)
            
            # Invalidate cache
            await self._invalidate_cache(issue_data.tenant_id)
            
            logger.info(f"Issue '{issue_data.title}' created successfully for tenant {issue_data.tenant_id}")
            return issue
            
        except Exception as e:
            logger.error(f"Failed to create issue {issue_data.title}: {str(e)}")
            raise
    
    async def get_issue(self, issue_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get issue by ID."""
        try:
            issue = await self.issue_repo.get_issue_by_id(issue_id, tenant_id)
            return issue
            
        except Exception as e:
            logger.error(f"Failed to get issue {issue_id}: {str(e)}")
            return None
    
    async def update_issue(self, issue_id: str, tenant_id: str, issue_data: IssueUpdate, updated_by: str) -> Optional[Dict[str, Any]]:
        """Update issue."""
        try:
            # Check if issue exists
            existing_issue = await self.issue_repo.get_issue_by_id(issue_id, tenant_id)
            if not existing_issue:
                return None
            
            # Prepare update data
            update_data = issue_data.dict(exclude_unset=True)
            update_data["updated_by"] = updated_by
            
            # Update issue
            issue = await self.issue_repo.update_issue(issue_id, tenant_id, update_data)
            
            if issue:
                # Check SLA breach after update
                await self._check_sla_breach(issue)
                
                # Invalidate cache
                await self._invalidate_cache(tenant_id)
                
                logger.info(f"Issue '{issue['title']}' updated successfully")
            
            return issue
            
        except Exception as e:
            logger.error(f"Failed to update issue {issue_id}: {str(e)}")
            raise
    
    async def delete_issue(self, issue_id: str, tenant_id: str) -> bool:
        """Delete issue."""
        try:
            success = await self.issue_repo.delete_issue(issue_id, tenant_id)
            
            if success:
                # Invalidate cache
                await self._invalidate_cache(tenant_id)
                
                logger.info(f"Issue {issue_id} deleted successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete issue {issue_id}: {str(e)}")
            return False
    
    async def list_issues(self, tenant_id: str, skip: int = 0, limit: int = 100,
                         status: Optional[str] = None, priority: Optional[str] = None,
                         category: Optional[str] = None, assigned_to: Optional[str] = None) -> List[Dict[str, Any]]:
        """List issues for tenant with filters."""
        try:
            issues = await self.issue_repo.list_issues(
                tenant_id, skip, limit, status, priority, category, assigned_to
            )
            return issues
            
        except Exception as e:
            logger.error(f"Failed to list issues for tenant {tenant_id}: {str(e)}")
            return []
    
    async def get_issues_by_assigned_to(self, analyst_id: str, tenant_id: str) -> List[Dict[str, Any]]:
        """Get issues assigned to a specific analyst."""
        try:
            issues = await self.issue_repo.get_issues_by_assigned_to(analyst_id, tenant_id)
            return issues
            
        except Exception as e:
            logger.error(f"Failed to get issues for analyst {analyst_id}: {str(e)}")
            return []
    
    async def get_issues_by_job(self, job_id: str, tenant_id: str) -> List[Dict[str, Any]]:
        """Get issues related to a specific job."""
        try:
            issues = await self.issue_repo.get_issues_by_job(job_id, tenant_id)
            return issues
            
        except Exception as e:
            logger.error(f"Failed to get issues for job {job_id}: {str(e)}")
            return []
    
    async def get_sla_breached_issues(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get issues that have breached SLA."""
        try:
            issues = await self.issue_repo.get_sla_breached_issues(tenant_id)
            return issues
            
        except Exception as e:
            logger.error(f"Failed to get SLA breached issues for tenant {tenant_id}: {str(e)}")
            return []
    
    async def create_comment(self, comment_data: IssueCommentCreate, created_by: str) -> Dict[str, Any]:
        """Create a new issue comment."""
        try:
            # Check if issue exists
            issue = await self.issue_repo.get_issue_by_id(comment_data.issue_id, comment_data.tenant_id)
            if not issue:
                raise ValueError(f"Issue {comment_data.issue_id} not found")
            
            # Prepare comment data
            comment_dict = comment_data.dict()
            comment_dict["author_id"] = created_by
            comment_dict["author_name"] = "User"  # This would come from user service
            
            # Create comment
            comment = await self.comment_repo.create_comment(comment_dict)
            
            logger.info(f"Comment created for issue {comment_data.issue_id}")
            return comment
            
        except Exception as e:
            logger.error(f"Failed to create comment: {str(e)}")
            raise
    
    async def get_comment(self, comment_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get comment by ID."""
        try:
            comment = await self.comment_repo.get_comment_by_id(comment_id, tenant_id)
            return comment
            
        except Exception as e:
            logger.error(f"Failed to get comment {comment_id}: {str(e)}")
            return None
    
    async def update_comment(self, comment_id: str, tenant_id: str, comment_data: IssueCommentUpdate, updated_by: str) -> Optional[Dict[str, Any]]:
        """Update comment."""
        try:
            # Check if comment exists
            existing_comment = await self.comment_repo.get_comment_by_id(comment_id, tenant_id)
            if not existing_comment:
                return None
            
            # Prepare update data
            update_data = comment_data.dict()
            update_data["updated_by"] = updated_by
            
            # Update comment
            comment = await self.comment_repo.update_comment(comment_id, tenant_id, update_data)
            
            if comment:
                logger.info(f"Comment {comment_id} updated successfully")
            
            return comment
            
        except Exception as e:
            logger.error(f"Failed to update comment {comment_id}: {str(e)}")
            raise
    
    async def delete_comment(self, comment_id: str, tenant_id: str) -> bool:
        """Delete comment."""
        try:
            success = await self.comment_repo.delete_comment(comment_id, tenant_id)
            
            if success:
                logger.info(f"Comment {comment_id} deleted successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete comment {comment_id}: {str(e)}")
            return False
    
    async def list_comments_by_issue(self, issue_id: str, tenant_id: str) -> List[Dict[str, Any]]:
        """List comments for a specific issue."""
        try:
            comments = await self.comment_repo.list_comments_by_issue(issue_id, tenant_id)
            return comments
            
        except Exception as e:
            logger.error(f"Failed to list comments for issue {issue_id}: {str(e)}")
            return []
    
    async def create_attachment(self, attachment_data: IssueAttachmentCreate, created_by: str) -> Dict[str, Any]:
        """Create a new issue attachment."""
        try:
            # Check if issue exists
            issue = await self.issue_repo.get_issue_by_id(attachment_data.issue_id, attachment_data.tenant_id)
            if not issue:
                raise ValueError(f"Issue {attachment_data.issue_id} not found")
            
            # Prepare attachment data
            attachment_dict = attachment_data.dict()
            attachment_dict["created_by"] = created_by
            attachment_dict["updated_by"] = created_by
            
            # Create attachment
            attachment = await self.attachment_repo.create_attachment(attachment_dict)
            
            logger.info(f"Attachment created for issue {attachment_data.issue_id}")
            return attachment
            
        except Exception as e:
            logger.error(f"Failed to create attachment: {str(e)}")
            raise
    
    async def get_attachment(self, attachment_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get attachment by ID."""
        try:
            attachment = await self.attachment_repo.get_attachment_by_id(attachment_id, tenant_id)
            return attachment
            
        except Exception as e:
            logger.error(f"Failed to get attachment {attachment_id}: {str(e)}")
            return None
    
    async def delete_attachment(self, attachment_id: str, tenant_id: str) -> bool:
        """Delete attachment."""
        try:
            success = await self.attachment_repo.delete_attachment(attachment_id, tenant_id)
            
            if success:
                logger.info(f"Attachment {attachment_id} deleted successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete attachment {attachment_id}: {str(e)}")
            return False
    
    async def list_attachments_by_issue(self, issue_id: str, tenant_id: str) -> List[Dict[str, Any]]:
        """List attachments for a specific issue."""
        try:
            attachments = await self.attachment_repo.list_attachments_by_issue(issue_id, tenant_id)
            return attachments
            
        except Exception as e:
            logger.error(f"Failed to list attachments for issue {issue_id}: {str(e)}")
            return []
    
    async def create_escalation(self, escalation_data: IssueEscalationCreate, created_by: str) -> Dict[str, Any]:
        """Create a new issue escalation."""
        try:
            # Check if issue exists
            issue = await self.issue_repo.get_issue_by_id(escalation_data.issue_id, escalation_data.tenant_id)
            if not issue:
                raise ValueError(f"Issue {escalation_data.issue_id} not found")
            
            # Prepare escalation data
            escalation_dict = escalation_data.dict()
            escalation_dict["escalated_by"] = created_by
            
            # Create escalation
            escalation = await self.escalation_repo.create_escalation(escalation_dict)
            
            logger.info(f"Escalation created for issue {escalation_data.issue_id}")
            return escalation
            
        except Exception as e:
            logger.error(f"Failed to create escalation: {str(e)}")
            raise
    
    async def get_escalation(self, escalation_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get escalation by ID."""
        try:
            escalation = await self.escalation_repo.get_escalation_by_id(escalation_id, tenant_id)
            return escalation
            
        except Exception as e:
            logger.error(f"Failed to get escalation {escalation_id}: {str(e)}")
            return None
    
    async def list_escalations_by_issue(self, issue_id: str, tenant_id: str) -> List[Dict[str, Any]]:
        """List escalations for a specific issue."""
        try:
            escalations = await self.escalation_repo.list_escalations_by_issue(issue_id, tenant_id)
            return escalations
            
        except Exception as e:
            logger.error(f"Failed to list escalations for issue {issue_id}: {str(e)}")
            return []
    
    async def _check_sla_breach(self, issue: Dict[str, Any]) -> None:
        """Check if issue has breached SLA and update flag."""
        try:
            # Get SLA configuration for this issue category and priority
            sla_config = await self._get_sla_config(issue["category"], issue["priority"], issue["tenant_id"])
            
            if not sla_config:
                return
            
            sla_hours = sla_config["sla_hours"]
            created_at = issue["created_at"]
            
            # Calculate if SLA is breached
            current_time = datetime.utcnow()
            time_elapsed = current_time - created_at
            sla_deadline = created_at + timedelta(hours=sla_hours)
            
            sla_breach = current_time > sla_deadline and issue["status"] != "resolved"
            
            # Update issue if SLA breach status has changed
            if sla_breach != issue.get("sla_breach", False):
                await self.issue_repo.update_issue(
                    issue["id"], 
                    issue["tenant_id"], 
                    {"sla_breach": sla_breach}
                )
                
                if sla_breach:
                    logger.warning(f"Issue {issue['id']} has breached SLA")
            
        except Exception as e:
            logger.error(f"Error checking SLA breach for issue {issue.get('id')}: {str(e)}")
    
    async def _get_sla_config(self, category: str, priority: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get SLA configuration for category and priority."""
        try:
            # This would typically fetch from a configuration service
            # For now, return default SLA configuration
            default_sla_configs = {
                "critical": {"sla_hours": 2, "escalation_hours": 1},
                "high": {"sla_hours": 4, "escalation_hours": 2},
                "medium": {"sla_hours": 8, "escalation_hours": 4},
                "low": {"sla_hours": 24, "escalation_hours": 12}
            }
            
            return default_sla_configs.get(priority, {"sla_hours": 8, "escalation_hours": 4})
            
        except Exception as e:
            logger.error(f"Error getting SLA config: {str(e)}")
            return None
    
    async def _invalidate_cache(self, tenant_id: str) -> None:
        """Invalidate cache for tenant."""
        try:
            cache_key = f"issues:{tenant_id}"
            await self.redis_client.delete(cache_key)
            logger.debug(f"Cache invalidated for tenant {tenant_id}")
        except Exception as e:
            logger.warning(f"Failed to invalidate cache for tenant {tenant_id}: {str(e)}") 