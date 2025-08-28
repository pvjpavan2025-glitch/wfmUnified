from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from .config import settings

api_key_header = APIKeyHeader(name=settings.api_key_name, auto_error=False)

def validate_api_key(api_key: str = Security(api_key_header)):
    if not settings.api_key:
        return  # disabled
    if api_key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return api_key
