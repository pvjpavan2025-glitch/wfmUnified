"""Main FastAPI application for the BPMN workflow engine."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .core.config import settings
from .core.database import init_db, close_db
from .core.redis_client import redis_client
from .engine.workflow_engine import WorkflowEngine, WorkflowExecutionError
from .api.workflows import router as workflows_router
from .api.tasks import router as tasks_router
from .api.executions import router as executions_router


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
app.include_router(tasks_router, prefix=f"{settings.api_prefix}/tasks", tags=["tasks"])
app.include_router(executions_router, prefix=f"{settings.api_prefix}/executions", tags=["executions"])


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
        
        return {
            "status": "healthy" if redis_healthy else "unhealthy",
            "timestamp": "2024-01-01T00:00:00Z",  # Replace with actual timestamp
            "services": {
                "redis": "connected" if redis_healthy else "disconnected",
                "database": "connected",  # Add actual database health check
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


@app.post("/start-workflow/{workflow_id}")
async def start_workflow(
    workflow_id: str,
    input_data: dict = None,
    instance_id: str = None
):
    """Start a workflow instance."""
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


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
