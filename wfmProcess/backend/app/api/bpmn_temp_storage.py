"""BPMN temporary storage API endpoints."""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel, Field

from ..core.redis_client import redis_client

logger = logging.getLogger(__name__)

router = APIRouter()

# Constants
TEMP_STORAGE_PREFIX = "bpmn_temp"
DEFAULT_EXPIRY_HOURS = 24
MAX_STORAGE_SIZE = 5 * 1024 * 1024  # 5MB max per BPMN


class BpmnTempStorageRequest(BaseModel):
    """Request model for storing BPMN temporarily."""
    xml: str = Field(..., description="BPMN XML content")
    filename: str = Field(..., description="Original filename")
    session_id: str = Field(..., description="User session ID")
    overwrite: bool = Field(default=False, description="Whether to overwrite existing files")


class BpmnTempStorageResponse(BaseModel):
    """Response model for BPMN storage operations."""
    success: bool
    key: Optional[str] = None
    message: str
    timestamp: str


class BpmnTempData(BaseModel):
    """BPMN temporary data model."""
    xml: str
    filename: str
    session_id: str
    timestamp: str
    size: int


def generate_storage_key(session_id: str, filename: str) -> str:
    """Generate a unique storage key."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Remove file extension for key generation
    base_filename = filename.rsplit('.', 1)[0] if '.' in filename else filename
    return f"{TEMP_STORAGE_PREFIX}:{session_id}:{base_filename}:{timestamp}"


def get_session_pattern(session_id: str) -> str:
    """Get Redis pattern for session keys."""
    return f"{TEMP_STORAGE_PREFIX}:{session_id}:*"


async def cleanup_expired_entries():
    """Clean up expired entries (background task)."""
    try:
        if not redis_client.redis:
            await redis_client.connect()
        
        if redis_client.redis:
            # Get all temp storage keys
            pattern = f"{TEMP_STORAGE_PREFIX}:*"
            keys = await redis_client.redis.keys(pattern)
            
            expired_count = 0
            for key in keys:
                # Check if key exists (Redis will auto-expire)
                if not await redis_client.exists(key):
                    expired_count += 1
            
            logger.info(f"Cleanup completed: {expired_count} expired entries removed")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")


@router.post("/store", response_model=BpmnTempStorageResponse)
async def store_bpmn_temporarily(request: BpmnTempStorageRequest):
    """Store BPMN XML temporarily in Redis."""
    try:
        # Validate input
        if not request.xml.strip():
            raise HTTPException(status_code=400, detail="BPMN XML content cannot be empty")
        
        if len(request.xml.encode('utf-8')) > MAX_STORAGE_SIZE:
            raise HTTPException(
                status_code=400, 
                detail=f"BPMN XML size exceeds maximum allowed size of {MAX_STORAGE_SIZE} bytes"
            )
        
        # Basic XML validation
        if not request.xml.strip().startswith('<'):
            raise HTTPException(status_code=400, detail="Invalid XML format")
        
        # Check for existing files if overwrite is False
        if not request.overwrite:
            session_pattern = get_session_pattern(request.session_id)
            if not redis_client.redis:
                await redis_client.connect()
            
            if redis_client.redis:
                existing_keys = await redis_client.redis.keys(session_pattern)
                
                # Check if any existing key contains the same base filename
                base_filename = request.filename.rsplit('.', 1)[0] if '.' in request.filename else request.filename
                for existing_key in existing_keys:
                    if base_filename in existing_key:
                        # Get existing data to check filename
                        existing_data = await redis_client.get(existing_key)
                        if existing_data and isinstance(existing_data, dict):
                            existing_base = existing_data.get('filename', '').rsplit('.', 1)[0]
                            if existing_base == base_filename:
                                raise HTTPException(
                                    status_code=409, 
                                    detail=f"File with similar name already exists. Use overwrite=true to replace it."
                                )
        
        # Generate storage key
        storage_key = generate_storage_key(request.session_id, request.filename)
        
        # If overwriting, delete existing files with same base name
        if request.overwrite:
            session_pattern = get_session_pattern(request.session_id)
            if not redis_client.redis:
                await redis_client.connect()
            
            if redis_client.redis:
                existing_keys = await redis_client.redis.keys(session_pattern)
                base_filename = request.filename.rsplit('.', 1)[0] if '.' in request.filename else request.filename
                
                for existing_key in existing_keys:
                    if base_filename in existing_key:
                        existing_data = await redis_client.get(existing_key)
                        if existing_data and isinstance(existing_data, dict):
                            existing_base = existing_data.get('filename', '').rsplit('.', 1)[0]
                            if existing_base == base_filename:
                                await redis_client.delete(existing_key)
        
        # Prepare data for storage
        storage_data = BpmnTempData(
            xml=request.xml,
            filename=request.filename,
            session_id=request.session_id,
            timestamp=datetime.now().isoformat(),
            size=len(request.xml.encode('utf-8'))
        )
        
        # Store in Redis with expiration
        expiry_seconds = DEFAULT_EXPIRY_HOURS * 3600
        success = await redis_client.set(
            storage_key, 
            storage_data.dict(), 
            expire=expiry_seconds
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to store BPMN in Redis")
        
        message = "BPMN stored successfully"
        if request.overwrite:
            message = "BPMN stored successfully (overwrote existing)"
        
        return BpmnTempStorageResponse(
            success=True,
            key=storage_key,
            message=message,
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error storing BPMN temporarily: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/retrieve/{key}")
async def retrieve_bpmn_by_key(key: str):
    """Retrieve BPMN by storage key."""
    try:
        # Validate key format
        if not key.startswith(TEMP_STORAGE_PREFIX):
            raise HTTPException(status_code=400, detail="Invalid storage key format")
        
        # Get data from Redis
        data = await redis_client.get(key)
        
        if not data:
            raise HTTPException(status_code=404, detail="BPMN not found or expired")
        
        return {
            "success": True,
            "data": data,
            "message": "BPMN retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving BPMN by key: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/list/{session_id}")
async def list_session_bpmns(session_id: str):
    """List all BPMN files for a session."""
    try:
        if not redis_client.redis:
            await redis_client.connect()
        
        # Get all keys for this session
        session_pattern = get_session_pattern(session_id)
        keys = []
        if redis_client.redis:
            keys = await redis_client.redis.keys(session_pattern)
        
        session_items = []
        for key in keys:
            data = await redis_client.get(key)
            if data and isinstance(data, dict):
                session_items.append({
                    "key": key,
                    "filename": data.get("filename"),
                    "timestamp": data.get("timestamp"),
                    "size": data.get("size", 0)
                })
        
        # Sort by timestamp (newest first)
        session_items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return {
            "success": True,
            "data": session_items,
            "count": len(session_items),
            "message": f"Found {len(session_items)} BPMN files for session"
        }
        
    except Exception as e:
        logger.error(f"Error listing session BPMNs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/delete/{key}")
async def delete_bpmn_by_key(key: str):
    """Delete BPMN by storage key."""
    try:
        # Validate key format
        if not key.startswith(TEMP_STORAGE_PREFIX):
            raise HTTPException(status_code=400, detail="Invalid storage key format")
        
        # Check if key exists
        if not await redis_client.exists(key):
            raise HTTPException(status_code=404, detail="BPMN not found")
        
        # Delete from Redis
        success = await redis_client.delete(key)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete BPMN")
        
        return {
            "success": True,
            "message": "BPMN deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting BPMN by key: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/delete-session/{session_id}")
async def delete_session_bpmns(session_id: str):
    """Delete all BPMN files for a session."""
    try:
        if not redis_client.redis:
            await redis_client.connect()
        
        # Get all keys for this session
        session_pattern = get_session_pattern(session_id)
        keys = []
        if redis_client.redis:
            keys = await redis_client.redis.keys(session_pattern)
        
        if not keys:
            return {
                "success": True,
                "message": "No BPMN files found for session",
                "deleted_count": 0
            }
        
        # Delete all keys
        deleted_count = 0
        for key in keys:
            if await redis_client.delete(key):
                deleted_count += 1
        
        return {
            "success": True,
            "message": f"Deleted {deleted_count} BPMN files for session",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        logger.error(f"Error deleting session BPMNs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/cleanup")
async def manual_cleanup():
    """Manually trigger cleanup of expired entries."""
    try:
        await cleanup_expired_entries()
        return {
            "success": True,
            "message": "Cleanup completed successfully"
        }
        
    except Exception as e:
        logger.error(f"Error during manual cleanup: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/stats")
async def get_storage_stats():
    """Get temporary storage statistics."""
    try:
        if not redis_client.redis:
            await redis_client.connect()
        
        # Get all temp storage keys
        pattern = f"{TEMP_STORAGE_PREFIX}:*"
        keys = []
        if redis_client.redis:
            keys = await redis_client.redis.keys(pattern)
        
        total_files = len(keys)
        total_size = 0
        sessions = set()
        
        for key in keys:
            data = await redis_client.get(key)
            if data and isinstance(data, dict):
                total_size += data.get("size", 0)
                sessions.add(data.get("session_id"))
        
        return {
            "success": True,
            "stats": {
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "active_sessions": len(sessions),
                "max_file_size_mb": MAX_STORAGE_SIZE / (1024 * 1024),
                "default_expiry_hours": DEFAULT_EXPIRY_HOURS
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting storage stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
