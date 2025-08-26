"""
Simple API Gateway Proxy for Authentication
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import httpx
import json

app = FastAPI(title="Simple API Gateway", version="1.0.0")

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
