"""
Business logic layer for Intelligent Scheduler Service.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import structlog
import httpx
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
        self.process_service_url = "http://localhost:8008"  # process service
        self.vendor_service_url = "http://localhost:8007"  # vendor service
    
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
    
    async def schedule_task_instance(self, task_instance_id: str, tenant_id: str) -> Dict[str, Any]:
        """Schedule a task instance using vendor service technicians."""
        try:
            # Get task instance from process service
            async with httpx.AsyncClient() as client:
                task_response = await client.get(
                    f"{self.process_service_url}/task-instances/{task_instance_id}"
                )
                
                if task_response.status_code != 200:
                    raise ValueError(f"Task instance {task_instance_id} not found")
                
                task_instance = task_response.json()
                
                # Get available technicians from vendor service
                technicians_response = await client.get(
                    f"{self.vendor_service_url}/technicians",
                    params={"status": "available"}
                )
                
                if technicians_response.status_code != 200:
                    raise ValueError("Failed to get available technicians")
                
                technicians = technicians_response.json()
                
                if not technicians:
                    raise ValueError("No available technicians found")
                
                # Find best technician for the task
                best_technician = await self._find_best_technician(task_instance, technicians)
                if not best_technician:
                    raise ValueError("No suitable technician found for this task")
                
                # Get lead for the technician
                lead_response = await client.get(
                    f"{self.vendor_service_url}/technicians/{best_technician['id']}/lead"
                )
                
                if lead_response.status_code != 200:
                    raise ValueError(f"No lead found for technician {best_technician['id']}")
                
                lead = lead_response.json()
                
                # Calculate schedule
                schedule = await self._calculate_task_schedule(task_instance, best_technician)
                
                # Assign task via vendor service
                assignment_data = {
                    "task_instance_id": task_instance_id,
                    "technician_id": best_technician["id"],
                    "lead_id": lead["id"],
                    "scheduled_start": schedule["start_time"].isoformat(),
                    "scheduled_end": schedule["end_time"].isoformat(),
                    "notes": f"Auto-scheduled by scheduler service"
                }
                
                assignment_response = await client.post(
                    f"{self.vendor_service_url}/task-assignments",
                    json=assignment_data
                )
                
                if assignment_response.status_code != 200:
                    raise ValueError("Failed to assign task to technician")
                
                assignment = assignment_response.json()
                
                # Update task instance with assignment
                task_update = {
                    "assigned_technician_id": best_technician["id"],
                    "assigned_lead_id": lead["id"],
                    "scheduled_start": schedule["start_time"].isoformat(),
                    "scheduled_end": schedule["end_time"].isoformat(),
                    "status": "scheduled"
                }
                
                await client.put(
                    f"{self.process_service_url}/task-instances/{task_instance_id}",
                    json=task_update
                )
                
                logger.info(f"Task {task_instance_id} scheduled with technician {best_technician['name']}")
                
                return {
                    "task_instance_id": task_instance_id,
                    "technician_id": best_technician["id"],
                    "technician_name": best_technician["name"],
                    "lead_id": lead["id"],
                    "lead_name": lead["name"],
                    "start_time": schedule["start_time"],
                    "end_time": schedule["end_time"],
                    "confidence_score": schedule["confidence_score"],
                    "assignment_id": assignment.get("id")
                }
                
        except Exception as e:
            logger.error(f"Failed to schedule task instance {task_instance_id}: {str(e)}")
            raise
    
    async def schedule_multiple_tasks(self, task_instance_ids: List[str], tenant_id: str) -> List[Dict[str, Any]]:
        """Schedule multiple task instances."""
        results = []
        
        for task_id in task_instance_ids:
            try:
                result = await self.schedule_task_instance(task_id, tenant_id)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to schedule task {task_id}: {str(e)}")
                results.append({
                    "task_instance_id": task_id,
                    "error": str(e),
                    "status": "failed"
                })
        
        return results
    
    async def get_technician_schedule(self, technician_id: str, tenant_id: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get schedule for a specific technician."""
        try:
            async with httpx.AsyncClient() as client:
                # Get technician's assigned tasks from vendor service
                response = await client.get(
                    f"{self.vendor_service_url}/technicians/{technician_id}/task-assignments",
                    params={
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat()
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Failed to get schedule for technician {technician_id}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting technician schedule: {str(e)}")
            return []
    
    async def _find_best_technician(self, task_instance: Dict[str, Any], technicians: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find the best technician for a task instance."""
        try:
            best_technician = None
            best_score = 0.0
            
            required_skills = task_instance.get("required_skills", [])
            
            for technician in technicians:
                if technician.get("status", "inactive") != "available":
                    continue
                
                # Calculate score based on skills match, availability, and current workload
                score = await self._calculate_technician_score(task_instance, technician, required_skills)
                
                if score > best_score:
                    best_score = score
                    best_technician = technician
            
            return best_technician
            
        except Exception as e:
            logger.error(f"Error finding best technician: {str(e)}")
            return None
    
    async def _calculate_technician_score(self, task_instance: Dict[str, Any], technician: Dict[str, Any], required_skills: List[str]) -> float:
        """Calculate technician suitability score for a task instance."""
        try:
            score = 0.0
            
            # Skills match (50% weight)
            technician_skills = technician.get("skills", [])
            if required_skills and technician_skills:
                matching_skills = set(required_skills) & set(technician_skills)
                skills_match = len(matching_skills) / len(required_skills) if required_skills else 1.0
                score += skills_match * 0.5
            elif not required_skills:
                score += 0.5  # No specific skills required
            
            # Availability (30% weight)
            availability_score = await self._calculate_technician_availability_score(technician)
            score += availability_score * 0.3
            
            # Experience level (20% weight)
            experience_level = technician.get("experience_level", "junior")
            experience_score = {"senior": 1.0, "mid": 0.7, "junior": 0.4}.get(experience_level, 0.4)
            score += experience_score * 0.2
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating technician score: {str(e)}")
            return 0.0
    
    async def _calculate_technician_availability_score(self, technician: Dict[str, Any]) -> float:
        """Calculate technician availability score."""
        try:
            # Check current workload
            current_tasks = technician.get("current_task_count", 0)
            max_tasks = technician.get("max_concurrent_tasks", 3)
            
            if current_tasks >= max_tasks:
                return 0.0
            
            # Calculate availability based on workload
            availability_score = 1.0 - (current_tasks / max_tasks)
            return availability_score
            
        except Exception as e:
            logger.error(f"Error calculating availability score: {str(e)}")
            return 0.0
    
    async def _calculate_task_schedule(self, task_instance: Dict[str, Any], technician: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate optimal schedule for task instance and technician."""
        try:
            # Start time based on technician availability and task priority
            priority = task_instance.get("priority", "medium")
            
            if priority == "urgent":
                start_time = datetime.utcnow() + timedelta(minutes=30)
            elif priority == "high":
                start_time = datetime.utcnow() + timedelta(hours=2)
            else:
                start_time = datetime.utcnow() + timedelta(hours=4)
            
            # End time based on estimated duration
            estimated_duration = task_instance.get("estimated_duration_hours", 2)
            end_time = start_time + timedelta(hours=estimated_duration)
            
            # Confidence score based on various factors
            confidence_score = 0.8  # Placeholder - would be based on historical data and current conditions
            
            return {
                "start_time": start_time,
                "end_time": end_time,
                "confidence_score": confidence_score
            }
            
        except Exception as e:
            logger.error(f"Error calculating task schedule: {str(e)}")
            raise