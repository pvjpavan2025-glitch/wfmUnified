"""
Repository layer for Intelligent Scheduler Service.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
import motor.motor_asyncio
import structlog
from bson import ObjectId
from .models import Job, Analyst, Schedule

logger = structlog.get_logger(__name__)


class JobRepository:
    """Repository for job operations."""
    
    def __init__(self, database: motor.motor_asyncio.AsyncIOMotorDatabase):
        self.database = database
        self.collection = database.jobs
    
    def _convert_id(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB ObjectId to string."""
        if "_id" in data:
            data["id"] = str(data["_id"])
            del data["_id"]
        return data
    
    async def create_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new job."""
        try:
            job_data["created_at"] = datetime.utcnow()
            job_data["updated_at"] = datetime.utcnow()
            
            result = await self.collection.insert_one(job_data)
            job_data["_id"] = result.inserted_id
            
            return self._convert_id(job_data)
        except Exception as e:
            logger.error(f"Failed to create job: {str(e)}")
            raise
    
    async def get_job_by_id(self, job_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get job by ID and tenant."""
        try:
            job = await self.collection.find_one({
                "_id": ObjectId(job_id),
                "tenant_id": tenant_id
            })
            
            if job:
                return self._convert_id(job)
            return None
        except Exception as e:
            logger.error(f"Failed to get job {job_id}: {str(e)}")
            return None
    
    async def update_job(self, job_id: str, tenant_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update job."""
        try:
            update_data["updated_at"] = datetime.utcnow()
            
            result = await self.collection.update_one(
                {"_id": ObjectId(job_id), "tenant_id": tenant_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                return await self.get_job_by_id(job_id, tenant_id)
            return None
        except Exception as e:
            logger.error(f"Failed to update job {job_id}: {str(e)}")
            return None
    
    async def delete_job(self, job_id: str, tenant_id: str) -> bool:
        """Delete job."""
        try:
            result = await self.collection.delete_one({
                "_id": ObjectId(job_id),
                "tenant_id": tenant_id
            })
            
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete job {job_id}: {str(e)}")
            return False
    
    async def list_jobs(self, tenant_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """List jobs for tenant."""
        try:
            cursor = self.collection.find({"tenant_id": tenant_id}).skip(skip).limit(limit)
            jobs = await cursor.to_list(length=limit)
            
            return [self._convert_id(job) for job in jobs]
        except Exception as e:
            logger.error(f"Failed to list jobs for tenant {tenant_id}: {str(e)}")
            return []
    
    async def create_schedule(self, schedule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new schedule."""
        try:
            schedule_data["created_at"] = datetime.utcnow()
            schedule_data["updated_at"] = datetime.utcnow()
            
            result = await self.database.schedules.insert_one(schedule_data)
            schedule_data["_id"] = result.inserted_id
            
            return self._convert_id(schedule_data)
        except Exception as e:
            logger.error(f"Failed to create schedule: {str(e)}")
            raise


class AnalystRepository:
    """Repository for analyst operations."""
    
    def __init__(self, database: motor.motor_asyncio.AsyncIOMotorDatabase):
        self.database = database
        self.collection = database.analysts
    
    def _convert_id(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB ObjectId to string."""
        if "_id" in data:
            data["id"] = str(data["_id"])
            del data["_id"]
        return data
    
    async def create_analyst(self, analyst_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new analyst."""
        try:
            analyst_data["created_at"] = datetime.utcnow()
            analyst_data["updated_at"] = datetime.utcnow()
            
            result = await self.collection.insert_one(analyst_data)
            analyst_data["_id"] = result.inserted_id
            
            return self._convert_id(analyst_data)
        except Exception as e:
            logger.error(f"Failed to create analyst: {str(e)}")
            raise
    
    async def get_analyst_by_id(self, analyst_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get analyst by ID and tenant."""
        try:
            analyst = await self.collection.find_one({
                "_id": ObjectId(analyst_id),
                "tenant_id": tenant_id
            })
            
            if analyst:
                return self._convert_id(analyst)
            return None
        except Exception as e:
            logger.error(f"Failed to get analyst {analyst_id}: {str(e)}")
            return None
    
    async def get_analyst_by_email(self, email: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get analyst by email and tenant."""
        try:
            analyst = await self.collection.find_one({
                "email": email,
                "tenant_id": tenant_id
            })
            
            if analyst:
                return self._convert_id(analyst)
            return None
        except Exception as e:
            logger.error(f"Failed to get analyst by email {email}: {str(e)}")
            return None
    
    async def update_analyst(self, analyst_id: str, tenant_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update analyst."""
        try:
            update_data["updated_at"] = datetime.utcnow()
            
            result = await self.collection.update_one(
                {"_id": ObjectId(analyst_id), "tenant_id": tenant_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                return await self.get_analyst_by_id(analyst_id, tenant_id)
            return None
        except Exception as e:
            logger.error(f"Failed to update analyst {analyst_id}: {str(e)}")
            return None
    
    async def delete_analyst(self, analyst_id: str, tenant_id: str) -> bool:
        """Delete analyst."""
        try:
            result = await self.collection.delete_one({
                "_id": ObjectId(analyst_id),
                "tenant_id": tenant_id
            })
            
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete analyst {analyst_id}: {str(e)}")
            return False
    
    async def list_analysts(self, tenant_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """List analysts for tenant."""
        try:
            cursor = self.collection.find({"tenant_id": tenant_id}).skip(skip).limit(limit)
            analysts = await cursor.to_list(length=limit)
            
            return [self._convert_id(analyst) for analyst in analysts]
        except Exception as e:
            logger.error(f"Failed to list analysts for tenant {tenant_id}: {str(e)}")
            return []
    
    async def get_available_analysts(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get available analysts for scheduling."""
        try:
            cursor = self.collection.find({
                "tenant_id": tenant_id,
                "status": "active"
            })
            
            analysts = await cursor.to_list(length=1000)
            return [self._convert_id(analyst) for analyst in analysts]
        except Exception as e:
            logger.error(f"Failed to get available analysts for tenant {tenant_id}: {str(e)}")
            return []
    
    async def update_analyst_job_count(self, analyst_id: str, tenant_id: str, job_count: int) -> bool:
        """Update analyst current job count."""
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(analyst_id), "tenant_id": tenant_id},
                {"$set": {"current_job_count": job_count, "updated_at": datetime.utcnow()}}
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update analyst job count {analyst_id}: {str(e)}")
            return False 