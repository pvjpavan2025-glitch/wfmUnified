"""Configuration management for the BPMN workflow engine."""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    app_name: str = "BPMN Workflow Engine"
    app_version: str = "0.1.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # API
    api_prefix: str = "/api/v1"
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    database_echo: bool = Field(default=False, env="DATABASE_ECHO")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    redis_db: int = Field(default=0, env="REDIS_DB")
    
    # Workflow Engine
    max_workflow_instances: int = Field(default=1000, env="MAX_WORKFLOW_INSTANCES")
    workflow_timeout_seconds: int = Field(default=3600, env="WORKFLOW_TIMEOUT_SECONDS")
    max_task_retries: int = Field(default=3, env="MAX_TASK_RETRIES")
    
    # BPMN Processing
    max_bpmn_file_size: int = Field(default=10 * 1024 * 1024, env="MAX_BPMN_FILE_SIZE")  # 10MB
    allowed_bpmn_extensions: list[str] = Field(default=[".bpmn", ".xml"], env="ALLOWED_BPMN_EXTENSIONS")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="CORS_ORIGINS"
    )
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = Field(default=["*"], env="CORS_ALLOW_METHODS")
    cors_allow_headers: list[str] = Field(default=["*"], env="CORS_ALLOW_HEADERS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
