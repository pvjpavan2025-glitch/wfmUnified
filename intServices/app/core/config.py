from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl
from typing import List
import os

class Settings(BaseSettings):
    app_name: str = "Integration Layer"
    env: str = "dev"
    port: int = 8082

    allowed_origins: str = ""

    database_url: str = "postgresql+asyncpg://intsvc:intsvc@localhost:5432/intservices"

    api_key_name: str = "X-API-Key"
    api_key: str = "change-me-please"

    jwt_secret: str = "change-me-please"
    jwt_alg: str = "HS256"
    access_token_expire_minutes: int = 30

    # Default to wfmServices rules-service port (override via env RULES_API_BASE_URL)
    rules_api_base_url: AnyHttpUrl = "http://localhost:8003"
    rules_api_token: str = ""
    rules_api_timeout_seconds: int = 15
    rules_api_stub: bool = False

    # Optional: generate JWT for Rules API if token not provided
    rules_jwt_secret: str = ""
    rules_jwt_alg: str = "HS256"
    rules_jwt_expire_minutes: int = 30
    rules_user_id: str = "integration-system"
    rules_username: str = "integration"
    rules_tenant_id: str = "default-tenant"
    rules_roles: str = "admin"

    # Scheduler API
    scheduler_api_base_url: AnyHttpUrl = "http://localhost:8004"
    scheduler_api_token: str = ""
    scheduler_api_timeout_seconds: int = 15
    scheduler_api_stub: bool = True

    # Order API (Order Service in wfmServices)
    order_api_base_url: AnyHttpUrl = "http://localhost:8008"
    order_api_token: str = ""
    order_api_timeout_seconds: int = 15

    @property
    def rules_roles_list(self):
        return [r.strip() for r in self.rules_roles.split(",") if r.strip()]

    @property
    def allowed_origins_list(self) -> List[str]:
        if not self.allowed_origins:
            return []
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    class Config:
        env_prefix = ""
        env_file = os.getenv("ENV_FILE", ".env")
        case_sensitive = False

settings = Settings()
