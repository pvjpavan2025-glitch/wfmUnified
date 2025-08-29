"""Process management service for BPMN workflows."""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from ..models.process_models import (
    Process, ProcessCreate, ProcessUpdate, ProcessSummary,
    ProcessInstance, ProcessInstanceCreate, ProcessInstanceUpdate, ProcessInstanceSummary,
    Template, TemplateCreate, TemplateUpdate, TemplateSummary
)
from ..core.mongodb import get_mongodb_database


class ProcessService:
    """Service for managing BPMN processes."""
    
    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        if db is None:
            self.db = get_mongodb_database()
        else:
            self.db = db
    
    async def create_process(self, process_data: ProcessCreate, user_id: str) -> Process:
        """Create a new process."""
        try:
            # Generate unique process ID
            process_id = f"process_{uuid.uuid4().hex[:8]}"
            
            # Create process document
            process_dict = process_data.dict()
            process_dict["process_id"] = process_id
            process_dict["created_by"] = user_id
            process_dict["updated_by"] = user_id
            process_dict["created_at"] = datetime.utcnow()
            process_dict["updated_at"] = datetime.utcnow()
            process_dict["status"] = "active"  # Set default status
            
            # Insert into database
            result = await self.db.processes.insert_one(process_dict)
            
            # Convert ObjectId to string for the response
            process_dict["_id"] = str(result.inserted_id)
            
            return Process(**process_dict)
            
        except Exception as e:
            raise Exception(f"Failed to create process: {str(e)}")
    
    async def get_process(self, process_id: str) -> Optional[Process]:
        """Get process by ID."""
        try:
            # Try to find by ObjectId first
            if ObjectId.is_valid(process_id):
                process_doc = await self.db.processes.find_one({"_id": ObjectId(process_id)})
            else:
                # Try to find by process_id field
                process_doc = await self.db.processes.find_one({"process_id": process_id})
            
            if process_doc:
                return Process(**process_doc)
            return None
            
        except Exception as e:
            raise Exception(f"Failed to get process: {str(e)}")
    
    async def list_processes(
        self,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> List[ProcessSummary]:
        """List processes with filtering and pagination."""
        try:
            # Build filter
            filter_query = {}
            
            if category:
                filter_query["category"] = category
            
            if is_active is not None:
                filter_query["is_active"] = is_active
            
            if search:
                filter_query["$or"] = [
                    {"name": {"$regex": search, "$options": "i"}},
                    {"description": {"$regex": search, "$options": "i"}},
                    {"tags": {"$in": [search]}}
                ]
            
            # Execute query
            cursor = self.db.processes.find(filter_query).skip(skip).limit(limit).sort("updated_at", -1)
            processes = await cursor.to_list(length=limit)
            
            # Convert to ProcessSummary with proper field mapping
            process_summaries = []
            for process in processes:
                # Convert ObjectId to string
                process["_id"] = str(process["_id"])
                
                # Ensure required fields exist with defaults
                if "execution_count" not in process:
                    process["execution_count"] = 0
                if "last_executed_at" not in process:
                    process["last_executed_at"] = None
                if "status" not in process:
                    process["status"] = "active"
                
                process_summaries.append(ProcessSummary(**process))
            
            return process_summaries
            
        except Exception as e:
            raise Exception(f"Failed to list processes: {str(e)}")
    
    async def update_process(self, process_id: str, update_data: ProcessUpdate, user_id: str) -> Optional[Process]:
        """Update process."""
        try:
            # Prepare update data
            update_dict = update_data.dict(exclude_unset=True)
            update_dict["updated_by"] = user_id
            update_dict["updated_at"] = datetime.utcnow()
            
            # Execute update
            if ObjectId.is_valid(process_id):
                result = await self.db.processes.update_one(
                    {"_id": ObjectId(process_id)},
                    {"$set": update_dict}
                )
            else:
                result = await self.db.processes.update_one(
                    {"process_id": process_id},
                    {"$set": update_dict}
                )
            
            if result.modified_count > 0:
                return await self.get_process(process_id)
            return None
            
        except Exception as e:
            raise Exception(f"Failed to update process: {str(e)}")
    
    async def delete_process(self, process_id: str) -> bool:
        """Delete process."""
        try:
            if ObjectId.is_valid(process_id):
                result = await self.db.processes.delete_one({"_id": ObjectId(process_id)})
            else:
                result = await self.db.processes.delete_one({"process_id": process_id})
            
            return result.deleted_count > 0
            
        except Exception as e:
            raise Exception(f"Failed to delete process: {str(e)}")
    
    async def create_process_instance(self, instance_data: ProcessInstanceCreate, user_id: str) -> ProcessInstance:
        """Create a new process instance."""
        try:
            # Generate unique instance ID
            instance_id = f"inst_{uuid.uuid4().hex[:8]}"
            
            # Create instance document
            instance_dict = instance_data.dict()
            instance_dict["instance_id"] = instance_id
            instance_dict["started_by"] = user_id
            instance_dict["started_at"] = datetime.utcnow()
            instance_dict["current_state"] = {}
            instance_dict["execution_path"] = []
            
            # Insert into database
            result = await self.db.process_instances.insert_one(instance_dict)
            instance_dict["_id"] = result.inserted_id
            
            # Update process execution count
            await self.db.processes.update_one(
                {"process_id": instance_data.process_id},
                {
                    "$inc": {"execution_count": 1},
                    "$set": {"last_executed_at": datetime.utcnow()}
                }
            )
            
            return ProcessInstance(**instance_dict)
            
        except Exception as e:
            raise Exception(f"Failed to create process instance: {str(e)}")
    
    async def list_process_instances(
        self,
        skip: int = 0,
        limit: int = 100,
        process_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[ProcessInstanceSummary]:
        """List process instances with filtering and pagination."""
        try:
            # Build filter
            filter_query = {}
            
            if process_id:
                filter_query["process_id"] = process_id
            
            if status:
                filter_query["status"] = status
            
            # Execute query
            cursor = self.db.process_instances.find(filter_query).skip(skip).limit(limit).sort("started_at", -1)
            instances = await cursor.to_list(length=limit)
            
            # Convert to ProcessInstanceSummary
            return [ProcessInstanceSummary(**instance) for instance in instances]
            
        except Exception as e:
            raise Exception(f"Failed to list process instances: {str(e)}")
    
    async def update_process_instance(self, instance_id: str, update_data: ProcessInstanceUpdate) -> Optional[ProcessInstance]:
        """Update process instance."""
        try:
            # Prepare update data
            update_dict = update_data.dict(exclude_unset=True)
            update_dict["updated_at"] = datetime.utcnow()
            
            # Execute update
            if ObjectId.is_valid(instance_id):
                result = await self.db.process_instances.update_one(
                    {"_id": ObjectId(instance_id)},
                    {"$set": update_dict}
                )
            else:
                result = await self.db.process_instances.update_one(
                    {"instance_id": instance_id},
                    {"$set": update_dict}
                )
            
            if result.modified_count > 0:
                # Get updated instance
                if ObjectId.is_valid(instance_id):
                    instance_doc = await self.db.process_instances.find_one({"_id": ObjectId(instance_id)})
                else:
                    instance_doc = await self.db.process_instances.find_one({"instance_id": instance_id})
                
                if instance_doc:
                    return ProcessInstance(**instance_doc)
            
            return None
            
        except Exception as e:
            raise Exception(f"Failed to update process instance: {str(e)}")
    
    async def get_process_instance(self, instance_id: str) -> Optional[ProcessInstance]:
        """Get process instance by ID."""
        try:
            if ObjectId.is_valid(instance_id):
                instance_doc = await self.db.process_instances.find_one({"_id": ObjectId(instance_id)})
            else:
                instance_doc = await self.db.process_instances.find_one({"instance_id": instance_id})
            
            if instance_doc:
                return ProcessInstance(**instance_doc)
            return None
            
        except Exception as e:
            raise Exception(f"Failed to get process instance: {str(e)}")


class TemplateService:
    """Service for managing BPMN templates."""
    
    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        if db is None:
            self.db = get_mongodb_database()
        else:
            self.db = db
    
    async def create_template(self, template_data: TemplateCreate, user_id: str) -> Template:
        """Create a new template."""
        try:
            # Generate unique process ID if not provided
            if not template_data.process_id:
                template_data.process_id = f"template_{uuid.uuid4().hex[:8]}"
            
            # Create template document
            template_dict = template_data.dict()
            template_dict["created_by"] = user_id
            template_dict["updated_by"] = user_id
            template_dict["created_at"] = datetime.utcnow()
            template_dict["updated_at"] = datetime.utcnow()
            template_dict["usage_count"] = 0
            
            # Insert into database
            result = await self.db.templates.insert_one(template_dict)
            template_dict["_id"] = result.inserted_id
            
            return Template(**template_dict)
            
        except Exception as e:
            raise Exception(f"Failed to create template: {str(e)}")
    
    async def get_template(self, template_id: str) -> Optional[Template]:
        """Get template by ID."""
        try:
            if ObjectId.is_valid(template_id):
                template_doc = await self.db.templates.find_one({"_id": ObjectId(template_id)})
            else:
                template_doc = await self.db.templates.find_one({"process_id": template_id})
            
            if template_doc:
                return Template(**template_doc)
            return None
            
        except Exception as e:
            raise Exception(f"Failed to get template: {str(e)}")
    
    async def list_templates(
        self,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        is_public: Optional[bool] = None,
        is_active: Optional[bool] = None
    ) -> List[TemplateSummary]:
        """List templates with filtering and pagination."""
        try:
            # Build filter
            filter_query = {}
            
            if category:
                filter_query["category"] = category
            
            if is_public is not None:
                filter_query["is_public"] = is_public
            
            if is_active is not None:
                filter_query["is_active"] = is_active
            
            # Execute query
            cursor = self.db.templates.find(filter_query).skip(skip).limit(limit).sort("created_at", -1)
            templates = await cursor.to_list(length=limit)
            
            # Convert to TemplateSummary
            return [TemplateSummary(**template) for template in templates]
            
        except Exception as e:
            raise Exception(f"Failed to list templates: {str(e)}")
    
    async def update_template(self, template_id: str, update_data: TemplateUpdate, user_id: str) -> Optional[Template]:
        """Update template."""
        try:
            # Prepare update data
            update_dict = update_data.dict(exclude_unset=True)
            update_dict["updated_by"] = user_id
            update_dict["updated_at"] = datetime.utcnow()
            
            # Execute update
            if ObjectId.is_valid(template_id):
                result = await self.db.templates.update_one(
                    {"_id": ObjectId(template_id)},
                    {"$set": update_dict}
                )
            else:
                result = await self.db.templates.update_one(
                    {"process_id": template_id},
                    {"$set": update_dict}
                )
            
            if result.modified_count > 0:
                return await self.get_template(template_id)
            return None
            
        except Exception as e:
            raise Exception(f"Failed to update template: {str(e)}")
    
    async def delete_template(self, template_id: str) -> bool:
        """Delete template."""
        try:
            if ObjectId.is_valid(template_id):
                result = await self.db.templates.delete_one({"_id": ObjectId(template_id)})
            else:
                result = await self.db.templates.delete_one({"process_id": template_id})
            
            return result.deleted_count > 0
            
        except Exception as e:
            raise Exception(f"Failed to delete template: {str(e)}")
    
    async def increment_template_usage(self, template_id: str) -> bool:
        """Increment template usage count."""
        try:
            if ObjectId.is_valid(template_id):
                result = await self.db.templates.update_one(
                    {"_id": ObjectId(template_id)},
                    {
                        "$inc": {"usage_count": 1},
                        "$set": {"last_used_at": datetime.utcnow()}
                    }
                )
            else:
                result = await self.db.templates.update_one(
                    {"process_id": template_id},
                    {
                        "$inc": {"usage_count": 1},
                        "$set": {"last_used_at": datetime.utcnow()}
                    }
                )
            
            return result.modified_count > 0
            
        except Exception as e:
            raise Exception(f"Failed to increment template usage: {str(e)}")
    
    async def create_template_from_process(self, process_id: str, template_data: TemplateCreate, user_id: str) -> Template:
        """Create a template from an existing process."""
        try:
            # Get the process
            process_service = ProcessService(self.db)
            process = await process_service.get_process(process_id)
            
            if not process:
                raise Exception("Process not found")
            
            # Create template with process data
            template_dict = template_data.dict()
            template_dict["bpmn_xml"] = process.bpmn_xml
            template_dict["process_id"] = f"template_{uuid.uuid4().hex[:8]}"
            template_dict["source_process_id"] = process_id
            template_dict["variables"] = process.variables
            template_dict["metadata"] = process.metadata
            template_dict["created_by"] = user_id
            template_dict["updated_by"] = user_id
            template_dict["created_at"] = datetime.utcnow()
            template_dict["updated_at"] = datetime.utcnow()
            template_dict["usage_count"] = 0
            
            # Insert into database
            result = await self.db.templates.insert_one(template_dict)
            template_dict["_id"] = result.inserted_id
            
            return Template(**template_dict)
            
        except Exception as e:
            raise Exception(f"Failed to create template from process: {str(e)}")


# Service instances - will be created when needed
# process_service = ProcessService()
# template_service = TemplateService()
