"""
Dashboard Service business logic.
"""
import structlog
from datetime import datetime, timedelta
from typing import Dict, List, Any
from bson import ObjectId

logger = structlog.get_logger()


class DashboardService:
    """Dashboard service for calculating metrics and fetching data."""
    
    def __init__(self, database):
        """Initialize dashboard service."""
        self.database = database
    
    async def get_dashboard_metrics(self, tenant_id: str) -> Dict[str, Any]:
        """Get dashboard metrics for a tenant."""
        try:
            logger.info(f"Getting dashboard metrics for tenant: {tenant_id}")
            
            # Convert tenant_id to ObjectId
            tenant_object_id = ObjectId(tenant_id)
            
            # Check if collections exist, if not return default metrics
            collections = await self.database.list_collection_names()
            logger.info(f"Available collections: {collections}")
            
            # Get active jobs (jobs that are not completed)
            active_jobs_count = 0
            if "jobs" in collections:
                active_jobs_pipeline = [
                    {"$match": {"tenant_id": tenant_object_id, "status": {"$ne": "completed"}}},
                    {"$count": "count"}
                ]
                active_jobs_result = await self.database.jobs.aggregate(active_jobs_pipeline).to_list(1)
                active_jobs_count = active_jobs_result[0]["count"] if active_jobs_result else 0
            
            # Get available technicians
            available_technicians_count = 0
            if "technicians" in collections:
                available_technicians_pipeline = [
                    {"$match": {"tenant_id": tenant_object_id, "status": "available"}},
                    {"$count": "count"}
                ]
                available_technicians_result = await self.database.technicians.aggregate(available_technicians_pipeline).to_list(1)
                available_technicians_count = available_technicians_result[0]["count"] if available_technicians_result else 0
            
            # Get jobs scheduled for today
            scheduled_today_count = 0
            if "jobs" in collections:
                today = datetime.utcnow().date()
                today_start = datetime.combine(today, datetime.min.time())
                today_end = datetime.combine(today, datetime.max.time())
                
                scheduled_today_pipeline = [
                    {"$match": {
                        "tenant_id": tenant_object_id,
                        "due_date": {"$gte": today_start, "$lte": today_end}
                    }},
                    {"$count": "count"}
                ]
                scheduled_today_result = await self.database.jobs.aggregate(scheduled_today_pipeline).to_list(1)
                scheduled_today_count = scheduled_today_result[0]["count"] if scheduled_today_result else 0
            
            # Get completion rate (completed jobs vs total jobs)
            total_jobs_count = 0
            completed_jobs_count = 0
            if "jobs" in collections:
                total_jobs_pipeline = [
                    {"$match": {"tenant_id": tenant_object_id}},
                    {"$count": "count"}
                ]
                total_jobs_result = await self.database.jobs.aggregate(total_jobs_pipeline).to_list(1)
                total_jobs_count = total_jobs_result[0]["count"] if total_jobs_result else 0
                
                completed_jobs_pipeline = [
                    {"$match": {"tenant_id": tenant_object_id, "status": "completed"}},
                    {"$count": "count"}
                ]
                completed_jobs_result = await self.database.jobs.aggregate(completed_jobs_pipeline).to_list(1)
                completed_jobs_count = completed_jobs_result[0]["count"] if completed_jobs_result else 0
            
            # Calculate completion rate
            completion_rate = 0
            if total_jobs_count > 0:
                completion_rate = round((completed_jobs_count / total_jobs_count) * 100, 1)
            
            # Calculate percentage changes (mock data for now)
            active_jobs_change = 12  # +12% from last month
            available_technicians_change = 5  # +5% from last month
            scheduled_today_change = -2  # -2% from last month
            completion_rate_change = 3  # +3% from last month
            
            metrics = {
                "active_jobs": {
                    "count": active_jobs_count,
                    "change_percentage": active_jobs_change,
                    "change_direction": "up" if active_jobs_change > 0 else "down"
                },
                "available_technicians": {
                    "count": available_technicians_count,
                    "change_percentage": available_technicians_change,
                    "change_direction": "up" if available_technicians_change > 0 else "down"
                },
                "scheduled_today": {
                    "count": scheduled_today_count,
                    "change_percentage": scheduled_today_change,
                    "change_direction": "up" if scheduled_today_change > 0 else "down"
                },
                "completion_rate": {
                    "percentage": completion_rate,
                    "change_percentage": completion_rate_change,
                    "change_direction": "up" if completion_rate_change > 0 else "down"
                },
                "total_jobs": total_jobs_count,
                "completed_jobs": completed_jobs_count
            }
            
            logger.info(f"Dashboard metrics calculated successfully for tenant: {tenant_id}")
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get dashboard metrics: {str(e)}")
            raise
    
    async def get_recent_jobs(self, tenant_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent jobs for dashboard display."""
        try:
            logger.info(f"Getting recent jobs for tenant: {tenant_id}")
            
            # Convert tenant_id to ObjectId
            tenant_object_id = ObjectId(tenant_id)
            
            # Get recent jobs with technician information
            pipeline = [
                {"$match": {"tenant_id": tenant_object_id}},
                {"$sort": {"updated_at": -1}},
                {"$limit": limit},
                {"$lookup": {
                    "from": "technicians",
                    "localField": "assigned_to",
                    "foreignField": "_id",
                    "as": "technician"
                }},
                {"$unwind": {"path": "$technician", "preserveNullAndEmptyArrays": True}},
                {"$project": {
                    "job_number": 1,
                    "description": 1,
                    "location": 1,
                    "priority": 1,
                    "status": 1,
                    "progress": 1,
                    "due_date": 1,
                    "assigned_to": 1,
                    "technician_name": "$technician.name",
                    "estimated_hours": 1,
                    "actual_hours": 1,
                    "created_at": 1,
                    "updated_at": 1
                }}
            ]
            
            recent_jobs = await self.database.jobs.aggregate(pipeline).to_list(limit)
            
            # Convert ObjectIds to strings for JSON serialization
            for job in recent_jobs:
                if "_id" in job:
                    job["id"] = str(job["_id"])
                    del job["_id"]
                if "assigned_to" in job and job["assigned_to"]:
                    job["assigned_to"] = str(job["assigned_to"])
                if "due_date" in job and job["due_date"]:
                    job["due_date"] = job["due_date"].isoformat()
                if "created_at" in job and job["created_at"]:
                    job["created_at"] = job["created_at"].isoformat()
                if "updated_at" in job and job["updated_at"]:
                    job["updated_at"] = job["updated_at"].isoformat()
            
            logger.info(f"Retrieved {len(recent_jobs)} recent jobs for tenant: {tenant_id}")
            return recent_jobs
            
        except Exception as e:
            logger.error(f"Failed to get recent jobs: {str(e)}")
            raise
    

    async def get_technicians(
        self,
        tenant_id: str,
        status: str = None,
        sort_order: str = "asc",
        limit: int = 10,
        page: int = 1
    ) -> List[Dict[str, Any]]:
        """Get technicians with optional filtering, sorting, and pagination."""
        try:
            logger.info(f"Getting technicians for tenant: {tenant_id}")
            tenant_object_id = ObjectId(tenant_id)

            # Base query filter
            match_query = {"tenant_id": tenant_object_id}
            if status:
                match_query["status"] = status

            sort_direction = 1 if sort_order == "asc" else -1

            pipeline = [
                {"$match": match_query},
                {"$sort": {"status": sort_direction}},
                {"$skip": (page - 1) * limit},
                {"$limit": limit},
                {
                    "$project": {
                        "id": {"$toString": "$_id"},
                        "name": 1,
                        "skills": 1,  # Array of skills
                        "profile_photo": 1,
                        "status": 1,
                        "shift": 1,
                        "location": 1,
                        "languages": 1,
                        "number": 1,
                        "mail": 1,
                        "completed_tasks": 1,
                        "rating": 1
                    }
                }
            ]

            technicians = await self.database.technicians.aggregate(pipeline).to_list(length=limit)

            # Ensure all IDs are strings
            for tech in technicians:
                if "_id" in tech:
                    tech["id"] = str(tech["_id"])
                    del tech["_id"]

            logger.info(f"Retrieved {len(technicians)} technicians for tenant: {tenant_id}")
            return technicians

        except Exception as e:
            logger.error(f"Failed to get technicians: {str(e)}")
            raise

    
    async def get_orders(self, tenant_id: str, limit: int = 10, status_filter: str = None) -> List[Dict[str, Any]]:
        """Get orders with tasks and progress calculation."""
        try:
            logger.info(f"Getting orders for tenant: {tenant_id}")

            tenant_object_id = ObjectId(tenant_id)

            match_stage = {"tenant_id": tenant_object_id}
            if status_filter:
                match_stage["status"] = status_filter

            pipeline = [
                {"$match": match_stage},
                {"$sort": {"created_at": -1}},
                {"$limit": limit},
                {
                    "$lookup": {
                        "from": "tasks",   # renamed collection from sub_orders
                        "localField": "_id",
                        "foreignField": "order_id",
                        "as": "tasks"
                    }
                },
                {
                    "$project": {
                        "order_id": {"$toString": "$_id"},
                        "customer_name": 1,
                        "order_type": 1,
                        "status": 1,
                        "priority": 1,
                        "location": 1,
                        "assigned_technician": {"$toString": "$assigned_technician"},
                        "created_at": 1,
                        "tasks": 1
                    }
                }
            ]

            orders = await self.database.orders.aggregate(pipeline).to_list(limit)

            for order in orders:
                tasks = order.get("tasks", [])
                total_tasks = len(tasks)
                completed_tasks = sum(1 for t in tasks if t.get("status") == "completed")
                order["progress"] = round((completed_tasks / total_tasks) * 100, 1) if total_tasks > 0 else 0

                for task in tasks:
                    if "_id" in task:
                        task["task_id"] = str(task["_id"])
                        del task["_id"]
                    if "order_id" in task:
                        task["order_id"] = str(task["order_id"])
                    if "assigned_technician" in task and task["assigned_technician"]:
                        task["assigned_technician"] = str(task["assigned_technician"])
                    if "created_at" in task and task["created_at"]:
                        task["created_at"] = task["created_at"].isoformat()
                    if "due_date" in task and task["due_date"]:
                        task["due_date"] = task["due_date"].isoformat()

                if "created_at" in order and order["created_at"]:
                    order["created_at"] = order["created_at"].isoformat()

            logger.info(f"Retrieved {len(orders)} orders for tenant: {tenant_id}")
            return orders

        except Exception as e:
            logger.error(f"Failed to get orders: {str(e)}")
            raise



    # tasks services
    async def get_task(self, tenant_id: str, task_id: str) -> Dict[str, Any]:
            """Get task details."""
            try:
                tenant_object_id = ObjectId(tenant_id)
                task = await self.database.tasks.find_one(
                    {"_id": ObjectId(task_id), "tenant_id": tenant_object_id}
                )
                if not task:
                    return None
                task["id"] = str(task["_id"])
                del task["_id"]
                return task
            except Exception as e:
                logger.error(f"Failed to get task: {str(e)}")
                raise

    async def update_task(self, tenant_id: str, task_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update task details (progress, status, etc.)."""
        try:
            tenant_object_id = ObjectId(tenant_id)
            updates["updated_at"] = datetime.utcnow()
            await self.database.tasks.update_one(
                {"_id": ObjectId(task_id), "tenant_id": tenant_object_id},
                {"$set": updates}
            )
            return await self.get_task(tenant_id, task_id)
        except Exception as e:
            logger.error(f"Failed to update task: {str(e)}")
            raise

    async def assign_task(self, tenant_id: str, task_id: str, analyst_id: str) -> Dict[str, Any]:
        """Assign an analyst to a task."""
        try:
            tenant_object_id = ObjectId(tenant_id)
            update = {
                "assigned_to": ObjectId(analyst_id),
                "status": "assigned",
                "updated_at": datetime.utcnow()
            }
            await self.database.tasks.update_one(
                {"_id": ObjectId(task_id), "tenant_id": tenant_object_id},
                {"$set": update}
            )
            return await self.get_task(tenant_id, task_id)
        except Exception as e:
            logger.error(f"Failed to assign task: {str(e)}")
            raise

    async def complete_task(self, tenant_id: str, task_id: str, actual_hours: str = None) -> Dict[str, Any]:
        """Mark a task as completed."""
        try:
            tenant_object_id = ObjectId(tenant_id)
            update = {
                "status": "completed",
                "progress": 100,
                "completed_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            if actual_hours:
                update["actual_hours"] = actual_hours

            await self.database.tasks.update_one(
                {"_id": ObjectId(task_id), "tenant_id": tenant_object_id},
                {"$set": update}
            )
            return await self.get_task(tenant_id, task_id)
        except Exception as e:
            logger.error(f"Failed to complete task: {str(e)}")
            raise