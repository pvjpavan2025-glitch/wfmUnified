"""
Middleware for API Gateway.
"""
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog
import redis.asyncio as redis

logger = structlog.get_logger(__name__)


class CorrelationMiddleware(BaseHTTPMiddleware):
    """Middleware to add correlation IDs to requests."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate correlation ID if not present
        correlation_id = request.headers.get("X-Correlation-ID")
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        # Add correlation ID to request state
        request.state.correlation_id = correlation_id
        
        # Add correlation ID to headers
        request.headers.__dict__["_list"].append(
            (b"x-correlation-id", correlation_id.encode())
        )
        
        # Process request
        response = await call_next(request)
        
        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting."""
    
    def __init__(self, app, redis_client: redis.Redis = None):
        super().__init__(app)
        self.redis_client = redis_client
        self.rate_limit = 100  # requests per minute
        self.window = 60  # seconds
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self.redis_client:
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Create rate limit key
        rate_limit_key = f"rate_limit:{client_ip}"
        
        try:
            # Check current request count
            current_count = await self.redis_client.get(rate_limit_key)
            
            if current_count and int(current_count) >= self.rate_limit:
                logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                return Response(
                    content="Rate limit exceeded",
                    status_code=429,
                    headers={"Retry-After": str(self.window)}
                )
            
            # Increment request count
            pipe = self.redis_client.pipeline()
            pipe.incr(rate_limit_key)
            pipe.expire(rate_limit_key, self.window)
            await pipe.execute()
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(self.rate_limit)
            response.headers["X-RateLimit-Remaining"] = str(
                max(0, self.rate_limit - (int(current_count or 0) + 1))
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Rate limiting error: {str(e)}")
            return await call_next(request)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware for authentication."""
    
    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/auth/login",
            "/docs",
            "/openapi.json"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip authentication for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Check for authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return Response(
                content="Missing or invalid authorization header",
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Extract token
        token = auth_header.split(" ")[1]
        
        # Verify token (basic check - full verification done in services)
        if not token:
            return Response(
                content="Invalid token",
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Add user info to request state
        request.state.token = token
        
        return await call_next(request)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Log request start
        start_time = time.time()
        correlation_id = getattr(request.state, "correlation_id", "unknown")
        
        logger.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else "unknown",
            correlation_id=correlation_id
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Log response
            duration = time.time() - start_time
            logger.info(
                "Request completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration=duration,
                correlation_id=correlation_id
            )
            
            return response
            
        except Exception as e:
            # Log error
            duration = time.time() - start_time
            logger.error(
                "Request failed",
                method=request.method,
                path=request.url.path,
                error=str(e),
                duration=duration,
                correlation_id=correlation_id
            )
            raise 