"""
Shared library for WFM microservices.

This module provides common utilities, models, and configurations
that are shared across all microservices in the WFM system.
"""

# Configuration
from .config import settings, DatabaseSettings, SecuritySettings, LoggingSettings, ServiceSettings

# Authentication
from .auth import (
    TokenManager, 
    TokenData, 
    TokenResponse, 
    token_manager,
    get_current_user,
    get_current_user_optional,
    require_roles,
    require_tenant_access,
    get_password_hash,
    verify_password,
    create_access_token
)

# Logging and Monitoring
from .logging import (
    get_logger,
    setup_logging,
    get_correlation_id,
    set_correlation_id,
    generate_correlation_id,
    metrics_collector,
    monitor_performance,
    PerformanceMonitor
)

# Distributed Tracing
from .tracing import (
    Tracer,
    TraceContext,
    Span,
    SpanContext,
    SpanKind,
    TracingHTTPClient,
    tracer,
    get_trace_id,
    set_trace_id,
    get_span_id,
    set_span_id,
    get_parent_span_id,
    set_parent_span_id,
    trace_operation
)

# Database
from .database import get_database, get_redis_client

# Models
from .models import (
    BaseModel,
    User,
    Role,
    Job,
    Analyst,
    Issue,
    Rule,
    Configuration,
    Report
)

# Version
__version__ = "1.0.0"

# Library metadata
__author__ = "WFM Team"
__description__ = "Shared utilities for WFM microservices"
__license__ = "MIT"

# Export all public APIs
__all__ = [
    # Configuration
    "settings",
    "DatabaseSettings", 
    "SecuritySettings",
    "LoggingSettings",
    "ServiceSettings",
    
    # Authentication
    "TokenManager",
    "TokenData",
    "TokenResponse", 
    "token_manager",
    "get_current_user",
    "get_current_user_optional",
    "require_roles",
    "require_tenant_access",
    "get_password_hash",
    "verify_password",
    "create_access_token",
    
    # Logging and Monitoring
    "get_logger",
    "setup_logging",
    "get_correlation_id",
    "set_correlation_id", 
    "generate_correlation_id",
    "metrics_collector",
    "monitor_performance",
    "PerformanceMonitor",
    
    # Distributed Tracing
    "Tracer",
    "TraceContext",
    "Span",
    "SpanContext", 
    "SpanKind",
    "TracingHTTPClient",
    "tracer",
    "get_trace_id",
    "set_trace_id",
    "get_span_id",
    "set_span_id",
    "get_parent_span_id",
    "set_parent_span_id",
    "trace_operation",
    
    # Database
    "get_database",
    "get_redis_client",
    
    # Models
    "BaseModel",
    "User",
    "Role", 
    "Job",
    "Analyst",
    "Issue",
    "Rule",
    "Configuration",
    "Report",
    
    # Version
    "__version__"
] 