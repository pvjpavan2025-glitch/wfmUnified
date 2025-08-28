"""
Logging utilities for WFM microservices.
"""
import logging
import sys
import uuid
import time
from datetime import datetime
from typing import Optional, Dict, Any
from contextvars import ContextVar
import structlog
from structlog.stdlib import LoggerFactory
from shared.config import settings
import asyncio

# Context variable for correlation ID
correlation_id_var: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


def get_correlation_id() -> Optional[str]:
    """Get current correlation ID."""
    return correlation_id_var.get()


def set_correlation_id(correlation_id: str) -> None:
    """Set correlation ID for current context."""
    correlation_id_var.set(correlation_id)


def generate_correlation_id() -> str:
    """Generate a new correlation ID."""
    return str(uuid.uuid4())


class CorrelationIdProcessor:
    """Structlog processor to add correlation ID to log entries."""
    
    def __init__(self, correlation_id_var: ContextVar[Optional[str]]):
        self.correlation_id_var = correlation_id_var
    
    def __call__(self, logger, method_name, event_dict):
        correlation_id = self.correlation_id_var.get()
        if correlation_id:
            event_dict["correlation_id"] = correlation_id
        return event_dict


class RequestIdProcessor:
    """Structlog processor to add request ID to log entries."""
    
    def __call__(self, logger, method_name, event_dict):
        if "request_id" not in event_dict:
            event_dict["request_id"] = str(uuid.uuid4())
        return event_dict


class TimestampProcessor:
    """Structlog processor to add timestamp to log entries."""
    
    def __call__(self, logger, method_name, event_dict):
        event_dict["timestamp"] = datetime.utcnow().isoformat()
        return event_dict


class ServiceNameProcessor:
    """Structlog processor to add service name to log entries."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
    
    def __call__(self, logger, method_name, event_dict):
        event_dict["service"] = self.service_name
        return event_dict


def setup_logging(service_name: str = None) -> None:
    """Setup structured logging with correlation ID support."""
    if service_name is None:
        service_name = settings.service.service_name
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            TimestampProcessor(),
            ServiceNameProcessor(service_name),
            CorrelationIdProcessor(correlation_id_var),
            RequestIdProcessor(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.logging.log_level.upper()),
    )
    return structlog.get_logger(service_name)


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


class MetricsCollector:
    """Collects and reports metrics for monitoring."""
    
    def __init__(self):
        self.metrics = {}
        self.logger = get_logger(__name__)
    
    def increment_counter(self, name: str, value: int = 1, labels: Dict[str, str] = None):
        """Increment a counter metric."""
        if name not in self.metrics:
            self.metrics[name] = {"type": "counter", "value": 0, "labels": labels or {}}
        
        self.metrics[name]["value"] += value
        self.logger.info("metric_incremented", metric_name=name, value=value, labels=labels)
    
    def record_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a gauge metric."""
        self.metrics[name] = {"type": "gauge", "value": value, "labels": labels or {}}
        self.logger.info("metric_recorded", metric_name=name, value=value, labels=labels)
    
    def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a histogram metric."""
        if name not in self.metrics:
            self.metrics[name] = {"type": "histogram", "values": [], "labels": labels or {}}
        
        self.metrics[name]["values"].append(value)
        self.logger.info("histogram_recorded", metric_name=name, value=value, labels=labels)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics."""
        return self.metrics


# Global metrics collector
metrics_collector = MetricsCollector()


class PerformanceMonitor:
    """Monitors performance of operations."""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        self.logger = get_logger(__name__)
    
    def __enter__(self):
        self.start_time = time.time()
        self.logger.info("operation_started", operation=self.operation_name)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        metrics_collector.record_histogram(f"{self.operation_name}_duration", duration)
        
        if exc_type:
            self.logger.error(
                "operation_failed",
                operation=self.operation_name,
                duration=duration,
                error=str(exc_val)
            )
            metrics_collector.increment_counter(f"{self.operation_name}_errors")
        else:
            self.logger.info(
                "operation_completed",
                operation=self.operation_name,
                duration=duration
            )
            metrics_collector.increment_counter(f"{self.operation_name}_success")


def monitor_performance(operation_name: str):
    """Decorator to monitor performance of functions."""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            with PerformanceMonitor(operation_name):
                return await func(*args, **kwargs)
        
        def sync_wrapper(*args, **kwargs):
            with PerformanceMonitor(operation_name):
                return func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Initialize logging
setup_logging() 