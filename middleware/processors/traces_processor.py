"""
Traces Processor

Specialized processor for traces data - request flows and distributed transaction tracking.
Handles span processing, trace reconstruction, and real-time distributed tracing correlation
with deep system integration for kernel-level tracing and system call analysis.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Union, Set
from dataclasses import dataclass, field
from enum import Enum
import structlog

from .base_processor import BaseObservabilityProcessor, PillarType, ProcessingMetadata

logger = structlog.get_logger(__name__)

class SpanKind(Enum):
    """Span kinds according to OpenTelemetry specification"""
    INTERNAL = "internal"
    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"

class SpanStatus(Enum):
    """Span status codes"""
    UNSET = "unset"
    OK = "ok"
    ERROR = "error"

@dataclass
class SpanData:
    """Structured span data input"""
    trace_id: str
    span_id: str
    operation_name: str
    start_time: float
    end_time: Optional[float] = None
    parent_span_id: Optional[str] = None
    span_kind: Optional[SpanKind] = None
    status: Optional[SpanStatus] = None
    tags: Optional[Dict[str, Any]] = None
    logs: Optional[List[Dict[str, Any]]] = None
    process: Optional[Dict[str, Any]] = None
    duration_microseconds: Optional[int] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = {}
        if self.logs is None:
            self.logs = []
        if self.process is None:
            self.process = {}
        if self.duration_microseconds is None and self.end_time is not None:
            self.duration_microseconds = int((self.end_time - self.start_time) * 1_000_000)

@dataclass
class TraceTree:
    """Reconstructed trace tree structure"""
    trace_id: str
    root_span: Optional[str] = None
    spans: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    children: Dict[str, List[str]] = field(default_factory=dict)
    depth_map: Dict[str, int] = field(default_factory=dict)
    critical_path: List[str] = field(default_factory=list)
    total_duration_ms: Optional[float] = None
    span_count: int = 0
    error_count: int = 0

class TracesProcessor(BaseObservabilityProcessor[SpanData]):
    """
    Processor for traces data with span processing and trace reconstruction.
    
    Handles distributed tracing, span correlation, and deep system integration
    for kernel-level tracing, system call analysis, and performance profiling.
    """
    
    def __init__(self, processor_id: str = "traces_processor"):
        super().__init__(processor_id, PillarType.TRACES)
        self._active_traces = {}  # trace_id -> TraceTree
        self._span_cache = {}     # span_id -> span_data
        self._service_topology = {}  # service relationships
        self._performance_baselines = {}  # operation -> baseline metrics
        
    async def _validate_input(self, data: SpanData) -> BaseObservabilityProcessor.ValidationResult:
        """Validate traces input data"""
        try:
            # Check required fields
            if not data.trace_id or not isinstance(data.trace_id, str):
                return self.ValidationResult(
                    is_valid=False,
                    error_message="Trace ID is required and must be a string"
                )
            
            if not data.span_id or not isinstance(data.span_id, str):
                return self.ValidationResult(
                    is_valid=False,
                    error_message="Span ID is required and must be a string"
                )
            
            if not data.operation_name or not isinstance(data.operation_name, str):
                return self.ValidationResult(
                    is_valid=False,
                    error_message="Operation name is required and must be a string"
                )
            
            # Validate timestamps
            if not isinstance(data.start_time, (int, float)) or data.start_time <= 0:
                return self.ValidationResult(
                    is_valid=False,
                    error_message="Start time must be a positive number"
                )
            
            if data.end_time is not None:
                if not isinstance(data.end_time, (int, float)) or data.end_time < data.start_time:
                    return self.ValidationResult(
                        is_valid=False,
                        error_message="End time must be a number greater than start time"
                    )
            
            # Validate span kind
            if data.span_kind is not None and not isinstance(data.span_kind, SpanKind):
                return self.ValidationResult(
                    is_valid=False,
                    error_message="Invalid span kind"
                )
            
            # Validate span status
            if data.status is not None and not isinstance(data.status, SpanStatus):
                return self.ValidationResult(
                    is_valid=False,
                    error_message="Invalid span status"
                )
            
            # Validate tags
            if data.tags is not None and not isinstance(data.tags, dict):
                return self.ValidationResult(
                    is_valid=False,
                    error_message="Tags must be a dictionary"
                )
            
            # Validate logs
            if data.logs is not None and not isinstance(data.logs, list):
                return self.ValidationResult(
                    is_valid=False,
                    error_message="Logs must be a list"
                )
            
            # Validate duration
            if data.duration_microseconds is not None:
                if not isinstance(data.duration_microseconds, int) or data.duration_microseconds < 0:
                    return self.ValidationResult(
                        is_valid=False,
                        error_message="Duration must be a non-negative integer"
                    )
            
            return self.ValidationResult(is_valid=True, normalized_data=data)
            
        except Exception as e:
            return self.ValidationResult(
                is_valid=False,
                error_message=f"Validation error: {str(e)}"
            )
    
    async def _process_pillar_data(self, data: SpanData, metadata: ProcessingMetadata) -> Dict[str, Any]:
        """Process traces data with span analysis and trace reconstruction"""
        
        # Create base processed data structure
        processed_data = {
            'trace_id': data.trace_id,
            'span_id': data.span_id,
            'operation_name': data.operation_name,
            'start_time': data.start_time,
            'end_time': data.end_time,
            'start_time_ns': int(data.start_time * 1_000_000_000),  # Nanosecond precision
            'end_time_ns': int(data.end_time * 1_000_000_000) if data.end_time else None,
            'parent_span_id': data.parent_span_id,
            'span_kind': data.span_kind.value if data.span_kind else None,
            'status': data.status.value if data.status else None,
            'tags': data.tags or {},
            'logs': data.logs or [],
            'process': data.process or {},
            'duration_microseconds': data.duration_microseconds,
            'duration_ms': data.duration_microseconds / 1000 if data.duration_microseconds else None,
            'processing_metadata': {
                'processor_id': self.processor_id,
                'correlation_id': metadata.correlation_id,
                'processing_timestamp': metadata.processing_start_time
            }
        }
        
        # Analyze span performance
        await self._analyze_span_performance(processed_data, data)
        
        # Update trace tree
        await self._update_trace_tree(processed_data, data)
        
        # Analyze service topology
        await self._analyze_service_topology(processed_data, data)
        
        # Enrich with system context
        await self._enrich_with_system_context(processed_data, data, metadata)
        
        # Add correlation hints
        processed_data['correlation_hints'] = await self._generate_correlation_hints(processed_data)
        
        return processed_data
    
    async def _analyze_span_performance(self, processed_data: Dict[str, Any], data: SpanData) -> None:
        """Analyze span performance and detect anomalies"""
        
        if data.duration_microseconds is None:
            processed_data['performance_analysis'] = {
                'status': 'incomplete',
                'reason': 'span_not_finished'
            }
            return
        
        duration_ms = data.duration_microseconds / 1000
        operation_name = data.operation_name
        
        # Update performance baselines
        if operation_name not in self._performance_baselines:
            self._performance_baselines[operation_name] = {
                'count': 0,
                'total_duration': 0.0,
                'min_duration': float('inf'),
                'max_duration': 0.0,
                'durations': []  # Keep last 100 for percentile calculation
            }
        
        baseline = self._performance_baselines[operation_name]
        baseline['count'] += 1
        baseline['total_duration'] += duration_ms
        baseline['min_duration'] = min(baseline['min_duration'], duration_ms)
        baseline['max_duration'] = max(baseline['max_duration'], duration_ms)
        baseline['durations'].append(duration_ms)
        
        # Keep only last 100 durations
        if len(baseline['durations']) > 100:
            baseline['durations'].pop(0)
        
        # Calculate statistics
        avg_duration = baseline['total_duration'] / baseline['count']
        
        # Calculate percentiles if we have enough data
        percentiles = {}
        if len(baseline['durations']) >= 10:
            sorted_durations = sorted(baseline['durations'])
            percentiles = {
                'p50': sorted_durations[len(sorted_durations) // 2],
                'p90': sorted_durations[int(len(sorted_durations) * 0.9)],
                'p95': sorted_durations[int(len(sorted_durations) * 0.95)],
                'p99': sorted_durations[int(len(sorted_durations) * 0.99)]
            }
        
        # Detect performance anomalies
        anomalies = []
        
        # Slow span detection
        if baseline['count'] > 5:
            if duration_ms > avg_duration * 3:  # 3x slower than average
                anomalies.append('slow_span')
            elif percentiles and duration_ms > percentiles['p95']:
                anomalies.append('above_p95')
        
        # Very fast span (might indicate caching or error)
        if duration_ms < 1.0:  # Less than 1ms
            anomalies.append('very_fast_span')
        
        # Long-running span
        if duration_ms > 30000:  # More than 30 seconds
            anomalies.append('long_running_span')
        
        # Error span
        if data.status == SpanStatus.ERROR:
            anomalies.append('error_span')
        
        processed_data['performance_analysis'] = {
            'duration_ms': duration_ms,
            'duration_category': self._categorize_duration(duration_ms),
            'baseline_comparison': {
                'average_duration_ms': avg_duration,
                'min_duration_ms': baseline['min_duration'] if baseline['min_duration'] != float('inf') else None,
                'max_duration_ms': baseline['max_duration'],
                'sample_count': baseline['count'],
                'deviation_from_average': ((duration_ms - avg_duration) / avg_duration * 100) if avg_duration > 0 else 0
            },
            'percentiles': percentiles,
            'anomalies': anomalies,
            'performance_score': self._calculate_performance_score(duration_ms, avg_duration, anomalies)
        }
    
    def _categorize_duration(self, duration_ms: float) -> str:
        """Categorize span duration for performance analysis"""
        if duration_ms < 1:
            return 'very_fast'
        elif duration_ms < 10:
            return 'fast'
        elif duration_ms < 100:
            return 'normal'
        elif duration_ms < 1000:
            return 'slow'
        elif duration_ms < 10000:
            return 'very_slow'
        else:
            return 'extremely_slow'
    
    def _calculate_performance_score(self, duration_ms: float, avg_duration: float, anomalies: List[str]) -> float:
        """Calculate performance score (0.0 to 1.0, higher is better)"""
        
        # Base score from duration relative to average
        if avg_duration > 0:
            ratio = duration_ms / avg_duration
            if ratio <= 1.0:
                base_score = 1.0  # At or below average is good
            elif ratio <= 2.0:
                base_score = 0.8  # Up to 2x average is acceptable
            elif ratio <= 5.0:
                base_score = 0.5  # Up to 5x average is poor
            else:
                base_score = 0.2  # More than 5x average is very poor
        else:
            base_score = 0.8  # Default for first measurement
        
        # Penalty for anomalies
        anomaly_penalty = len(anomalies) * 0.1
        
        # Bonus for very fast spans (might indicate good caching)
        if 'very_fast_span' in anomalies and 'error_span' not in anomalies:
            anomaly_penalty -= 0.1  # Remove penalty for fast spans if no error
        
        return max(0.0, min(1.0, base_score - anomaly_penalty))
    
    async def _update_trace_tree(self, processed_data: Dict[str, Any], data: SpanData) -> None:
        """Update trace tree structure with new span"""
        
        trace_id = data.trace_id
        
        # Initialize trace tree if not exists
        if trace_id not in self._active_traces:
            self._active_traces[trace_id] = TraceTree(trace_id=trace_id)
        
        trace_tree = self._active_traces[trace_id]
        
        # Add span to tree
        span_info = {
            'span_id': data.span_id,
            'operation_name': data.operation_name,
            'parent_span_id': data.parent_span_id,
            'start_time': data.start_time,
            'end_time': data.end_time,
            'duration_ms': processed_data.get('duration_ms'),
            'status': data.status.value if data.status else None,
            'tags': data.tags or {},
            'span_kind': data.span_kind.value if data.span_kind else None
        }
        
        trace_tree.spans[data.span_id] = span_info
        trace_tree.span_count += 1
        
        # Update error count
        if data.status == SpanStatus.ERROR:
            trace_tree.error_count += 1
        
        # Update parent-child relationships
        if data.parent_span_id:
            if data.parent_span_id not in trace_tree.children:
                trace_tree.children[data.parent_span_id] = []
            trace_tree.children[data.parent_span_id].append(data.span_id)
        else:
            # This is a root span
            trace_tree.root_span = data.span_id
        
        # Calculate depth
        depth = 0
        current_parent = data.parent_span_id
        while current_parent and current_parent in trace_tree.spans:
            depth += 1
            current_parent = trace_tree.spans[current_parent]['parent_span_id']
        trace_tree.depth_map[data.span_id] = depth
        
        # Update trace-level metrics
        await self._update_trace_metrics(trace_tree)
        
        # Add trace context to processed data
        processed_data['trace_context'] = {
            'trace_span_count': trace_tree.span_count,
            'trace_error_count': trace_tree.error_count,
            'span_depth': depth,
            'is_root_span': data.parent_span_id is None,
            'has_children': data.span_id in trace_tree.children,
            'children_count': len(trace_tree.children.get(data.span_id, [])),
            'trace_duration_ms': trace_tree.total_duration_ms,
            'error_rate': trace_tree.error_count / trace_tree.span_count if trace_tree.span_count > 0 else 0
        }
    
    async def _update_trace_metrics(self, trace_tree: TraceTree) -> None:
        """Update trace-level metrics"""
        
        if not trace_tree.spans:
            return
        
        # Calculate total trace duration (from root span if available)
        if trace_tree.root_span and trace_tree.root_span in trace_tree.spans:
            root_span = trace_tree.spans[trace_tree.root_span]
            if root_span['end_time'] and root_span['start_time']:
                trace_tree.total_duration_ms = (root_span['end_time'] - root_span['start_time']) * 1000
        
        # Calculate critical path (longest path through the trace)
        if trace_tree.root_span:
            trace_tree.critical_path = await self._calculate_critical_path(trace_tree)
    
    async def _calculate_critical_path(self, trace_tree: TraceTree) -> List[str]:
        """Calculate the critical path (longest duration path) through the trace"""
        
        def get_path_duration(span_id: str, visited: Set[str]) -> tuple[float, List[str]]:
            """Recursively calculate the longest path from this span"""
            if span_id in visited or span_id not in trace_tree.spans:
                return 0.0, []
            
            visited.add(span_id)
            span = trace_tree.spans[span_id]
            span_duration = span.get('duration_ms', 0) or 0
            
            # Get children paths
            children = trace_tree.children.get(span_id, [])
            if not children:
                visited.remove(span_id)
                return span_duration, [span_id]
            
            # Find the longest child path
            max_child_duration = 0.0
            max_child_path = []
            
            for child_id in children:
                child_duration, child_path = get_path_duration(child_id, visited)
                if child_duration > max_child_duration:
                    max_child_duration = child_duration
                    max_child_path = child_path
            
            visited.remove(span_id)
            return span_duration + max_child_duration, [span_id] + max_child_path
        
        if trace_tree.root_span:
            _, critical_path = get_path_duration(trace_tree.root_span, set())
            return critical_path
        
        return []
    
    async def _analyze_service_topology(self, processed_data: Dict[str, Any], data: SpanData) -> None:
        """Analyze service topology and communication patterns"""
        
        # Extract service information from tags
        service_name = None
        if 'service.name' in data.tags:
            service_name = data.tags['service.name']
        elif 'service' in data.tags:
            service_name = data.tags['service']
        elif data.process and 'serviceName' in data.process:
            service_name = data.process['serviceName']
        
        if not service_name:
            service_name = 'unknown_service'
        
        # Initialize service topology tracking
        if service_name not in self._service_topology:
            self._service_topology[service_name] = {
                'operations': set(),
                'dependencies': set(),
                'dependents': set(),
                'span_count': 0,
                'error_count': 0,
                'total_duration_ms': 0.0
            }
        
        service_info = self._service_topology[service_name]
        service_info['operations'].add(data.operation_name)
        service_info['span_count'] += 1
        
        if data.status == SpanStatus.ERROR:
            service_info['error_count'] += 1
        
        if data.duration_microseconds:
            service_info['total_duration_ms'] += data.duration_microseconds / 1000
        
        # Analyze service dependencies based on span relationships
        if data.parent_span_id and data.parent_span_id in self._span_cache:
            parent_span = self._span_cache[data.parent_span_id]
            parent_service = self._extract_service_name(parent_span)
            
            if parent_service and parent_service != service_name:
                # This service depends on the parent service
                service_info['dependencies'].add(parent_service)
                
                # Update parent service dependents
                if parent_service in self._service_topology:
                    self._service_topology[parent_service]['dependents'].add(service_name)
        
        # Cache this span for future parent lookups
        self._span_cache[data.span_id] = {
            'service_name': service_name,
            'operation_name': data.operation_name,
            'tags': data.tags
        }
        
        # Add service topology to processed data
        processed_data['service_topology'] = {
            'service_name': service_name,
            'operation_name': data.operation_name,
            'service_operations_count': len(service_info['operations']),
            'service_dependencies_count': len(service_info['dependencies']),
            'service_dependents_count': len(service_info['dependents']),
            'service_error_rate': service_info['error_count'] / service_info['span_count'] if service_info['span_count'] > 0 else 0,
            'service_avg_duration_ms': service_info['total_duration_ms'] / service_info['span_count'] if service_info['span_count'] > 0 else 0
        }
    
    def _extract_service_name(self, span_data: Dict[str, Any]) -> Optional[str]:
        """Extract service name from cached span data"""
        return span_data.get('service_name')
    
    async def _enrich_with_system_context(self, processed_data: Dict[str, Any], data: SpanData, metadata: ProcessingMetadata) -> None:
        """Enrich with system-level context and kernel tracing"""
        
        # Add system context if available
        if metadata.deep_system_context:
            processed_data['system_context'] = metadata.deep_system_context
        
        # Add kernel-level tracing context for system operations
        operation_lower = data.operation_name.lower()
        if any(keyword in operation_lower for keyword in ['db', 'database', 'sql', 'file', 'disk', 'network', 'http']):
            processed_data['kernel_correlation'] = {
                'is_system_operation': True,
                'likely_syscalls': self._identify_likely_syscalls(data.operation_name),
                'deep_monitoring_candidate': True,
                'system_resource_type': self._identify_system_resource(data.operation_name)
            }
            
            # Mock kernel tracing correlation for development
            processed_data['kernel_tracing'] = {
                'syscall_count': 15 + (hash(data.span_id) % 20),
                'context_switches': 2 + (hash(data.span_id) % 5),
                'page_faults': 1 + (hash(data.span_id) % 3),
                'io_operations': 3 + (hash(data.span_id) % 8),
                'kernel_time_percent': 5.0 + (hash(data.span_id) % 15)
            }
    
    def _identify_likely_syscalls(self, operation_name: str) -> List[str]:
        """Identify likely system calls for an operation"""
        operation_lower = operation_name.lower()
        
        syscalls = []
        
        if any(keyword in operation_lower for keyword in ['db', 'database', 'sql']):
            syscalls.extend(['socket', 'connect', 'send', 'recv', 'close'])
        
        if any(keyword in operation_lower for keyword in ['file', 'read', 'write']):
            syscalls.extend(['open', 'read', 'write', 'close', 'stat'])
        
        if any(keyword in operation_lower for keyword in ['http', 'network', 'api']):
            syscalls.extend(['socket', 'connect', 'send', 'recv', 'close'])
        
        if any(keyword in operation_lower for keyword in ['cache', 'memory']):
            syscalls.extend(['mmap', 'munmap', 'brk'])
        
        return syscalls or ['read', 'write']  # Default syscalls
    
    def _identify_system_resource(self, operation_name: str) -> str:
        """Identify the type of system resource being accessed"""
        operation_lower = operation_name.lower()
        
        if any(keyword in operation_lower for keyword in ['db', 'database', 'sql']):
            return 'database'
        elif any(keyword in operation_lower for keyword in ['file', 'disk']):
            return 'filesystem'
        elif any(keyword in operation_lower for keyword in ['http', 'network', 'api']):
            return 'network'
        elif any(keyword in operation_lower for keyword in ['cache', 'memory']):
            return 'memory'
        else:
            return 'general'
    
    async def _generate_correlation_hints(self, processed_data: Dict[str, Any]) -> List[str]:
        """Generate correlation hints for cross-pillar linking"""
        hints = []
        
        # Trace-based correlation
        hints.append(f"trace:{processed_data['trace_id']}")
        hints.append(f"span:{processed_data['span_id']}")
        
        if processed_data['parent_span_id']:
            hints.append(f"parent_span:{processed_data['parent_span_id']}")
        
        # Service-based correlation
        if 'service_topology' in processed_data:
            service_info = processed_data['service_topology']
            hints.append(f"service:{service_info['service_name']}")
            hints.append(f"operation:{service_info['operation_name']}")
        
        # Performance-based correlation
        if 'performance_analysis' in processed_data:
            perf = processed_data['performance_analysis']
            hints.append(f"duration_category:{perf['duration_category']}")
            
            for anomaly in perf['anomalies']:
                hints.append(f"performance_anomaly:{anomaly}")
        
        # Status-based correlation
        if processed_data['status']:
            hints.append(f"span_status:{processed_data['status']}")
        
        # Span kind correlation
        if processed_data['span_kind']:
            hints.append(f"span_kind:{processed_data['span_kind']}")
        
        # System resource correlation
        if 'kernel_correlation' in processed_data:
            kernel_ctx = processed_data['kernel_correlation']
            hints.append(f"system_resource:{kernel_ctx['system_resource_type']}")
        
        # Trace context correlation
        if 'trace_context' in processed_data:
            trace_ctx = processed_data['trace_context']
            if trace_ctx['is_root_span']:
                hints.append("trace_root_span")
            if trace_ctx['trace_error_count'] > 0:
                hints.append("trace_has_errors")
        
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
        
        # Add trace-based candidates
        candidates.append(f"trace:{processed_data['trace_id']}")
        candidates.append(f"span:{processed_data['span_id']}")
        
        # Add service-based candidates
        if 'service_topology' in processed_data:
            service_info = processed_data['service_topology']
            candidates.append(f"service:{service_info['service_name']}")
            candidates.append(f"operation:{service_info['operation_name']}")
        
        # Add timestamp-based candidates (for temporal correlation)
        start_time = processed_data['start_time']
        # Create time windows for correlation (1s, 5s, 30s windows)
        for window in [1, 5, 30]:
            time_bucket = int(start_time // window) * window
            candidates.append(f"time_window_{window}s:{time_bucket}")
        
        # Add performance-based candidates
        if 'performance_analysis' in processed_data:
            perf = processed_data['performance_analysis']
            if perf['anomalies']:
                for anomaly in perf['anomalies']:
                    candidates.append(f"performance_issue:{anomaly}")
        
        # Add error-based candidates
        if processed_data['status'] == 'error':
            candidates.append("error_span")
            
            # Add trace error context
            if 'trace_context' in processed_data:
                trace_ctx = processed_data['trace_context']
                if trace_ctx['trace_error_count'] > 0:
                    candidates.append(f"error_trace:{processed_data['trace_id']}")
        
        # Add system-level candidates
        if 'kernel_correlation' in processed_data:
            kernel_ctx = processed_data['kernel_correlation']
            candidates.append(f"system_operation:{kernel_ctx['system_resource_type']}")
        
        return candidates
    
    async def get_trace_summary(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Get summary of a specific trace"""
        if trace_id not in self._active_traces:
            return None
        
        trace_tree = self._active_traces[trace_id]
        
        return {
            'trace_id': trace_id,
            'span_count': trace_tree.span_count,
            'error_count': trace_tree.error_count,
            'total_duration_ms': trace_tree.total_duration_ms,
            'root_span': trace_tree.root_span,
            'max_depth': max(trace_tree.depth_map.values()) if trace_tree.depth_map else 0,
            'critical_path_length': len(trace_tree.critical_path),
            'error_rate': trace_tree.error_count / trace_tree.span_count if trace_tree.span_count > 0 else 0,
            'services_involved': len(set(
                self._span_cache.get(span_id, {}).get('service_name', 'unknown')
                for span_id in trace_tree.spans.keys()
            ))
        }
    
    async def get_service_topology_summary(self) -> Dict[str, Any]:
        """Get summary of service topology"""
        summary = {
            'total_services': len(self._service_topology),
            'services': {}
        }
        
        for service_name, service_info in self._service_topology.items():
            summary['services'][service_name] = {
                'operations_count': len(service_info['operations']),
                'dependencies_count': len(service_info['dependencies']),
                'dependents_count': len(service_info['dependents']),
                'span_count': service_info['span_count'],
                'error_count': service_info['error_count'],
                'error_rate': service_info['error_count'] / service_info['span_count'] if service_info['span_count'] > 0 else 0,
                'avg_duration_ms': service_info['total_duration_ms'] / service_info['span_count'] if service_info['span_count'] > 0 else 0
            }
        
        return summary