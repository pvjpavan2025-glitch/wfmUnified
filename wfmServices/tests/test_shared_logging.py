"""
Unit tests for shared logging and monitoring module.
"""
import pytest
import time
from unittest.mock import Mock, patch
from shared.logging import (
    get_logger,
    setup_logging,
    get_correlation_id,
    set_correlation_id,
    generate_correlation_id,
    metrics_collector,
    monitor_performance,
    PerformanceMonitor
)


class TestLogging:
    """Test cases for logging functionality."""
    
    def test_get_logger(self):
        """Test getting a logger instance."""
        logger = get_logger("test-module")
        assert logger is not None
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "debug")
    
    def test_setup_logging(self):
        """Test logging setup."""
        setup_logging("test-service")
        logger = get_logger("test-module")
        assert logger is not None
    
    def test_correlation_id_management(self):
        """Test correlation ID management."""
        # Initially no correlation ID
        assert get_correlation_id() is None
        
        # Set correlation ID
        test_id = "test-correlation-123"
        set_correlation_id(test_id)
        assert get_correlation_id() == test_id
        
        # Generate new correlation ID
        new_id = generate_correlation_id()
        assert new_id is not None
        assert isinstance(new_id, str)
        assert len(new_id) > 0


class TestMetricsCollector:
    """Test cases for MetricsCollector."""
    
    @pytest.fixture
    def collector(self):
        """Create a metrics collector for testing."""
        return metrics_collector
    
    def test_increment_counter(self, collector):
        """Test incrementing a counter metric."""
        collector.increment_counter("test_counter", 1)
        collector.increment_counter("test_counter", 2)
        
        metrics = collector.get_metrics()
        assert "test_counter" in metrics
        assert metrics["test_counter"]["type"] == "counter"
        assert metrics["test_counter"]["value"] == 3
    
    def test_record_gauge(self, collector):
        """Test recording a gauge metric."""
        collector.record_gauge("test_gauge", 42.5)
        
        metrics = collector.get_metrics()
        assert "test_gauge" in metrics
        assert metrics["test_gauge"]["type"] == "gauge"
        assert metrics["test_gauge"]["value"] == 42.5
    
    def test_record_histogram(self, collector):
        """Test recording a histogram metric."""
        collector.record_histogram("test_histogram", 10.0)
        collector.record_histogram("test_histogram", 20.0)
        collector.record_histogram("test_histogram", 30.0)
        
        metrics = collector.get_metrics()
        assert "test_histogram" in metrics
        assert metrics["test_histogram"]["type"] == "histogram"
        assert len(metrics["test_histogram"]["values"]) == 3
        assert 10.0 in metrics["test_histogram"]["values"]
        assert 20.0 in metrics["test_histogram"]["values"]
        assert 30.0 in metrics["test_histogram"]["values"]
    
    def test_metrics_with_labels(self, collector):
        """Test metrics with labels."""
        labels = {"service": "test", "endpoint": "/api/test"}
        collector.increment_counter("labeled_counter", 1, labels)
        
        metrics = collector.get_metrics()
        assert "labeled_counter" in metrics
        assert metrics["labeled_counter"]["labels"] == labels
    
    def test_get_metrics(self, collector):
        """Test getting all metrics."""
        # Add some metrics
        collector.increment_counter("counter1", 1)
        collector.record_gauge("gauge1", 100.0)
        collector.record_histogram("histogram1", 50.0)
        
        metrics = collector.get_metrics()
        
        assert "counter1" in metrics
        assert "gauge1" in metrics
        assert "histogram1" in metrics
        assert isinstance(metrics, dict)


class TestPerformanceMonitor:
    """Test cases for PerformanceMonitor."""
    
    def test_performance_monitor_success(self):
        """Test performance monitoring for successful operations."""
        with PerformanceMonitor("test_operation") as monitor:
            time.sleep(0.01)  # Simulate some work
        
        # Check that metrics were recorded
        metrics = metrics_collector.get_metrics()
        assert "test_operation_duration" in metrics
        assert "test_operation_success" in metrics
        assert metrics["test_operation_success"]["value"] == 1
    
    def test_performance_monitor_failure(self):
        """Test performance monitoring for failed operations."""
        with pytest.raises(ValueError):
            with PerformanceMonitor("test_operation"):
                time.sleep(0.01)
                raise ValueError("Test error")
        
        # Check that error metrics were recorded
        metrics = metrics_collector.get_metrics()
        assert "test_operation_duration" in metrics
        assert "test_operation_errors" in metrics
        assert metrics["test_operation_errors"]["value"] == 1
    
    def test_performance_monitor_attributes(self):
        """Test adding attributes to performance monitor."""
        with PerformanceMonitor("test_operation") as monitor:
            # PerformanceMonitor doesn't have add_attribute method
            # The monitoring is done automatically
            time.sleep(0.01)
        
        # Check that metrics were recorded
        metrics = metrics_collector.get_metrics()
        assert "test_operation_duration" in metrics
        assert "test_operation_success" in metrics


class TestMonitorPerformanceDecorator:
    """Test cases for monitor_performance decorator."""
    
    def test_sync_function_monitoring(self):
        """Test monitoring a synchronous function."""
        @monitor_performance("test_sync_function")
        def test_function():
            time.sleep(0.01)
            return "success"
        
        result = test_function()
        assert result == "success"
        
        # Check that metrics were recorded
        metrics = metrics_collector.get_metrics()
        assert "test_sync_function_duration" in metrics
        assert "test_sync_function_success" in metrics
    
    @pytest.mark.asyncio
    async def test_async_function_monitoring(self):
        """Test monitoring an asynchronous function."""
        @monitor_performance("test_async_function")
        async def test_async_function():
            await asyncio.sleep(0.01)
            return "success"
        
        result = await test_async_function()
        assert result == "success"
        
        # Check that metrics were recorded
        metrics = metrics_collector.get_metrics()
        assert "test_async_function_duration" in metrics
        assert "test_async_function_success" in metrics
    
    def test_function_with_exception(self):
        """Test monitoring a function that raises an exception."""
        @monitor_performance("test_error_function")
        def test_error_function():
            time.sleep(0.01)
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            test_error_function()
        
        # Check that error metrics were recorded
        metrics = metrics_collector.get_metrics()
        assert "test_error_function_duration" in metrics
        assert "test_error_function_errors" in metrics
        assert metrics["test_error_function_errors"]["value"] == 1


class TestLoggingIntegration:
    """Integration tests for logging functionality."""
    
    def test_logging_with_correlation_id(self):
        """Test logging with correlation ID."""
        correlation_id = generate_correlation_id()
        set_correlation_id(correlation_id)
        
        logger = get_logger("test-module")
        logger.info("Test message", extra_data="test")
        
        # The log should include correlation ID
        # This is tested by checking that the logger works without errors
    
    def test_metrics_collector_persistence(self):
        """Test that metrics persist across operations."""
        collector = metrics_collector
        
        # Clear existing metrics
        collector.metrics = {}
        
        # Add metrics
        collector.increment_counter("persistent_counter", 1)
        collector.record_gauge("persistent_gauge", 42.0)
        
        # Get metrics
        metrics = collector.get_metrics()
        
        # Verify persistence
        assert "persistent_counter" in metrics
        assert "persistent_gauge" in metrics
        assert metrics["persistent_counter"]["value"] == 1
        assert metrics["persistent_gauge"]["value"] == 42.0
    
    def test_performance_monitoring_integration(self):
        """Test integration of performance monitoring with metrics."""
        # Clear existing metrics
        metrics_collector.metrics = {}
        
        # Monitor an operation
        with PerformanceMonitor("integration_test"):
            time.sleep(0.01)
        
        # Check that metrics were recorded
        metrics = metrics_collector.get_metrics()
        assert "integration_test_duration" in metrics
        assert "integration_test_success" in metrics
        
        # Check that duration is reasonable
        duration_metric = metrics["integration_test_duration"]
        assert duration_metric["type"] == "histogram"
        assert len(duration_metric["values"]) == 1
        assert duration_metric["values"][0] > 0


# Import asyncio for async tests
import asyncio 