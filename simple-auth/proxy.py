"""
Simple API Gateway Proxy for WFM Services
"""
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import json
from datetime import datetime

app = FastAPI(title="WFM API Gateway", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs
AUTH_SERVICE_URL = "http://auth-service:8001"
PROCESS_ENGINE_URL = "http://wfm-process:8090"

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "simple-api-gateway"}

@app.api_route("/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_auth(path: str, request: Request):
    """Proxy authentication requests to auth service."""
    try:
        # Get request body
        body = await request.body()
        
        # Prepare headers
        headers = dict(request.headers)
        # Remove host header to avoid conflicts
        headers.pop("host", None)
        
        # Make request to auth service
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=request.method,
                url=f"{AUTH_SERVICE_URL}/auth/{path}",
                content=body,
                headers=headers,
                timeout=30.0
            )
            
            # Return response
            return response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
    
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Dashboard endpoints - mock data for now
@app.get("/dashboard/metrics")
async def get_dashboard_metrics():
    """Get dashboard metrics."""
    return {
        "active_jobs": {
            "count": 15,
            "change_percentage": 12.5,
            "change_direction": "up"
        },
        "available_technicians": {
            "count": 8,
            "change_percentage": 5.2,
            "change_direction": "up"
        },
        "scheduled_today": {
            "count": 28,
            "change_percentage": 8.1,
            "change_direction": "up"
        },
        "completion_rate": {
            "percentage": 87,
            "change_percentage": 3.4,
            "change_direction": "up"
        },
        "total_jobs": 42,
        "completed_jobs": 37,
        "system_health": "healthy",
        "last_updated": datetime.now().isoformat()
    }

@app.get("/dashboard/recent-jobs")
async def get_recent_jobs():
    """Get recent jobs."""
    return [
        {
            "id": "wo-001",
            "job_number": "WO-001",
            "description": "Fiber Installation",
            "location": "125 Oak St, Cedar Park, TX",
            "priority": "High",
            "status": "in_progress",
            "progress": 65,
            "due_date": "2025-08-27T10:00:00Z",
            "technician_name": "John Smith",
            "estimated_hours": 4,
            "actual_hours": 2
        },
        {
            "id": "wo-002",
            "job_number": "WO-002",
            "description": "Cable Laying",
            "location": "464 Maple Ave, Lakewood, TX",
            "priority": "Medium",
            "status": "pending",
            "progress": 0,
            "due_date": "2025-08-28T14:00:00Z",
            "technician_name": "Sarah Johnson",
            "estimated_hours": 6,
            "actual_hours": 0
        },
        {
            "id": "wo-003",
            "job_number": "WO-003",
            "description": "Splicing Work",
            "location": "4 Paintapple Ave, Mountains, TX",
            "priority": "Low",
            "status": "completed",
            "progress": 100,
            "due_date": "2025-08-26T09:00:00Z",
            "technician_name": "Mike Davis",
            "estimated_hours": 3,
            "actual_hours": 3
        }
    ]

@app.api_route("/vendors", methods=["GET"])
async def get_vendors(request: Request):
    """Get vendors list."""
    return {
        "vendors": [
            {"id": 1, "name": "Acme Corp", "status": "active", "contracts": 3},
            {"id": 2, "name": "TechFlow Solutions", "status": "active", "contracts": 2},
            {"id": 3, "name": "ServicePro Inc", "status": "pending", "contracts": 1}
        ],
        "total": 3
    }

@app.api_route("/settings", methods=["GET"])
async def get_settings(request: Request):
    """Get system settings."""
    return {
        "system": {
            "timezone": "UTC",
            "language": "en",
            "theme": "light"
        },
        "notifications": {
            "email": True,
            "sms": False,
            "push": True
        }
    }

@app.api_route("/reports", methods=["GET"])
async def get_reports(request: Request):
    """Get reports list."""
    return {
        "reports": [
            {"id": 1, "name": "Weekly Performance", "type": "performance", "last_run": "2025-08-25T10:30:00Z"},
            {"id": 2, "name": "Monthly Summary", "type": "summary", "last_run": "2025-08-01T09:00:00Z"},
            {"id": 3, "name": "Vendor Analysis", "type": "vendor", "last_run": "2025-08-20T14:15:00Z"}
        ],
        "total": 3
    }

# Process engine proxy
@app.api_route("/workflows/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_workflows(path: str, request: Request):
    """Proxy workflow requests to process engine."""
    try:
        # Get request body
        body = await request.body()
        
        # Prepare headers
        headers = dict(request.headers)
        headers.pop("host", None)
        
        # Make request to process engine
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=request.method,
                url=f"{PROCESS_ENGINE_URL}/workflows/{path}",
                content=body,
                headers=headers,
                timeout=30.0
            )
            
            return response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
    
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Process engine unavailable: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
