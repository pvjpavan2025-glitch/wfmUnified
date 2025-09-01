"""Main FastAPI application for the BPMN workflow engine."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import uvicorn

from .core.config import settings
from .core.database import init_db, close_db
from .core.redis_client import redis_client
from .core.mongodb import init_mongodb, close_mongodb
from .engine.workflow_engine import WorkflowEngine, WorkflowExecutionError
from .api.workflows import router as workflows_router
from .api.enhanced_workflows import router as enhanced_workflows_router
from .api.tasks import router as tasks_router
from .api.executions import router as executions_router
from .api.processes import router as process_management_router
from .api.bpmn_temp_storage import router as bpmn_temp_storage_router


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting BPMN Workflow Engine...")
    
    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized successfully")
        
        # Initialize MongoDB
        await init_mongodb()
        logger.info("MongoDB initialized successfully")
        
        # Initialize Redis
        await redis_client.connect()
        logger.info("Redis connected successfully")
        
        # Initialize workflow engine
        app.state.workflow_engine = WorkflowEngine()
        logger.info("Workflow engine initialized successfully")
        
        logger.info("BPMN Workflow Engine started successfully")
        yield
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    finally:
        # Shutdown
        logger.info("Shutting down BPMN Workflow Engine...")
        
        try:
            # Close Redis connection
            await redis_client.disconnect()
            logger.info("Redis disconnected successfully")
            
            # Close database connections
            await close_db()
            logger.info("Database connections closed successfully")
            
            # Close MongoDB connection
            await close_mongodb()
            logger.info("MongoDB disconnected successfully")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        
        logger.info("BPMN Workflow Engine shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A modern, cloud-native BPMN workflow execution engine",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Include API routers
app.include_router(workflows_router, prefix=f"{settings.api_prefix}/workflows", tags=["workflows"])
app.include_router(enhanced_workflows_router, prefix=f"{settings.api_prefix}/enhanced-workflows", tags=["enhanced-workflows"])
app.include_router(tasks_router, prefix=f"{settings.api_prefix}/tasks", tags=["tasks"])
app.include_router(executions_router, prefix=f"{settings.api_prefix}/executions", tags=["executions"])
app.include_router(process_management_router, prefix=f"{settings.api_prefix}/processes", tags=["processes"])
app.include_router(bpmn_temp_storage_router, prefix=f"{settings.api_prefix}/bpmn-temp", tags=["bpmn-temp-storage"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "BPMN Workflow Engine API",
        "version": settings.app_version,
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check Redis connection
        redis_healthy = await redis_client.ping()
        
        # Check MongoDB connection
        from .core.mongodb import health_check as mongodb_health_check
        mongodb_healthy = await mongodb_health_check()
        
        return {
            "status": "healthy" if redis_healthy and mongodb_healthy else "unhealthy",
            "timestamp": "2024-01-01T00:00:00Z",  # Replace with actual timestamp
            "services": {
                "redis": "connected" if redis_healthy else "disconnected",
                "database": "connected",  # Add actual database health check
                "mongodb": "connected" if mongodb_healthy else "disconnected",
                "workflow_engine": "running"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": "2024-01-01T00:00:00Z"  # Replace with actual timestamp
            }
        )


@app.post("/upload-bpmn")
async def upload_bpmn(
    file: UploadFile = File(...),
    name: str = None,
    version: str = "1.0.0"
):
    """Upload and parse BPMN file."""
    try:
        # Validate file
        if not file.filename.endswith(('.bpmn', '.xml')):
            raise HTTPException(
                status_code=400, 
                detail="Only .bpmn and .xml files are allowed"
            )
        
        # Read file content
        content = await file.read()
        if len(content) > settings.max_bpmn_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {settings.max_bpmn_file_size} bytes"
            )
        
        # Parse BPMN
        bpmn_xml = content.decode('utf-8')
        workflow_engine: WorkflowEngine = app.state.workflow_engine
        
        workflow_def = await workflow_engine.create_workflow_definition(
            bpmn_xml=bpmn_xml,
            name=name or file.filename,
            version=version
        )
        
        return {
            "message": "BPMN file uploaded and parsed successfully",
            "workflow_definition": {
                "id": workflow_def.bpmn_id,
                "name": workflow_def.name,
                "version": workflow_def.version,
                "process_id": workflow_def.process_id,
                "task_count": len(workflow_def.task_definitions)
            }
        }
        
    except WorkflowExecutionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to upload BPMN file: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/execute-process")
async def execute_process(
    request_data: Dict[str, Any] = Body(...)
):
    """Execute a BPMN process for an order."""
    try:
        workflow_engine: WorkflowEngine = app.state.workflow_engine
        
        # Extract required fields
        order_id = request_data.get("order_id")
        process_definition_key = request_data.get("process_definition_key")
        bpmn_xml = request_data.get("bpmn_xml")
        input_data = request_data.get("input_data", {})
        tenant_id = request_data.get("tenant_id")
        auto_assign_tasks = request_data.get("auto_assign_tasks", False)
        
        if not all([order_id, process_definition_key, bpmn_xml, tenant_id]):
            raise HTTPException(
                status_code=400, 
                detail="Missing required fields: order_id, process_definition_key, bpmn_xml, tenant_id"
            )
        
        # Create workflow definition from BPMN XML
        workflow_def = await workflow_engine.create_workflow_definition(
            bpmn_xml=bpmn_xml,
            name=f"Process {process_definition_key} for Order {order_id}",
            version="1.0.0",
            process_id=process_definition_key
        )
        
        # Start workflow instance
        instance_id = f"{order_id}_{process_definition_key}_{tenant_id}"
        workflow_instance = await workflow_engine.start_workflow(
            workflow_definition=workflow_def,
            input_data={
                **input_data,
                "order_id": order_id,
                "tenant_id": tenant_id,
                "process_definition_key": process_definition_key
            },
            instance_id=instance_id
        )
        
        # Extract task information
        tasks = []
        for task_def in workflow_def.task_definitions:
            task_info = {
                "id": task_def.task_id,
                "name": task_def.name,
                "type": task_def.task_type,
                "status": "pending",
                "assignee": None,
                "created_at": workflow_instance.created_at.isoformat() if hasattr(workflow_instance, 'created_at') else None
            }
            tasks.append(task_info)
        
        return {
            "id": workflow_instance.instance_id,
            "order_id": order_id,
            "process_definition_key": process_definition_key,
            "status": workflow_instance.status,
            "tasks": tasks,
            "tenant_id": tenant_id,
            "auto_assign_tasks": auto_assign_tasks,
            "created_at": workflow_instance.created_at.isoformat() if hasattr(workflow_instance, 'created_at') else None
        }
        
    except WorkflowExecutionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to execute process: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/start-workflow/{workflow_id}")
async def start_workflow(
    workflow_id: str,
    input_data: dict = None,
    instance_id: str = None
):
    """Start a workflow instance (legacy endpoint)."""
    try:
        workflow_engine: WorkflowEngine = app.state.workflow_engine
        
        # For now, we'll create a mock workflow definition
        # In a real implementation, you'd fetch this from the database
        from .models.workflow import WorkflowDefinition
        mock_workflow_def = WorkflowDefinition(
            id=1,
            name="Mock Workflow",
            version="1.0.0",
            bpmn_xml="<mock>",
            bpmn_id=workflow_id,
            process_id="mock_process",
            is_executable=True
        )
        
        workflow_instance = await workflow_engine.start_workflow(
            workflow_definition=mock_workflow_def,
            input_data=input_data or {},
            instance_id=instance_id
        )
        
        return {
            "message": "Workflow started successfully",
            "instance_id": workflow_instance.instance_id,
            "status": workflow_instance.status
        }
        
    except WorkflowExecutionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to start workflow: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/workflow-status/{instance_id}")
async def get_workflow_status(instance_id: str):
    """Get workflow instance status."""
    try:
        workflow_engine: WorkflowEngine = app.state.workflow_engine
        status = await workflow_engine.get_workflow_status(instance_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Workflow instance not found")
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/complete-task")
async def complete_task(
    request_data: Dict[str, Any] = Body(...)
):
    """Complete a task in a workflow instance."""
    try:
        workflow_engine: WorkflowEngine = app.state.workflow_engine
        
        instance_id = request_data.get("instance_id")
        task_id = request_data.get("task_id")
        output_data = request_data.get("output_data", {})
        
        if not all([instance_id, task_id]):
            raise HTTPException(
                status_code=400,
                detail="Missing required fields: instance_id, task_id"
            )
        
        success = await workflow_engine.complete_task(
            instance_id=instance_id,
            task_id=task_id,
            output_data=output_data
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Task or workflow instance not found"
            )
        
        return {
            "message": "Task completed successfully",
            "instance_id": instance_id,
            "task_id": task_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to complete task: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/process-instances/{instance_id}/tasks")
async def get_process_tasks(instance_id: str):
    """Get all tasks for a process instance."""
    try:
        workflow_engine: WorkflowEngine = app.state.workflow_engine
        tasks = await workflow_engine.get_instance_tasks(instance_id)
        
        if tasks is None:
            raise HTTPException(status_code=404, detail="Process instance not found")
        
        return tasks
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get process tasks: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/stop-workflow/{instance_id}")
async def stop_workflow(instance_id: str):
    """Stop a workflow instance."""
    try:
        workflow_engine: WorkflowEngine = app.state.workflow_engine
        success = await workflow_engine.stop_workflow(instance_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Workflow instance not found")
        
        return {"message": "Workflow stopped successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop workflow: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/save-bpmn")
async def save_bpmn(
    request_data: Dict[str, Any] = Body(...)
):
    """Save BPMN diagram to database."""
    try:
        workflow_engine: WorkflowEngine = app.state.workflow_engine
        
        name = request_data.get("name")
        bpmn_xml = request_data.get("bpmn_xml")
        version = request_data.get("version", "1.0.0")
        process_id = request_data.get("process_id")
        
        if not all([name, bpmn_xml]):
            raise HTTPException(
                status_code=400,
                detail="Missing required fields: name, bpmn_xml"
            )
        
        workflow_def = await workflow_engine.create_workflow_definition(
            bpmn_xml=bpmn_xml,
            name=name,
            version=version,
            process_id=process_id
        )
        
        return {
            "message": "BPMN diagram saved successfully",
            "workflow_definition": {
                "id": workflow_def.bpmn_id,
                "name": workflow_def.name,
                "version": workflow_def.version,
                "process_id": workflow_def.process_id,
                "task_count": len(workflow_def.task_definitions)
            }
        }
        
    except WorkflowExecutionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to save BPMN diagram: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/bpmn-diagrams")
async def list_bpmn_diagrams():
    """List all saved BPMN diagrams."""
    try:
        workflow_engine: WorkflowEngine = app.state.workflow_engine
        diagrams = await workflow_engine.list_workflow_definitions()
        
        return {
            "diagrams": [
                {
                    "id": diagram.bpmn_id,
                    "name": diagram.name,
                    "version": diagram.version,
                    "process_id": diagram.process_id,
                    "task_count": len(diagram.task_definitions),
                    "is_executable": diagram.is_executable
                }
                for diagram in diagrams
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to list BPMN diagrams: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/bpmn-diagrams/{diagram_id}")
async def get_bpmn_diagram(diagram_id: str):
    """Get a specific BPMN diagram."""
    try:
        workflow_engine: WorkflowEngine = app.state.workflow_engine
        diagram = await workflow_engine.get_workflow_definition(diagram_id)
        
        if not diagram:
            raise HTTPException(status_code=404, detail="BPMN diagram not found")
        
        return {
            "id": diagram.bpmn_id,
            "name": diagram.name,
            "version": diagram.version,
            "process_id": diagram.process_id,
            "bpmn_xml": diagram.bpmn_xml,
            "task_count": len(diagram.task_definitions),
            "is_executable": diagram.is_executable,
            "tasks": [
                {
                    "id": task.task_id,
                    "name": task.name,
                    "type": task.task_type
                }
                for task in diagram.task_definitions
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get BPMN diagram: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
