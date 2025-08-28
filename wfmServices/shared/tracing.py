"""
Distributed tracing utilities for WFM microservices.
"""
import uuid
import time
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from contextvars import ContextVar
from dataclasses import dataclass, asdict
from enum import Enum
import httpx
from shared.logging import get_logger, set_correlation_id, get_correlation_id

logger = get_logger(__name__)

# Context variables for tracing
trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)
span_id_var: ContextVar[Optional[str]] = ContextVar("span_id", default=None)
parent_span_id_var: ContextVar[Optional[str]] = ContextVar("parent_span_id", default=None)


class SpanKind(Enum):
    """Span kinds for different types of operations."""
    CLIENT = "client"
    SERVER = "server"
    INTERNAL = "internal"
    PRODUCER = "producer"
    CONSUMER = "consumer"


@dataclass
class Span:
    """Represents a span in the trace."""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    name: str
    kind: SpanKind
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    attributes: Dict[str, Any] = None
    events: List[Dict[str, Any]] = None
    status: str = "OK"
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}
        if self.events is None:
            self.events = []
    
    def add_attribute(self, key: str, value: Any):
        """Add an attribute to the span."""
        self.attributes[key] = value
    
    def add_event(self, name: str, attributes: Dict[str, Any] = None):
        """Add an event to the span."""
        event = {
            "name": name,
            "timestamp": datetime.utcnow().isoformat(),
            "attributes": attributes or {}
        }
        self.events.append(event)
    
    def end(self, status: str = "OK", error_message: Optional[str] = None):
        """End the span."""
        self.end_time = datetime.utcnow()
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        self.status = status
        self.error_message = error_message
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary."""
        return asdict(self)


class TraceContext:
    """Manages trace context for distributed tracing."""
    
    def __init__(self, trace_id: Optional[str] = None, span_id: Optional[str] = None):
        self.trace_id = trace_id or str(uuid.uuid4())
        self.span_id = span_id or str(uuid.uuid4())
        self.parent_span_id = None
    
    def create_child_context(self) -> 'TraceContext':
        """Create a child trace context."""
        child = TraceContext(trace_id=self.trace_id, span_id=str(uuid.uuid4()))
        child.parent_span_id = self.span_id
        return child
    
    def to_headers(self) -> Dict[str, str]:
        """Convert trace context to HTTP headers."""
        return {
            "X-Trace-ID": self.trace_id,
            "X-Span-ID": self.span_id,
            "X-Parent-Span-ID": self.parent_span_id or "",
        }
    
    @classmethod
    def from_headers(cls, headers: Dict[str, str]) -> 'TraceContext':
        """Create trace context from HTTP headers."""
        trace_id = headers.get("X-Trace-ID") or str(uuid.uuid4())
        span_id = headers.get("X-Span-ID") or str(uuid.uuid4())
        parent_span_id = headers.get("X-Parent-Span-ID")
        
        context = cls(trace_id=trace_id, span_id=span_id)
        context.parent_span_id = parent_span_id
        return context


class Tracer:
    """Main tracer class for distributed tracing."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.spans: List[Span] = []
        self.logger = get_logger(__name__)
    
    def start_span(self, name: str, kind: SpanKind = SpanKind.INTERNAL, 
                   attributes: Dict[str, Any] = None) -> 'SpanContext':
        """Start a new span."""
        trace_id = get_trace_id() or str(uuid.uuid4())
        span_id = str(uuid.uuid4())
        parent_span_id = get_span_id()
        
        span = Span(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            name=name,
            kind=kind,
            start_time=datetime.utcnow(),
            attributes=attributes or {}
        )
        
        # Set context variables
        set_trace_id(trace_id)
        set_span_id(span_id)
        set_parent_span_id(parent_span_id)
        
        # Set correlation ID for logging
        set_correlation_id(trace_id)
        
        self.logger.info(
            "span_started",
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            name=name,
            kind=kind.value,
            service=self.service_name
        )
        
        return SpanContext(self, span)
    
    def record_span(self, span: Span):
        """Record a completed span."""
        self.spans.append(span)
        self.logger.info(
            "span_completed",
            trace_id=span.trace_id,
            span_id=span.span_id,
            name=span.name,
            duration_ms=span.duration_ms,
            status=span.status,
            service=self.service_name
        )
    
    def get_trace(self, trace_id: str) -> List[Span]:
        """Get all spans for a trace ID."""
        return [span for span in self.spans if span.trace_id == trace_id]
    
    def export_traces(self) -> List[Dict[str, Any]]:
        """Export all traces for external systems."""
        traces = {}
        for span in self.spans:
            if span.trace_id not in traces:
                traces[span.trace_id] = []
            traces[span.trace_id].append(span.to_dict())
        
        return list(traces.values())


class SpanContext:
    """Context manager for spans."""
    
    def __init__(self, tracer: Tracer, span: Span):
        self.tracer = tracer
        self.span = span
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.span.end(status="ERROR", error_message=str(exc_val))
            self.span.add_attribute("error", True)
            self.span.add_attribute("error.type", exc_type.__name__)
            self.span.add_attribute("error.message", str(exc_val))
        else:
            self.span.end()
        
        self.tracer.record_span(self.span)
    
    def add_attribute(self, key: str, value: Any):
        """Add an attribute to the span."""
        self.span.add_attribute(key, value)
    
    def add_event(self, name: str, attributes: Dict[str, Any] = None):
        """Add an event to the span."""
        self.span.add_event(name, attributes)


# Global tracer instance
tracer = Tracer("wfm-service")


def get_trace_id() -> Optional[str]:
    """Get current trace ID."""
    return trace_id_var.get()


def set_trace_id(trace_id: str) -> None:
    """Set trace ID for current context."""
    trace_id_var.set(trace_id)


def get_span_id() -> Optional[str]:
    """Get current span ID."""
    return span_id_var.get()


def set_span_id(span_id: str) -> None:
    """Set span ID for current context."""
    span_id_var.set(span_id)


def get_parent_span_id() -> Optional[str]:
    """Get current parent span ID."""
    return parent_span_id_var.get()


def set_parent_span_id(parent_span_id: str) -> None:
    """Set parent span ID for current context."""
    parent_span_id_var.set(parent_span_id)


def trace_operation(name: str, kind: SpanKind = SpanKind.INTERNAL):
    """Decorator to trace operations."""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            with tracer.start_span(name, kind) as span:
                span.add_attribute("function", func.__name__)
                span.add_attribute("module", func.__module__)
                return await func(*args, **kwargs)
        
        def sync_wrapper(*args, **kwargs):
            with tracer.start_span(name, kind) as span:
                span.add_attribute("function", func.__name__)
                span.add_attribute("module", func.__module__)
                return func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class TracingHTTPClient:
    """HTTP client with tracing support."""
    
    def __init__(self, base_url: str = "", headers: Dict[str, str] = None):
        self.base_url = base_url
        self.headers = headers or {}
        self.client = httpx.AsyncClient()
        self.logger = get_logger(__name__)
    
    async def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Make an HTTP request with tracing."""
        full_url = f"{self.base_url}{url}"
        
        # Get current trace context
        trace_id = get_trace_id()
        span_id = get_span_id()
        
        # Add tracing headers
        headers = kwargs.get("headers", {})
        if trace_id:
            headers["X-Trace-ID"] = trace_id
        if span_id:
            headers["X-Span-ID"] = span_id
        
        kwargs["headers"] = headers
        
        with tracer.start_span(f"HTTP {method}", SpanKind.CLIENT) as span:
            span.add_attribute("http.method", method)
            span.add_attribute("http.url", full_url)
            span.add_attribute("http.request_id", str(uuid.uuid4()))
            
            try:
                response = await self.client.request(method, full_url, **kwargs)
                span.add_attribute("http.status_code", response.status_code)
                span.add_attribute("http.response_size", len(response.content))
                return response
            except Exception as e:
                span.add_attribute("error", True)
                span.add_attribute("error.message", str(e))
                raise


# Import asyncio for async function detection
import asyncio 