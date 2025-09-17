"""
Shared configuration module for WFM microservices.
"""
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    # MongoDB settings
    mongodb_url: str = Field(default="mongodb://localhost:27017", env="MONGODB_URL")
    database_name: str = Field(default="wfm", env="DATABASE_NAME")
    # TLS/SSL settings
    mongodb_tls: bool = Field(default=True, env="MONGODB_TLS")
    mongodb_tls_allow_invalid_certificates: bool = Field(default=False, env="MONGODB_TLS_ALLOW_INVALID_CERTIFICATES")
    mongodb_tls_ca_file: str = Field(default="/etc/ssl/certs/ca-certificates.crt", env="MONGODB_TLS_CA_FILE")
    
    # Redis settings
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # PostgreSQL settings
    postgres_user: str = Field(default="workflow_user", env="POSTGRES_USER")
    postgres_password: str = Field(default="workflow_pass", env="POSTGRES_PASSWORD")
    postgres_host: str = Field(default="localhost", env="POSTGRES_HOST")
    postgres_port: str = Field(default="5432", env="POSTGRES_PORT")
    postgres_db: str = Field(default="workflow", env="POSTGRES_DB")
    sql_database_url: Optional[str] = Field(default=None, env="POSTGRESQL_URL")


class SecuritySettings(BaseSettings):
    """Security configuration settings."""
    jwt_secret_key: str = Field(default="your-super-secret-jwt-key-change-in-production", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_minutes: int = Field(default=30, env="JWT_EXPIRATION_MINUTES")
    bcrypt_rounds: int = Field(default=12, env="BCRYPT_ROUNDS")


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    enable_correlation_id: bool = Field(default=True, env="ENABLE_CORRELATION_ID")


class ServiceSettings(BaseSettings):
    """Service-specific configuration settings."""
    service_name: str = Field(default="wfm-service", env="SERVICE_NAME")
    service_port: int = Field(default=8000, env="SERVICE_PORT")
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")


class Settings(BaseSettings):
    """Main settings class combining all configuration."""
    database: DatabaseSettings = DatabaseSettings()
    security: SecuritySettings = SecuritySettings()
    logging: LoggingSettings = LoggingSettings()
    service: ServiceSettings = ServiceSettings()

    class Config:
        env_file = "env.online"
        case_sensitive = False
        extra = "ignore"


# Global settings instance
settings = Settings() 