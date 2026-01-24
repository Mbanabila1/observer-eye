"""
Metrics Processor

Specialized processor for metrics data - quantitative measurements and performance indicators.
Handles counter, gauge, histogram, and summary metric types with real-time aggregation
and correlation capabilities.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import structlog

from .base_processor import BaseObservabilityProcessor, PillarType, ProcessingMetadata

logger = structlog.get_logger(__name__)

class MetricType(Enum):
    """Types of metrics supported"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"
    TIMER = "timer"

@dataclass
class MetricData:
    """Structured metric data input"""
    name: str
    value: Union[float, int]
    metric_type: MetricType
    timestamp: Optional[float] = None
    labels: Optional[Dict[str, str]] = None
    unit: Optional[str] = None
    help_text: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.labels is None:
            self.labels = {}

class MetricsProcessor(BaseObservabilityProcessor[MetricData]):
    """
    Processor for metrics data with real-time aggregation and correlation.
    
    Handles various metric types and provides deep system integration
    for kernel-level performance metrics and hardware monitoring.
    """
    
    def __init__(self, processor_id: str = "metrics_processor"):
        super().__init__(processor_id, PillarType.METRICS)
        self._metric_aggregations = {}
        self._correlation_cache = {}
        
    async def _validate_input(self, data: MetricData) -> BaseObservabilityProcessor.ValidationResult:
        """Validate metrics input data"""
        try:
            # Check required fields
            if not data.name or not isinstance(data.name, str):
                return self.ValidationResult(
                    is_valid=False,
                    error_message="Metric name is required and must be a string"
                )
            
            if data.value is None:
                return self.ValidationResult(
                    is_valid=False,
                    error_message="Metric value is required"
                )
            
            # Validate numeric value
            if not isinstance(data.value, (int, float)):
                try:
                    data.value = float(data.value)
                except (ValueError, TypeError):
                    return self.ValidationResult(
                        is_valid=False,
                        error_message="Metric value must be numeric"
                    )
            
            # Validate metric type
            if not isinstance(data.metric_type, MetricType):
                return self.ValidationResult(
                    is_valid=False,
                    error_message="Invalid metric type"
                )
            
            # Validate timestamp
            if data.timestamp is not None:
                if not isinstance(data.timestamp, (int, float)) or data.timestamp <= 0:
                    return self.ValidationResult(
                        is_valid=False,
                        error_message="Timestamp must be a positive number"
                    )
            
            # Validate labels
            if data.labels is not None:
                if not isinstance(data.labels, dict):
                    return self.ValidationResult(
                        is_valid=False,
                        error_message="Labels must be a dictionary"
                    )
                
                # Ensure all label keys and values are strings
                for key, value in data.labels.items():
                    if not isinstance(key, str) or not isinstance(value, str):
                        return self.ValidationResult(
                            is_valid=False,
                            error_message="All label keys and values must be strings"
                        )
            
            return self.ValidationResult(is_valid=True, normalized_data=data)
            
        except Exception as e:
            return self.ValidationResult(
                is_valid=False,
                error_message=f"Validation error: {str(e)}"
            )
    
    async def _process_pillar_data(self, data: MetricData, metadata: ProcessingMetadata) -> Dict[str, Any]:
        """Process metrics data with aggregation and enrichment"""
        
        # Create base processed data structure
        processed_data = {
            'metric_name': data.name,
            'metric_value': data.value,
            'metric_type': data.metric_type.value,
            'timestamp': data.timestamp,
            'timestamp_ns': int(data.timestamp * 1_000_000_000),  # Nanosecond precision
            'labels': data.labels or {},
            'unit': data.unit,
            'help_text': data.help_text,
            'processing_metadata': {
                'processor_id': self.processor_id,
                'correlation_id': metadata.correlation_id,
                'processing_timestamp': metadata.processing_start_time
            }
        }
        
        # Add metric-specific processing
        await self._process_metric_type_specific(processed_data, data, metadata)
        
        # Perform real-time aggregation
        await self._perform_real_time_aggregation(processed_data, data)
        
        # Enrich with system context
        await self._enrich_with_system_metrics(processed_data, metadata)
        
        # Add correlation hints
        processed_data['correlation_hints'] = await self._generate_correlation_hints(processed_data)
        
        return processed_data
    
    async def _process_metric_type_specific(
        self, 
        processed_data: Dict[str, Any], 
        data: MetricData, 
        metadata: ProcessingMetadata
    ) -> None:
        """Apply metric type-specific processing"""
        
        if data.metric_type == MetricType.COUNTER:
            # Counters: calculate rate of change
            processed_data['metric_properties'] = {
                'is_monotonic': True,
                'rate_calculation_enabled': True,
                'aggregation_method': 'sum'
            }
            
            # Calculate rate if we have previous values
            rate = await self._calculate_counter_rate(data.name, data.value, data.timestamp)
            if rate is not None:
                processed_data['derived_metrics'] = {
                    'rate_per_second': rate
                }
        
        elif data.metric_type == MetricType.GAUGE:
            # Gauges: current value with trend analysis
            processed_data['metric_properties'] = {
                'is_monotonic': False,
                'trend_analysis_enabled': True,
                'aggregation_method': 'average'
            }
            
            # Calculate trend if we have historical data
            trend = await self._calculate_gauge_trend(data.name, data.value, data.timestamp)
            if trend is not None:
                processed_data['derived_metrics'] = {
                    'trend_direction': trend['direction'],
                    'trend_magnitude': trend['magnitude']
                }
        
        elif data.metric_type == MetricType.HISTOGRAM:
            # Histograms: distribution analysis
            processed_data['metric_properties'] = {
                'is_distribution': True,
                'percentile_calculation_enabled': True,
                'aggregation_method': 'histogram_merge'
            }
            
            # For histogram values, we expect bucket data
            if isinstance(data.value, dict) and 'buckets' in data.value:
                processed_data['histogram_data'] = data.value
                processed_data['derived_metrics'] = await self._calculate_histogram_percentiles(data.value)
        
        elif data.metric_type == MetricType.TIMER:
            # Timers: latency and performance analysis
            processed_data['metric_properties'] = {
                'is_timing': True,
                'latency_analysis_enabled': True,
                'aggregation_method': 'statistical'
            }
            
            # Convert to standard time units and calculate performance metrics
            processed_data['timing_data'] = {
                'value_ms': data.value,
                'value_ns': int(data.value * 1_000_000),
                'performance_category': self._categorize_latency(data.value)
            }
    
    async def _perform_real_time_aggregation(self, processed_data: Dict[str, Any], data: MetricData) -> None:
        """Perform real-time metric aggregation"""
        
        metric_key = f"{data.name}:{hash(str(sorted((data.labels or {}).items())))}"
        
        if metric_key not in self._metric_aggregations:
            self._metric_aggregations[metric_key] = {
                'count': 0,
                'sum': 0.0,
                'min': float('inf'),
                'max': float('-inf'),
                'last_value': None,
                'last_timestamp': None,
                'values_buffer': []  # Keep last 100 values for trend analysis
            }
        
        agg = self._metric_aggregations[metric_key]
        agg['count'] += 1
        agg['sum'] += data.value
        agg['min'] = min(agg['min'], data.value)
        agg['max'] = max(agg['max'], data.value)
        agg['last_value'] = data.value
        agg['last_timestamp'] = data.timestamp
        
        # Maintain rolling buffer
        agg['values_buffer'].append({
            'value': data.value,
            'timestamp': data.timestamp
        })
        if len(agg['values_buffer']) > 100:
            agg['values_buffer'].pop(0)
        
        # Add aggregation data to processed result
        processed_data['aggregation_data'] = {
            'count': agg['count'],
            'average': agg['sum'] / agg['count'],
            'min': agg['min'],
            'max': agg['max'],
            'range': agg['max'] - agg['min'],
            'last_value': agg['last_value']
        }
    
    async def _enrich_with_system_metrics(self, processed_data: Dict[str, Any], metadata: ProcessingMetadata) -> None:
        """Enrich with system-level metrics and deep monitoring context"""
        
        # Add system context if available
        if metadata.deep_system_context:
            processed_data['system_context'] = metadata.deep_system_context
        
        # Add kernel-level metrics if this is a system metric
        metric_name = processed_data['metric_name']
        if any(keyword in metric_name.lower() for keyword in ['cpu', 'memory', 'disk', 'network', 'kernel']):
            processed_data['kernel_correlation'] = {
                'is_system_metric': True,
                'kernel_subsystem': self._identify_kernel_subsystem(metric_name),
                'deep_monitoring_candidate': True
            }
            
            # Mock kernel metrics for development
            processed_data['kernel_metrics'] = {
                'syscalls_per_second': 1250 + (hash(metric_name) % 500),
                'context_switches': 890 + (hash(metric_name) % 200),
                'interrupts_per_second': 450 + (hash(metric_name) % 100),
                'kernel_time_percent': 5.2 + (hash(metric_name) % 10) / 10
            }
    
    def _identify_kernel_subsystem(self, metric_name: str) -> str:
        """Identify the kernel subsystem for system metrics"""
        metric_lower = metric_name.lower()
        
        if any(keyword in metric_lower for keyword in ['cpu', 'processor', 'core']):
            return 'scheduler'
        elif any(keyword in metric_lower for keyword in ['memory', 'ram', 'swap']):
            return 'memory_management'
        elif any(keyword in metric_lower for keyword in ['disk', 'io', 'storage']):
            return 'block_io'
        elif any(keyword in metric_lower for keyword in ['network', 'net', 'tcp', 'udp']):
            return 'network_stack'
        else:
            return 'general'
    
    def _categorize_latency(self, latency_ms: float) -> str:
        """Categorize latency performance"""
        if latency_ms < 1:
            return 'excellent'
        elif latency_ms < 10:
            return 'good'
        elif latency_ms < 100:
            return 'acceptable'
        elif latency_ms < 1000:
            return 'poor'
        else:
            return 'critical'
    
    async def _calculate_counter_rate(self, metric_name: str, current_value: float, timestamp: float) -> Optional[float]:
        """Calculate rate of change for counter metrics"""
        cache_key = f"counter_rate:{metric_name}"
        
        if cache_key in self._correlation_cache:
            prev_data = self._correlation_cache[cache_key]
            time_diff = timestamp - prev_data['timestamp']
            value_diff = current_value - prev_data['value']
            
            if time_diff > 0:
                rate = value_diff / time_diff
                self._correlation_cache[cache_key] = {'value': current_value, 'timestamp': timestamp}
                return rate
        
        # Store current value for next calculation
        self._correlation_cache[cache_key] = {'value': current_value, 'timestamp': timestamp}
        return None
    
    async def _calculate_gauge_trend(self, metric_name: str, current_value: float, timestamp: float) -> Optional[Dict[str, Any]]:
        """Calculate trend for gauge metrics"""
        cache_key = f"gauge_trend:{metric_name}"
        
        if cache_key not in self._correlation_cache:
            self._correlation_cache[cache_key] = []
        
        trend_data = self._correlation_cache[cache_key]
        trend_data.append({'value': current_value, 'timestamp': timestamp})
        
        # Keep only last 10 values for trend calculation
        if len(trend_data) > 10:
            trend_data.pop(0)
        
        if len(trend_data) >= 3:
            # Simple linear trend calculation
            values = [point['value'] for point in trend_data]
            n = len(values)
            
            # Calculate slope using least squares
            sum_x = sum(range(n))
            sum_y = sum(values)
            sum_xy = sum(i * values[i] for i in range(n))
            sum_x2 = sum(i * i for i in range(n))
            
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            
            return {
                'direction': 'increasing' if slope > 0.01 else 'decreasing' if slope < -0.01 else 'stable',
                'magnitude': abs(slope),
                'slope': slope
            }
        
        return None
    
    async def _calculate_histogram_percentiles(self, histogram_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate percentiles from histogram data"""
        # Simplified percentile calculation for histogram buckets
        buckets = histogram_data.get('buckets', {})
        
        if not buckets:
            return {}
        
        # Mock percentile calculation - in production this would use proper histogram analysis
        total_count = sum(buckets.values())
        if total_count == 0:
            return {}
        
        return {
            'p50': 50.0,  # Median
            'p90': 90.0,  # 90th percentile
            'p95': 95.0,  # 95th percentile
            'p99': 99.0   # 99th percentile
        }
    
    async def _generate_correlation_hints(self, processed_data: Dict[str, Any]) -> List[str]:
        """Generate correlation hints for cross-pillar linking"""
        hints = []
        
        # Service-based correlation
        labels = processed_data.get('labels', {})
        if 'service' in labels:
            hints.append(f"service:{labels['service']}")
        if 'service_name' in labels:
            hints.append(f"service:{labels['service_name']}")
        
        # Environment correlation
        if 'environment' in labels or 'env' in labels:
            env = labels.get('environment', labels.get('env'))
            hints.append(f"environment:{env}")
        
        # Instance correlation
        if 'instance' in labels:
            hints.append(f"instance:{labels['instance']}")
        
        # Metric type correlation
        metric_type = processed_data['metric_type']
        hints.append(f"metric_type:{metric_type}")
        
        # Performance category correlation (for timing metrics)
        if 'timing_data' in processed_data:
            category = processed_data['timing_data']['performance_category']
            hints.append(f"performance:{category}")
        
        # System subsystem correlation
        if 'kernel_correlation' in processed_data:
            subsystem = processed_data['kernel_correlation']['kernel_subsystem']
            hints.append(f"kernel_subsystem:{subsystem}")
        
        return hints
    
    async def _extract_correlation_candidates(
        self, 
        processed_data: Dict[str, Any], 
        metadata: ProcessingMetadata
    ) -> List[str]:
        """Extract correlation candidates for cross-pillar linking"""
        candidates = []
        
        # Add correlation ID
        candidates.append(metadata.correlation_id)
        
        # Add service-based candidates
        labels = processed_data.get('labels', {})
        if 'service' in labels:
            candidates.append(f"service:{labels['service']}")
        
        # Add timestamp-based candidates (for temporal correlation)
        timestamp = processed_data['timestamp']
        # Create time windows for correlation (1s, 5s, 30s windows)
        for window in [1, 5, 30]:
            time_bucket = int(timestamp // window) * window
            candidates.append(f"time_window_{window}s:{time_bucket}")
        
        # Add metric-specific candidates
        metric_name = processed_data['metric_name']
        candidates.append(f"metric:{metric_name}")
        
        # Add performance-based candidates
        if 'timing_data' in processed_data:
            category = processed_data['timing_data']['performance_category']
            candidates.append(f"performance_issue:{category}")
        
        # Add system-level candidates
        if 'kernel_correlation' in processed_data:
            candidates.append(f"system_metric:{processed_data['kernel_correlation']['kernel_subsystem']}")
        
        return candidates
    
    async def get_aggregation_summary(self) -> Dict[str, Any]:
        """Get summary of current metric aggregations"""
        summary = {
            'total_metrics': len(self._metric_aggregations),
            'metrics': {}
        }
        
        for metric_key, agg_data in self._metric_aggregations.items():
            summary['metrics'][metric_key] = {
                'count': agg_data['count'],
                'average': agg_data['sum'] / agg_data['count'] if agg_data['count'] > 0 else 0,
                'min': agg_data['min'] if agg_data['min'] != float('inf') else None,
                'max': agg_data['max'] if agg_data['max'] != float('-inf') else None,
                'last_value': agg_data['last_value'],
                'last_timestamp': agg_data['last_timestamp']
            }
        
        return summary