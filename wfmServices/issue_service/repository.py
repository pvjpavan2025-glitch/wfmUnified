"""
Repository layer for Issue Handler Service.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
import motor.motor_asyncio
import structlog
from bson import ObjectId
from .models import Issue, IssueComment, IssueAttachment, IssueEscalation, IssueSLAConfig

logger = structlog.get_logger(__name__)


class IssueRepository:
    """Repository for issue operations."""
    
    def __init__(self, database: motor.motor_asyncio.AsyncIOMotorDatabase):
        self.database = database
        self.collection = database.issues
    
    def _convert_id(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB ObjectId to string."""
        if "_id" in data:
            data["id"] = str(data["_id"])
            del data["_id"]
        return data
    
    async def create_issue(self, issue_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new issue."""
        try:
            issue_data["created_at"] = datetime.utcnow()
            issue_data["updated_at"] = datetime.utcnow()
            
            result = await self.collection.insert_one(issue_data)
            issue_data["_id"] = result.inserted_id
            
            return self._convert_id(issue_data)
        except Exception as e:
            logger.error(f"Failed to create issue: {str(e)}")
            raise
    
    async def get_issue_by_id(self, issue_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get issue by ID and tenant."""
        try:
            issue = await self.collection.find_one({
                "_id": ObjectId(issue_id),
                "tenant_id": tenant_id
            })
            
            if issue:
                return self._convert_id(issue)
            return None
        except Exception as e:
            logger.error(f"Failed to get issue {issue_id}: {str(e)}")
            return None
    
    async def update_issue(self, issue_id: str, tenant_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update issue."""
        try:
            update_data["updated_at"] = datetime.utcnow()
            
            # If status is being updated to resolved, set resolution time
            if update_data.get("status") == "resolved":
                update_data["resolution_time"] = datetime.utcnow()
            
            result = await self.collection.update_one(
                {"_id": ObjectId(issue_id), "tenant_id": tenant_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                return await self.get_issue_by_id(issue_id, tenant_id)
            return None
        except Exception as e:
            logger.error(f"Failed to update issue {issue_id}: {str(e)}")
            return None
    
    async def delete_issue(self, issue_id: str, tenant_id: str) -> bool:
        """Delete issue."""
        try:
            result = await self.collection.delete_one({
                "_id": ObjectId(issue_id),
                "tenant_id": tenant_id
            })
            
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete issue {issue_id}: {str(e)}")
            return False
    
    async def list_issues(self, tenant_id: str, skip: int = 0, limit: int = 100, 
                         status: Optional[str] = None, priority: Optional[str] = None,
                         category: Optional[str] = None, assigned_to: Optional[str] = None) -> List[Dict[str, Any]]:
        """List issues for tenant with filters."""
        try:
            filter_query = {"tenant_id": tenant_id}
            
            if status:
                filter_query["status"] = status
            if priority:
                filter_query["priority"] = priority
            if category:
                filter_query["category"] = category
            if assigned_to:
                filter_query["assigned_to"] = assigned_to
            
            cursor = self.collection.find(filter_query).skip(skip).limit(limit)
            issues = await cursor.to_list(length=limit)
            
            return [self._convert_id(issue) for issue in issues]
        except Exception as e:
            logger.error(f"Failed to list issues for tenant {tenant_id}: {str(e)}")
            return []
    
    async def get_issues_by_assigned_to(self, analyst_id: str, tenant_id: str) -> List[Dict[str, Any]]:
        """Get issues assigned to a specific analyst."""
        try:
            cursor = self.collection.find({
                "assigned_to": analyst_id,
                "tenant_id": tenant_id
            })
            
            issues = await cursor.to_list(length=1000)
            return [self._convert_id(issue) for issue in issues]
        except Exception as e:
            logger.error(f"Failed to get issues for analyst {analyst_id}: {str(e)}")
            return []
    
    async def get_issues_by_job(self, job_id: str, tenant_id: str) -> List[Dict[str, Any]]:
        """Get issues related to a specific job."""
        try:
            cursor = self.collection.find({
                "related_job_id": job_id,
                "tenant_id": tenant_id
            })
            
            issues = await cursor.to_list(length=1000)
            return [self._convert_id(issue) for issue in issues]
        except Exception as e:
            logger.error(f"Failed to get issues for job {job_id}: {str(e)}")
            return []
    
    async def get_sla_breached_issues(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get issues that have breached SLA."""
        try:
            cursor = self.collection.find({
                "tenant_id": tenant_id,
                "sla_breach": True
            })
            
            issues = await cursor.to_list(length=1000)
            return [self._convert_id(issue) for issue in issues]
        except Exception as e:
            logger.error(f"Failed to get SLA breached issues for tenant {tenant_id}: {str(e)}")
            return []


class IssueCommentRepository:
    """Repository for issue comment operations."""
    
    def __init__(self, database: motor.motor_asyncio.AsyncIOMotorDatabase):
        self.database = database
        self.collection = database.issue_comments
    
    def _convert_id(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB ObjectId to string."""
        if "_id" in data:
            data["id"] = str(data["_id"])
            del data["_id"]
        return data
    
    async def create_comment(self, comment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new issue comment."""
        try:
            comment_data["created_at"] = datetime.utcnow()
            comment_data["updated_at"] = datetime.utcnow()
            
            result = await self.collection.insert_one(comment_data)
            comment_data["_id"] = result.inserted_id
            
            return self._convert_id(comment_data)
        except Exception as e:
            logger.error(f"Failed to create comment: {str(e)}")
            raise
    
    async def get_comment_by_id(self, comment_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get comment by ID and tenant."""
        try:
            comment = await self.collection.find_one({
                "_id": ObjectId(comment_id),
                "tenant_id": tenant_id
            })
            
            if comment:
                return self._convert_id(comment)
            return None
        except Exception as e:
            logger.error(f"Failed to get comment {comment_id}: {str(e)}")
            return None
    
    async def update_comment(self, comment_id: str, tenant_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update comment."""
        try:
            update_data["updated_at"] = datetime.utcnow()
            
            result = await self.collection.update_one(
                {"_id": ObjectId(comment_id), "tenant_id": tenant_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                return await self.get_comment_by_id(comment_id, tenant_id)
            return None
        except Exception as e:
            logger.error(f"Failed to update comment {comment_id}: {str(e)}")
            return None
    
    async def delete_comment(self, comment_id: str, tenant_id: str) -> bool:
        """Delete comment."""
        try:
            result = await self.collection.delete_one({
                "_id": ObjectId(comment_id),
                "tenant_id": tenant_id
            })
            
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete comment {comment_id}: {str(e)}")
            return False
    
    async def list_comments_by_issue(self, issue_id: str, tenant_id: str) -> List[Dict[str, Any]]:
        """List comments for a specific issue."""
        try:
            cursor = self.collection.find({
                "issue_id": issue_id,
                "tenant_id": tenant_id
            }).sort("created_at", 1)
            
            comments = await cursor.to_list(length=1000)
            return [self._convert_id(comment) for comment in comments]
        except Exception as e:
            logger.error(f"Failed to list comments for issue {issue_id}: {str(e)}")
            return []


class IssueAttachmentRepository:
    """Repository for issue attachment operations."""
    
    def __init__(self, database: motor.motor_asyncio.AsyncIOMotorDatabase):
        self.database = database
        self.collection = database.issue_attachments
    
    def _convert_id(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB ObjectId to string."""
        if "_id" in data:
            data["id"] = str(data["_id"])
            del data["_id"]
        return data
    
    async def create_attachment(self, attachment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new issue attachment."""
        try:
            attachment_data["created_at"] = datetime.utcnow()
            attachment_data["updated_at"] = datetime.utcnow()
            
            result = await self.collection.insert_one(attachment_data)
            attachment_data["_id"] = result.inserted_id
            
            return self._convert_id(attachment_data)
        except Exception as e:
            logger.error(f"Failed to create attachment: {str(e)}")
            raise
    
    async def get_attachment_by_id(self, attachment_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get attachment by ID and tenant."""
        try:
            attachment = await self.collection.find_one({
                "_id": ObjectId(attachment_id),
                "tenant_id": tenant_id
            })
            
            if attachment:
                return self._convert_id(attachment)
            return None
        except Exception as e:
            logger.error(f"Failed to get attachment {attachment_id}: {str(e)}")
            return None
    
    async def delete_attachment(self, attachment_id: str, tenant_id: str) -> bool:
        """Delete attachment."""
        try:
            result = await self.collection.delete_one({
                "_id": ObjectId(attachment_id),
                "tenant_id": tenant_id
            })
            
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete attachment {attachment_id}: {str(e)}")
            return False
    
    async def list_attachments_by_issue(self, issue_id: str, tenant_id: str) -> List[Dict[str, Any]]:
        """List attachments for a specific issue."""
        try:
            cursor = self.collection.find({
                "issue_id": issue_id,
                "tenant_id": tenant_id
            })
            
            attachments = await cursor.to_list(length=1000)
            return [self._convert_id(attachment) for attachment in attachments]
        except Exception as e:
            logger.error(f"Failed to list attachments for issue {issue_id}: {str(e)}")
            return []


class IssueEscalationRepository:
    """Repository for issue escalation operations."""
    
    def __init__(self, database: motor.motor_asyncio.AsyncIOMotorDatabase):
        self.database = database
        self.collection = database.issue_escalations
    
    def _convert_id(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB ObjectId to string."""
        if "_id" in data:
            data["id"] = str(data["_id"])
            del data["_id"]
        return data
    
    async def create_escalation(self, escalation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new issue escalation."""
        try:
            escalation_data["created_at"] = datetime.utcnow()
            escalation_data["updated_at"] = datetime.utcnow()
            
            result = await self.collection.insert_one(escalation_data)
            escalation_data["_id"] = result.inserted_id
            
            return self._convert_id(escalation_data)
        except Exception as e:
            logger.error(f"Failed to create escalation: {str(e)}")
            raise
    
    async def get_escalation_by_id(self, escalation_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get escalation by ID and tenant."""
        try:
            escalation = await self.collection.find_one({
                "_id": ObjectId(escalation_id),
                "tenant_id": tenant_id
            })
            
            if escalation:
                return self._convert_id(escalation)
            return None
        except Exception as e:
            logger.error(f"Failed to get escalation {escalation_id}: {str(e)}")
            return None
    
    async def list_escalations_by_issue(self, issue_id: str, tenant_id: str) -> List[Dict[str, Any]]:
        """List escalations for a specific issue."""
        try:
            cursor = self.collection.find({
                "issue_id": issue_id,
                "tenant_id": tenant_id
            }).sort("created_at", -1)
            
            escalations = await cursor.to_list(length=1000)
            return [self._convert_id(escalation) for escalation in escalations]
        except Exception as e:
            logger.error(f"Failed to list escalations for issue {issue_id}: {str(e)}")
            return []
    
    async def update_escalation_status(self, escalation_id: str, tenant_id: str, status: str) -> bool:
        """Update escalation status."""
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(escalation_id), "tenant_id": tenant_id},
                {"$set": {"status": status, "updated_at": datetime.utcnow()}}
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update escalation status {escalation_id}: {str(e)}")
            return False 