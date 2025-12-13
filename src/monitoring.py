"""Monitoring and metrics collection for Predictive Propositions Service."""
import logging
import time
from typing import Dict, Optional, Callable
from datetime import datetime
from functools import wraps
from dataclasses import dataclass, asdict
import json
from enum import Enum

try:
    from prometheus_client import Counter, Histogram, Gauge
    HAS_PROMETHEUS = True
except ImportError:
    HAS_PROMETHEUS = False

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Types of metrics to track."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


@dataclass
class RequestMetric:
    """Request metrics."""
    endpoint: str
    method: str
    status_code: int
    latency_ms: float
    timestamp: str
    user_id: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ModelMetric:
    """ML model metrics."""
    user_id: str
    propositions_count: int
    top_score: float
    model_version: str
    latency_ms: float
    served_by: str  # 'ml_ranker' or 'fallback'
    timestamp: str

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


class MetricsCollector:
    """Centralized metrics collection."""

    def __init__(self, service_name: str = "predictive-propositions-service"):
        """Initialize metrics collector.
        
        Args:
            service_name: Name of the service for metrics
        """
        self.service_name = service_name
        self.metrics_buffer = []
        self.max_buffer_size = 10000
        
        # Initialize Prometheus metrics if available
        if HAS_PROMETHEUS:
            self._init_prometheus_metrics()
        else:
            logger.warning("Prometheus client not installed. Using in-memory metrics only.")

    def _init_prometheus_metrics(self):
        """Initialize Prometheus metrics."""
        self.request_count = Counter(
            'service_requests_total',
            'Total number of requests',
            ['method', 'endpoint', 'status']
        )
        self.request_latency = Histogram(
            'service_request_latency_ms',
            'Request latency in milliseconds',
            ['method', 'endpoint'],
            buckets=[10, 50, 100, 150, 250, 500, 1000]
        )
        self.active_requests = Gauge(
            'service_active_requests',
            'Number of active requests'
        )
        self.ml_inference_latency = Histogram(
            'ml_inference_latency_ms',
            'ML model inference latency',
            buckets=[5, 10, 25, 50, 100, 150]
        )
        self.model_predictions = Counter(
            'ml_model_predictions_total',
            'Total model predictions',
            ['model_version', 'served_by']
        )
        self.cache_hits = Counter(
            'cache_hits_total',
            'Total cache hits'
        )
        self.cache_misses = Counter(
            'cache_misses_total',
            'Total cache misses'
        )

    def record_request(self, metric: RequestMetric) -> None:
        """Record request metric.
        
        Args:
            metric: RequestMetric instance
        """
        self.metrics_buffer.append(metric)
        
        # Manage buffer size
        if len(self.metrics_buffer) > self.max_buffer_size:
            # Keep only recent metrics
            self.metrics_buffer = self.metrics_buffer[-self.max_buffer_size:]
        
        if HAS_PROMETHEUS:
            self.request_count.labels(
                method=metric.method,
                endpoint=metric.endpoint,
                status=metric.status_code
            ).inc()
            self.request_latency.labels(
                method=metric.method,
                endpoint=metric.endpoint
            ).observe(metric.latency_ms)

    def record_model_inference(self, metric: ModelMetric) -> None:
        """Record ML model inference metric.
        
        Args:
            metric: ModelMetric instance
        """
        self.metrics_buffer.append(metric)
        
        if len(self.metrics_buffer) > self.max_buffer_size:
            self.metrics_buffer = self.metrics_buffer[-self.max_buffer_size:]
        
        if HAS_PROMETHEUS:
            self.ml_inference_latency.observe(metric.latency_ms)
            self.model_predictions.labels(
                model_version=metric.model_version,
                served_by=metric.served_by
            ).inc()

    def record_cache_hit(self) -> None:
        """Record cache hit."""
        if HAS_PROMETHEUS:
            self.cache_hits.inc()

    def record_cache_miss(self) -> None:
        """Record cache miss."""
        if HAS_PROMETHEUS:
            self.cache_misses.inc()

    def increment_active_requests(self) -> None:
        """Increment active request counter."""
        if HAS_PROMETHEUS:
            self.active_requests.inc()

    def decrement_active_requests(self) -> None:
        """Decrement active request counter."""
        if HAS_PROMETHEUS:
            self.active_requests.dec()

    def get_metrics(self, metric_type: Optional[str] = None, limit: int = 100) -> list:
        """Get collected metrics.
        
        Args:
            metric_type: Filter by metric type
            limit: Maximum number of metrics to return
        
        Returns:
            List of metrics
        """
        metrics = self.metrics_buffer[-limit:]
        if metric_type:
            metrics = [m for m in metrics if isinstance(m).__name__ == metric_type]
        return [m.to_dict() if hasattr(m, 'to_dict') else m for m in metrics]

    def get_summary(self) -> Dict:
        """Get metrics summary.
        
        Returns:
            Dictionary with metrics summary
        """
        request_metrics = [m for m in self.metrics_buffer if isinstance(m, RequestMetric)]
        model_metrics = [m for m in self.metrics_buffer if isinstance(m, ModelMetric)]
        
        summary = {
            "total_requests": len(request_metrics),
            "total_inferences": len(model_metrics),
            "buffer_size": len(self.metrics_buffer),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if request_metrics:
            latencies = [m.latency_ms for m in request_metrics]
            summary["request_latency_p50"] = sorted(latencies)[len(latencies)//2]
            summary["request_latency_p95"] = sorted(latencies)[int(len(latencies)*0.95)]
            summary["request_latency_p99"] = sorted(latencies)[int(len(latencies)*0.99)]
            summary["error_rate"] = len([m for m in request_metrics if m.error]) / len(request_metrics)
        
        if model_metrics:
            model_latencies = [m.latency_ms for m in model_metrics]
            summary["ml_latency_p50"] = sorted(model_latencies)[len(model_latencies)//2]
            summary["ml_latency_p95"] = sorted(model_latencies)[int(len(model_latencies)*0.95)]
            summary["ml_latency_avg"] = sum(model_latencies) / len(model_latencies)
        
        return summary


def track_endpoint(collector: MetricsCollector) -> Callable:
    """Decorator to track endpoint metrics.
    
    Args:
        collector: MetricsCollector instance
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            collector.increment_active_requests()
            
            try:
                result = await func(*args, **kwargs)
                status_code = 200
                error = None
                return result
            except Exception as e:
                status_code = 500
                error = str(e)
                logger.error(f"Error in {func.__name__}: {error}")
                raise
            finally:
                latency_ms = (time.time() - start_time) * 1000
                collector.decrement_active_requests()
                
                metric = RequestMetric(
                    endpoint=func.__name__,
                    method="POST",  # Default, can be overridden
                    status_code=status_code,
                    latency_ms=latency_ms,
                    timestamp=datetime.utcnow().isoformat(),
                    error=error
                )
                collector.record_request(metric)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            collector.increment_active_requests()
            
            try:
                result = func(*args, **kwargs)
                status_code = 200
                error = None
                return result
            except Exception as e:
                status_code = 500
                error = str(e)
                logger.error(f"Error in {func.__name__}: {error}")
                raise
            finally:
                latency_ms = (time.time() - start_time) * 1000
                collector.decrement_active_requests()
                
                metric = RequestMetric(
                    endpoint=func.__name__,
                    method="POST",
                    status_code=status_code,
                    latency_ms=latency_ms,
                    timestamp=datetime.utcnow().isoformat(),
                    error=error
                )
                collector.record_request(metric)
        
        # Return async or sync wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Global metrics collector instance
metrics_collector = MetricsCollector()
