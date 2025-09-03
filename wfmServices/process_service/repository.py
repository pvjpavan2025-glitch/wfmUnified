"""
Repository layer for Process Service.
"""
from typing import List, Optional
from datetime import datetime
from shared.database import get_database
from shared.models import PaginationParams
from .models import ProcessInstance, TaskInstance


class ProcessInstanceRepository:
    """Repository for process instance operations."""
    
    def __init__(self):
        self.db = None
        self.collection = None
    
    async def initialize(self):
        """Initialize database connection."""
        if not self.db:
            self.db = await get_database()
            self.collection = self.db.process_instances
    
    async def create(self, process_instance: ProcessInstance) -> ProcessInstance:
        """Create a new process instance."""
        instance_dict = process_instance.model_dump(by_alias=True)
        result = await self.collection.insert_one(instance_dict)
        process_instance.id = str(result.inserted_id)
        return process_instance
    
    async def get_by_id(self, instance_id: str, tenant_id: str) -> Optional[ProcessInstance]:
        """Get process instance by ID."""
        instance_dict = await self.collection.find_one({
            "_id": instance_id,
            "tenant_id": tenant_id
        })
        return ProcessInstance(**instance_dict) if instance_dict else None
    
    async def get_by_order(self, order_id: str, tenant_id: str) -> List[ProcessInstance]:
        """Get all process instances for an order."""
        cursor = self.collection.find({
            "order_id": order_id,
            "tenant_id": tenant_id
        })
        instances = []
        async for instance_dict in cursor:
            instances.append(ProcessInstance(**instance_dict))
        return instances
    
    async def get_by_process(self, process_id: str, tenant_id: str, pagination: PaginationParams) -> List[ProcessInstance]:
        """Get all instances of a process."""
        cursor = self.collection.find({
            "process_id": process_id,
            "tenant_id": tenant_id
        })
        cursor = cursor.skip(pagination.skip).limit(pagination.limit)
        instances = []
        async for instance_dict in cursor:
            instances.append(ProcessInstance(**instance_dict))
        return instances
    
    async def get_by_status(self, status: str, tenant_id: str) -> List[ProcessInstance]:
        """Get process instances by status."""
        cursor = self.collection.find({
            "status": status,
            "tenant_id": tenant_id
        })
        instances = []
        async for instance_dict in cursor:
            instances.append(ProcessInstance(**instance_dict))
        return instances
    
    async def update(self, instance_id: str, tenant_id: str, update_data: dict) -> Optional[ProcessInstance]:
        """Update process instance."""
        update_data["updated_at"] = datetime.utcnow()
        result = await self.collection.update_one(
            {"_id": instance_id, "tenant_id": tenant_id},
            {"$set": update_data}
        )
        if result.modified_count:
            return await self.get_by_id(instance_id, tenant_id)
        return None
    
    async def delete(self, instance_id: str, tenant_id: str) -> bool:
        """Delete process instance."""
        result = await self.collection.delete_one({
            "_id": instance_id,
            "tenant_id": tenant_id
        })
        return result.deleted_count > 0


class TaskInstanceRepository:
    """Repository for task instance operations."""
    
    def __init__(self):
        self.db = None
        self.collection = None
    
    async def initialize(self):
        """Initialize database connection."""
        if not self.db:
            self.db = await get_database()
            self.collection = self.db.task_instances
    
    async def create(self, task_instance: TaskInstance) -> TaskInstance:
        """Create a new task instance."""
        instance_dict = task_instance.model_dump(by_alias=True)
        result = await self.collection.insert_one(instance_dict)
        task_instance.id = str(result.inserted_id)
        return task_instance
    
    async def get_by_id(self, instance_id: str, tenant_id: str) -> Optional[TaskInstance]:
        """Get task instance by ID."""
        instance_dict = await self.collection.find_one({
            "_id": instance_id,
            "tenant_id": tenant_id
        })
        return TaskInstance(**instance_dict) if instance_dict else None
    
    async def get_by_process_instance(self, process_instance_id: str, tenant_id: str) -> List[TaskInstance]:
        """Get all task instances for a process instance."""
        cursor = self.collection.find({
            "process_instance_id": process_instance_id,
            "tenant_id": tenant_id
        })
        instances = []
        async for instance_dict in cursor:
            instances.append(TaskInstance(**instance_dict))
        return instances
    
    async def get_by_technician(self, technician_id: str, tenant_id: str) -> List[TaskInstance]:
        """Get all task instances assigned to a technician."""
        cursor = self.collection.find({
            "assigned_technician_id": technician_id,
            "tenant_id": tenant_id
        })
        instances = []
        async for instance_dict in cursor:
            instances.append(TaskInstance(**instance_dict))
        return instances
    
    async def get_by_status(self, status: str, tenant_id: str) -> List[TaskInstance]:
        """Get task instances by status."""
        cursor = self.collection.find({
            "status": status,
            "tenant_id": tenant_id
        })
        instances = []
        async for instance_dict in cursor:
            instances.append(TaskInstance(**instance_dict))
        return instances
    
    async def get_unassigned_tasks(self, tenant_id: str, required_skills: Optional[List[str]] = None) -> List[TaskInstance]:
        """Get unassigned task instances, optionally filtered by required skills."""
        query = {
            "assigned_technician_id": None,
            "status": {"$in": ["pending", "ready"]},
            "tenant_id": tenant_id
        }
        
        if required_skills:
            query["required_skills"] = {"$in": required_skills}
        
        cursor = self.collection.find(query)
        instances = []
        async for instance_dict in cursor:
            instances.append(TaskInstance(**instance_dict))
        return instances
    
    async def update(self, instance_id: str, tenant_id: str, update_data: dict) -> Optional[TaskInstance]:
        """Update task instance."""
        update_data["updated_at"] = datetime.utcnow()
        result = await self.collection.update_one(
            {"_id": instance_id, "tenant_id": tenant_id},
            {"$set": update_data}
        )
        if result.modified_count:
            return await self.get_by_id(instance_id, tenant_id)
        return None
    
    async def delete(self, instance_id: str, tenant_id: str) -> bool:
        """Delete task instance."""
        result = await self.collection.delete_one({
            "_id": instance_id,
            "tenant_id": tenant_id
        })
        return result.deleted_count > 0
