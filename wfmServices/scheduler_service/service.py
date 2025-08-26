"""
Business logic layer for Intelligent Scheduler Service.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import structlog
import redis.asyncio as redis
from .repository import JobRepository, AnalystRepository
from .models import JobCreate, JobUpdate, AnalystCreate, AnalystUpdate, SchedulingRequest

logger = structlog.get_logger(__name__)


class SchedulerService:
    """Intelligent scheduler service business logic."""
    
    def __init__(self, job_repo: JobRepository, analyst_repo: AnalystRepository, redis_client: redis.Redis):
        self.job_repo = job_repo
        self.analyst_repo = analyst_repo
        self.redis_client = redis_client
        self.cache_ttl = 300  # 5 minutes
    
    async def create_job(self, job_data: JobCreate, created_by: str) -> Dict[str, Any]:
        """Create a new job."""
        try:
            # Validate tasks exist
            # This would typically check against a task service
            if not job_data.tasks:
                raise ValueError("Job must have at least one task")
            
            # Prepare job data
            job_dict = job_data.dict()
            job_dict["created_by"] = created_by
            job_dict["updated_by"] = created_by
            
            # Create job
            job = await self.job_repo.create_job(job_dict)
            
            logger.info(f"Job '{job_data.name}' created successfully for tenant {job_data.tenant_id}")
            return job
            
        except Exception as e:
            logger.error(f"Failed to create job {job_data.name}: {str(e)}")
            raise
    
    async def get_job(self, job_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get job by ID."""
        try:
            job = await self.job_repo.get_job_by_id(job_id, tenant_id)
            return job
            
        except Exception as e:
            logger.error(f"Failed to get job {job_id}: {str(e)}")
            return None
    
    async def update_job(self, job_id: str, tenant_id: str, job_data: JobUpdate, updated_by: str) -> Optional[Dict[str, Any]]:
        """Update job."""
        try:
            # Check if job exists
            existing_job = await self.job_repo.get_job_by_id(job_id, tenant_id)
            if not existing_job:
                return None
            
            # Prepare update data
            update_data = job_data.dict(exclude_unset=True)
            update_data["updated_by"] = updated_by
            
            # Update job
            job = await self.job_repo.update_job(job_id, tenant_id, update_data)
            
            if job:
                logger.info(f"Job '{job['name']}' updated successfully")
            
            return job
            
        except Exception as e:
            logger.error(f"Failed to update job {job_id}: {str(e)}")
            raise
    
    async def delete_job(self, job_id: str, tenant_id: str) -> bool:
        """Delete job."""
        try:
            success = await self.job_repo.delete_job(job_id, tenant_id)
            
            if success:
                logger.info(f"Job {job_id} deleted successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete job {job_id}: {str(e)}")
            return False
    
    async def list_jobs(self, tenant_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """List jobs for tenant."""
        try:
            jobs = await self.job_repo.list_jobs(tenant_id, skip, limit)
            return jobs
            
        except Exception as e:
            logger.error(f"Failed to list jobs for tenant {tenant_id}: {str(e)}")
            return []
    
    async def schedule_job(self, job_id: str, tenant_id: str) -> Dict[str, Any]:
        """Schedule a job."""
        try:
            # Get job
            job = await self.job_repo.get_job_by_id(job_id, tenant_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")
            
            # Get available analysts
            analysts = await self.analyst_repo.get_available_analysts(tenant_id)
            if not analysts:
                raise ValueError("No available analysts found")
            
            # Find best analyst for the job
            best_analyst = await self._find_best_analyst(job, analysts)
            if not best_analyst:
                raise ValueError("No suitable analyst found for this job")
            
            # Calculate schedule
            schedule = await self._calculate_schedule(job, best_analyst)
            
            # Update job with schedule
            update_data = {
                "assigned_analyst": best_analyst["id"],
                "scheduled_start": schedule["start_time"],
                "scheduled_end": schedule["end_time"],
                "status": "scheduled"
            }
            
            updated_job = await self.job_repo.update_job(job_id, tenant_id, update_data)
            
            # Create schedule record
            schedule_data = {
                "analyst_id": best_analyst["id"],
                "job_id": job_id,
                "start_time": schedule["start_time"],
                "end_time": schedule["end_time"],
                "tenant_id": tenant_id
            }
            
            await self.job_repo.create_schedule(schedule_data)
            
            logger.info(f"Job {job_id} scheduled with analyst {best_analyst['name']}")
            
            return {
                "job_id": job_id,
                "analyst_id": best_analyst["id"],
                "analyst_name": best_analyst["name"],
                "start_time": schedule["start_time"],
                "end_time": schedule["end_time"],
                "confidence_score": schedule["confidence_score"]
            }
            
        except Exception as e:
            logger.error(f"Failed to schedule job {job_id}: {str(e)}")
            raise
    
    async def create_analyst(self, analyst_data: AnalystCreate, created_by: str) -> Dict[str, Any]:
        """Create a new analyst."""
        try:
            # Check if analyst email already exists for tenant
            existing_analyst = await self.analyst_repo.get_analyst_by_email(
                analyst_data.email, analyst_data.tenant_id
            )
            
            if existing_analyst:
                raise ValueError(f"Analyst with email '{analyst_data.email}' already exists for this tenant")
            
            # Prepare analyst data
            analyst_dict = analyst_data.dict()
            analyst_dict["created_by"] = created_by
            analyst_dict["updated_by"] = created_by
            
            # Create analyst
            analyst = await self.analyst_repo.create_analyst(analyst_dict)
            
            logger.info(f"Analyst '{analyst_data.name}' created successfully for tenant {analyst_data.tenant_id}")
            return analyst
            
        except Exception as e:
            logger.error(f"Failed to create analyst {analyst_data.name}: {str(e)}")
            raise
    
    async def get_analyst(self, analyst_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get analyst by ID."""
        try:
            analyst = await self.analyst_repo.get_analyst_by_id(analyst_id, tenant_id)
            return analyst
            
        except Exception as e:
            logger.error(f"Failed to get analyst {analyst_id}: {str(e)}")
            return None
    
    async def update_analyst(self, analyst_id: str, tenant_id: str, analyst_data: AnalystUpdate, updated_by: str) -> Optional[Dict[str, Any]]:
        """Update analyst."""
        try:
            # Check if analyst exists
            existing_analyst = await self.analyst_repo.get_analyst_by_id(analyst_id, tenant_id)
            if not existing_analyst:
                return None
            
            # Prepare update data
            update_data = analyst_data.dict(exclude_unset=True)
            update_data["updated_by"] = updated_by
            
            # Update analyst
            analyst = await self.analyst_repo.update_analyst(analyst_id, tenant_id, update_data)
            
            if analyst:
                logger.info(f"Analyst '{analyst['name']}' updated successfully")
            
            return analyst
            
        except Exception as e:
            logger.error(f"Failed to update analyst {analyst_id}: {str(e)}")
            raise
    
    async def delete_analyst(self, analyst_id: str, tenant_id: str) -> bool:
        """Delete analyst."""
        try:
            success = await self.analyst_repo.delete_analyst(analyst_id, tenant_id)
            
            if success:
                logger.info(f"Analyst {analyst_id} deleted successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete analyst {analyst_id}: {str(e)}")
            return False
    
    async def list_analysts(self, tenant_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """List analysts for tenant."""
        try:
            analysts = await self.analyst_repo.list_analysts(tenant_id, skip, limit)
            return analysts
            
        except Exception as e:
            logger.error(f"Failed to list analysts for tenant {tenant_id}: {str(e)}")
            return []
    
    async def _find_best_analyst(self, job: Dict[str, Any], analysts: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find the best analyst for a job."""
        try:
            best_analyst = None
            best_score = 0.0
            
            for analyst in analysts:
                if analyst.get("status", "inactive") != "active":
                    continue
                
                current_jobs = analyst.get("current_job_count", 0)
                max_jobs = max(1, analyst.get("max_concurrent_jobs", 5))
                if current_jobs >= max_jobs:
                    continue
                
                # Calculate score based on skills match, availability, and current workload
                score = await self._calculate_analyst_score(job, analyst)
                
                if score > best_score:
                    best_score = score
                    best_analyst = analyst
            
            return best_analyst
            
        except Exception as e:
            logger.error(f"Error finding best analyst: {str(e)}")
            return None
    
    async def _calculate_analyst_score(self, job: Dict[str, Any], analyst: Dict[str, Any]) -> float:
        """Calculate analyst suitability score for a job."""
        try:
            score = 0.0
            
            # Skills match (40% weight)
            if analyst["skills"]:
                # This would check job requirements against analyst skills
                skills_match = 0.5  # Placeholder
                score += skills_match * 0.4
            
            # Availability (30% weight)
            availability_score = await self._calculate_availability_score(analyst)
            score += availability_score * 0.3
            
            # Workload balance (20% weight)
            current_jobs = analyst.get("current_job_count", 0)
            max_jobs = max(1, analyst.get("max_concurrent_jobs", 5))
            workload_score = 1.0 - (current_jobs / max_jobs)
            score += workload_score * 0.2
            
            # Performance history (10% weight)
            performance_score = 0.8  # Placeholder - would be based on historical data
            score += performance_score * 0.1
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating analyst score: {str(e)}")
            return 0.0
    
    async def _calculate_availability_score(self, analyst: Dict[str, Any]) -> float:
        """Calculate analyst availability score."""
        try:
            # This would check analyst availability against current time
            # For now, return a placeholder score
            return 0.8
            
        except Exception as e:
            logger.error(f"Error calculating availability score: {str(e)}")
            return 0.0
    
    async def _calculate_schedule(self, job: Dict[str, Any], analyst: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate optimal schedule for job and analyst."""
        try:
            # Start time would be based on analyst availability and current time
            start_time = datetime.utcnow() + timedelta(hours=1)
            
            # End time based on SLA
            end_time = start_time + timedelta(hours=job["sla_hours"])
            
            # Confidence score based on various factors
            confidence_score = 0.85  # Placeholder
            
            return {
                "start_time": start_time,
                "end_time": end_time,
                "confidence_score": confidence_score
            }
            
        except Exception as e:
            logger.error(f"Error calculating schedule: {str(e)}")
            raise 