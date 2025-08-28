"""
Unit tests for shared distributed tracing module.
"""
import pytest
import time
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from shared.tracing import (
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


class TestTraceContext:
    """Test cases for TraceContext class."""
    
    def test_trace_context_creation(self):
        """Test creating a trace context."""
        context = TraceContext()
        
        assert context.trace_id is not None
        assert context.span_id is not None
        assert context.parent_span_id is None
        assert isinstance(context.trace_id, str)
        assert isinstance(context.span_id, str)
    
    def test_trace_context_with_ids(self):
        """Test creating a trace context with specific IDs."""
        trace_id = "test-trace-123"
        span_id = "test-span-456"
        context = TraceContext(trace_id=trace_id, span_id=span_id)
        
        assert context.trace_id == trace_id
        assert context.span_id == span_id
        assert context.parent_span_id is None
    
    def test_create_child_context(self):
        """Test creating a child trace context."""
        parent = TraceContext(trace_id="parent-trace", span_id="parent-span")
        child = parent.create_child_context()
        
        assert child.trace_id == parent.trace_id
        assert child.span_id != parent.span_id
        assert child.parent_span_id == parent.span_id
    
    def test_to_headers(self):
        """Test converting trace context to headers."""
        context = TraceContext(trace_id="test-trace", span_id="test-span")
        headers = context.to_headers()
        
        assert headers["X-Trace-ID"] == "test-trace"
        assert headers["X-Span-ID"] == "test-span"
        assert headers["X-Parent-Span-ID"] == ""
    
    def test_to_headers_with_parent(self):
        """Test converting trace context with parent to headers."""
        parent = TraceContext(trace_id="parent-trace", span_id="parent-span")
        child = parent.create_child_context()
        headers = child.to_headers()
        
        assert headers["X-Trace-ID"] == "parent-trace"
        assert headers["X-Span-ID"] == child.span_id
        assert headers["X-Parent-Span-ID"] == "parent-span"
    
    def test_from_headers(self):
        """Test creating trace context from headers."""
        headers = {
            "X-Trace-ID": "test-trace",
            "X-Span-ID": "test-span",
            "X-Parent-Span-ID": "parent-span"
        }
        context = TraceContext.from_headers(headers)
        
        assert context.trace_id == "test-trace"
        assert context.span_id == "test-span"
        assert context.parent_span_id == "parent-span"
    
    def test_from_headers_missing(self):
        """Test creating trace context from headers with missing values."""
        headers = {}
        context = TraceContext.from_headers(headers)
        
        assert context.trace_id is not None
        assert context.span_id is not None
        assert context.parent_span_id is None


class TestSpan:
    """Test cases for Span class."""
    
    def test_span_creation(self):
        """Test creating a span."""
        span = Span(
            trace_id="test-trace",
            span_id="test-span",
            parent_span_id="parent-span",
            name="test-operation",
            kind=SpanKind.INTERNAL,
            start_time=datetime.utcnow()  # Set start_time explicitly
        )
        
        assert span.trace_id == "test-trace"
        assert span.span_id == "test-span"
        assert span.parent_span_id == "parent-span"
        assert span.name == "test-operation"
        assert span.kind == SpanKind.INTERNAL
        assert span.start_time is not None
        assert span.end_time is None
        assert span.duration_ms is None
        assert span.attributes == {}
        assert span.events == []
        assert span.status == "OK"
        assert span.error_message is None
    
    def test_span_add_attribute(self):
        """Test adding attributes to a span."""
        span = Span(
            trace_id="test-trace",
            span_id="test-span",
            parent_span_id=None,
            name="test-operation",
            kind=SpanKind.INTERNAL,
            start_time=None
        )
        
        span.add_attribute("test_key", "test_value")
        span.add_attribute("numeric_key", 42)
        
        assert span.attributes["test_key"] == "test_value"
        assert span.attributes["numeric_key"] == 42
    
    def test_span_add_event(self):
        """Test adding events to a span."""
        span = Span(
            trace_id="test-trace",
            span_id="test-span",
            parent_span_id=None,
            name="test-operation",
            kind=SpanKind.INTERNAL,
            start_time=None
        )
        
        span.add_event("test_event", {"key": "value"})
        
        assert len(span.events) == 1
        assert span.events[0]["name"] == "test_event"
        assert span.events[0]["attributes"] == {"key": "value"}
        assert "timestamp" in span.events[0]
    
    def test_span_end_success(self):
        """Test ending a span successfully."""
        span = Span(
            trace_id="test-trace",
            span_id="test-span",
            parent_span_id=None,
            name="test-operation",
            kind=SpanKind.INTERNAL,
            start_time=datetime.utcnow()
        )
        
        time.sleep(0.01)  # Simulate some work
        span.end()
        
        assert span.end_time is not None
        assert span.duration_ms is not None
        assert span.duration_ms > 0
        assert span.status == "OK"
        assert span.error_message is None
    
    def test_span_end_with_error(self):
        """Test ending a span with an error."""
        span = Span(
            trace_id="test-trace",
            span_id="test-span",
            parent_span_id=None,
            name="test-operation",
            kind=SpanKind.INTERNAL,
            start_time=datetime.utcnow()
        )
        
        span.end(status="ERROR", error_message="Test error")
        
        assert span.end_time is not None
        assert span.duration_ms is not None
        assert span.status == "ERROR"
        assert span.error_message == "Test error"
    
    def test_span_to_dict(self):
        """Test converting span to dictionary."""
        span = Span(
            trace_id="test-trace",
            span_id="test-span",
            parent_span_id="parent-span",
            name="test-operation",
            kind=SpanKind.INTERNAL,
            start_time=datetime.utcnow()
        )
        
        span.add_attribute("test_attr", "test_value")
        span.end()
        
        span_dict = span.to_dict()
        
        assert span_dict["trace_id"] == "test-trace"
        assert span_dict["span_id"] == "test-span"
        assert span_dict["parent_span_id"] == "parent-span"
        assert span_dict["name"] == "test-operation"
        assert span_dict["kind"] == SpanKind.INTERNAL
        assert span_dict["attributes"]["test_attr"] == "test_value"
        assert span_dict["status"] == "OK"


class TestTracer:
    """Test cases for Tracer class."""
    
    @pytest.fixture
    def tracer_instance(self):
        """Create a tracer instance for testing."""
        return Tracer("test-service")
    
    def test_tracer_creation(self, tracer_instance):
        """Test creating a tracer."""
        assert tracer_instance.service_name == "test-service"
        assert tracer_instance.spans == []
    
    def test_start_span(self, tracer_instance):
        """Test starting a span."""
        with tracer_instance.start_span("test-operation") as span_context:
            assert span_context is not None
            assert hasattr(span_context, "add_attribute")
            assert hasattr(span_context, "add_event")
        
        # Check that span was recorded
        assert len(tracer_instance.spans) == 1
        span = tracer_instance.spans[0]
        assert span.name == "test-operation"
        assert span.kind == SpanKind.INTERNAL
    
    def test_start_span_with_attributes(self, tracer_instance):
        """Test starting a span with attributes."""
        attributes = {"service": "test", "operation": "test-op"}
        
        with tracer_instance.start_span("test-operation", attributes=attributes) as span_context:
            span_context.add_attribute("additional_attr", "value")
        
        # Check that span was recorded with attributes
        assert len(tracer_instance.spans) == 1
        span = tracer_instance.spans[0]
        assert span.attributes["service"] == "test"
        assert span.attributes["operation"] == "test-op"
        assert span.attributes["additional_attr"] == "value"
    
    def test_start_span_with_exception(self, tracer_instance):
        """Test starting a span that raises an exception."""
        with pytest.raises(ValueError):
            with tracer_instance.start_span("test-operation"):
                raise ValueError("Test error")
        
        # Check that span was recorded with error
        assert len(tracer_instance.spans) == 1
        span = tracer_instance.spans[0]
        assert span.status == "ERROR"
        assert span.error_message == "Test error"
    
    def test_get_trace(self, tracer_instance):
        """Test getting spans for a specific trace."""
        trace_id = "test-trace-123"
        
        # Create spans with same trace ID
        with tracer_instance.start_span("operation1") as span_context:
            span_context.span.trace_id = trace_id
        
        with tracer_instance.start_span("operation2") as span_context:
            span_context.span.trace_id = trace_id
        
        # Create span with different trace ID
        with tracer_instance.start_span("operation3") as span_context:
            span_context.span.trace_id = "different-trace"
        
        # Get spans for specific trace
        trace_spans = tracer_instance.get_trace(trace_id)
        
        assert len(trace_spans) == 2
        assert all(span.trace_id == trace_id for span in trace_spans)
        assert any(span.name == "operation1" for span in trace_spans)
        assert any(span.name == "operation2" for span in trace_spans)
    
    def test_export_traces(self, tracer_instance):
        """Test exporting traces."""
        # Create spans for different traces
        with tracer_instance.start_span("operation1") as span_context:
            span_context.span.trace_id = "trace1"
        
        with tracer_instance.start_span("operation2") as span_context:
            span_context.span.trace_id = "trace1"
        
        with tracer_instance.start_span("operation3") as span_context:
            span_context.span.trace_id = "trace2"
        
        # Export traces
        traces = tracer_instance.export_traces()
        
        assert len(traces) == 2
        assert any(len(trace) == 2 for trace in traces)  # trace1 has 2 spans
        assert any(len(trace) == 1 for trace in traces)  # trace2 has 1 span


class TestTracingFunctions:
    """Test cases for tracing utility functions."""
    
    def test_trace_id_management(self):
        """Test trace ID management functions."""
        # Clear any existing trace ID
        set_trace_id(None)
        
        # Initially no trace ID
        assert get_trace_id() is None
        
        # Set trace ID
        test_trace_id = "test-trace-123"
        set_trace_id(test_trace_id)
        assert get_trace_id() == test_trace_id
    
    def test_span_id_management(self):
        """Test span ID management functions."""
        # Clear any existing span ID
        set_span_id(None)
        
        # Initially no span ID
        assert get_span_id() is None
        
        # Set span ID
        test_span_id = "test-span-456"
        set_span_id(test_span_id)
        assert get_span_id() == test_span_id
    
    def test_parent_span_id_management(self):
        """Test parent span ID management functions."""
        # Clear any existing parent span ID
        set_parent_span_id(None)
        
        # Initially no parent span ID
        assert get_parent_span_id() is None
        
        # Set parent span ID
        test_parent_span_id = "test-parent-span-789"
        set_parent_span_id(test_parent_span_id)
        assert get_parent_span_id() == test_parent_span_id


class TestTraceOperationDecorator:
    """Test cases for trace_operation decorator."""
    
    def test_sync_function_tracing(self):
        """Test tracing a synchronous function."""
        # Clear existing spans
        tracer.spans = []
        
        @trace_operation("test_sync_function")
        def test_function():
            time.sleep(0.01)
            return "success"
        
        result = test_function()
        assert result == "success"
        
        # Check that span was created
        spans = tracer.spans
        assert len(spans) == 1
        assert spans[0].name == "test_sync_function"
        assert spans[0].attributes["function"] == "test_function"
    
    @pytest.mark.asyncio
    async def test_async_function_tracing(self):
        """Test tracing an asynchronous function."""
        # Clear existing spans
        tracer.spans = []
        
        @trace_operation("test_async_function")
        async def test_async_function():
            await asyncio.sleep(0.01)
            return "success"
        
        result = await test_async_function()
        assert result == "success"
        
        # Check that span was created
        spans = tracer.spans
        assert len(spans) == 1
        assert spans[0].name == "test_async_function"
        assert spans[0].attributes["function"] == "test_async_function"
    
    def test_function_with_exception_tracing(self):
        """Test tracing a function that raises an exception."""
        # Clear existing spans
        tracer.spans = []
        
        @trace_operation("test_error_function")
        def test_error_function():
            time.sleep(0.01)
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            test_error_function()
        
        # Check that span was created with error
        spans = tracer.spans
        assert len(spans) == 1
        assert spans[0].name == "test_error_function"
        assert spans[0].status == "ERROR"
        assert spans[0].error_message == "Test error"


class TestTracingHTTPClient:
    """Test cases for TracingHTTPClient."""
    
    @pytest.fixture
    def http_client(self):
        """Create a tracing HTTP client for testing."""
        return TracingHTTPClient(base_url="http://test.com")
    
    @pytest.mark.asyncio
    async def test_http_client_creation(self, http_client):
        """Test creating a tracing HTTP client."""
        assert http_client.base_url == "http://test.com"
        assert http_client.headers == {}
        assert http_client.client is not None
    
    @pytest.mark.asyncio
    async def test_http_request_tracing(self, http_client):
        """Test making an HTTP request with tracing."""
        # Mock the httpx client
        with patch.object(http_client, 'client') as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.content = b"test response"
            mock_client.request = AsyncMock(return_value=mock_response)
            
            # Set trace context
            set_trace_id("test-trace-123")
            set_span_id("test-span-456")
            
            response = await http_client.request("GET", "/test")
            
            # Check that request was made with tracing headers
            mock_client.request.assert_called_once()
            call_args = mock_client.request.call_args
            headers = call_args[1].get("headers", {})
            
            assert headers["X-Trace-ID"] == "test-trace-123"
            assert headers["X-Span-ID"] == "test-span-456"
            assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_http_request_without_trace_context(self, http_client):
        """Test making an HTTP request without trace context."""
        # Clear any existing trace context
        set_trace_id(None)
        set_span_id(None)
        set_parent_span_id(None)
        
        with patch.object(http_client, 'client') as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.content = b"test response"
            mock_client.request = AsyncMock(return_value=mock_response)
            
            response = await http_client.request("GET", "/test")
            
            # Check that request was made without tracing headers
            mock_client.request.assert_called_once()
            call_args = mock_client.request.call_args
            headers = call_args[1].get("headers", {})
            
            assert "X-Trace-ID" not in headers
            assert "X-Span-ID" not in headers
            assert response.status_code == 200


class TestTracingIntegration:
    """Integration tests for tracing functionality."""
    
    def test_full_trace_lifecycle(self):
        """Test complete trace lifecycle."""
        # Clear existing spans
        tracer.spans = []
        
        # Set trace context without parent span
        set_trace_id("integration-trace")
        set_span_id(None)
        set_parent_span_id(None)
        
        # Start spans
        with tracer.start_span("root_operation", SpanKind.SERVER) as root_span:
            root_span.add_attribute("service", "test-service")
            
            with tracer.start_span("child_operation", SpanKind.INTERNAL) as child_span:
                child_span.add_attribute("operation", "child")
                time.sleep(0.01)
            
            with tracer.start_span("another_child", SpanKind.INTERNAL) as another_span:
                another_span.add_attribute("operation", "another")
                time.sleep(0.01)
        
        # Check that all spans were recorded
        assert len(tracer.spans) == 3
        
        # Check trace structure
        trace_spans = tracer.get_trace("integration-trace")
        assert len(trace_spans) == 3
        
        # Check span relationships
        root_span = next(span for span in trace_spans if span.name == "root_operation")
        child_span = next(span for span in trace_spans if span.name == "child_operation")
        another_span = next(span for span in trace_spans if span.name == "another_child")
        
        assert root_span.parent_span_id is None
        assert child_span.parent_span_id == root_span.span_id
        # The another_child span should be a child of the child_operation span
        assert another_span.parent_span_id == child_span.span_id
    
    def test_trace_with_exceptions(self):
        """Test tracing with exceptions."""
        # Clear existing spans
        tracer.spans = []
        
        with pytest.raises(ValueError):
            with tracer.start_span("error_operation") as span:
                span.add_attribute("test_attr", "test_value")
                time.sleep(0.01)
                raise ValueError("Test error")
        
        # Check that span was recorded with error
        assert len(tracer.spans) == 1
        span = tracer.spans[0]
        assert span.name == "error_operation"
        assert span.status == "ERROR"
        assert span.error_message == "Test error"
        assert span.attributes["test_attr"] == "test_value"


# Import asyncio for async tests
import asyncio 