"""
Router for API Gateway.
"""
from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import JSONResponse
import httpx
import structlog

logger = structlog.get_logger(__name__)


class APIRouter:
    """API Router for service routing."""
    
    def __init__(self):
        self.service_urls = {
            "auth": "http://localhost:8001",
            "config": "http://localhost:8002",
            "rules": "http://localhost:8003",
            "scheduler": "http://localhost:8004",
            "issue": "http://localhost:8005",
            "analytics": "http://localhost:8006"
        }
    
    async def route_request(self, request: Request, service: str, path: str) -> JSONResponse:
        """Route request to appropriate service."""
        try:
            # Get service URL
            service_url = self.service_urls.get(service)
            if not service_url:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Service '{service}' not available"
                )
            
            # Prepare request
            url = f"{service_url}{path}"
            method = request.method
            headers = dict(request.headers)
            
            # Remove host header to avoid conflicts
            headers.pop("host", None)
            
            # Get request body
            body = await request.body()
            
            # Forward request
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    content=body,
                    timeout=30.0
                )
                
                # Return response
                return JSONResponse(
                    content=response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
                
        except httpx.RequestError as e:
            logger.error(f"Request error forwarding to {service}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Service '{service}' is not available"
            )
        except Exception as e:
            logger.error(f"Error forwarding request to {service}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def get_service_for_path(self, path: str) -> str:
        """Determine service based on path."""
        if path.startswith("/auth") or path.startswith("/users"):
            return "auth"
        elif path.startswith("/configs"):
            return "config"
        elif path.startswith("/rules"):
            return "rules"
        elif path.startswith("/jobs"):
            return "scheduler"
        elif path.startswith("/issues"):
            return "issue"
        elif path.startswith("/reports") or path.startswith("/metrics"):
            return "analytics"
        else:
            return None 