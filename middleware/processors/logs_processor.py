"""
Logs Processor

Specialized processor for logs data - textual records and structured logging data.
Handles log parsing, structured data extraction, and real-time log correlation
with deep system integration for kernel logs and system call tracing.
"""

import asyncio
import time
import re
import json
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import structlog

from .base_processor import BaseObservabilityProcessor, PillarType, ProcessingMetadata

logger = structlog.get_logger(__name__)

class LogLevel(Enum):
    """Log levels supported"""
    TRACE = "trace"
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    FATAL = "fatal"

class LogFormat(Enum):
    """Log format types"""
    PLAIN_TEXT = "plain_text"
    JSON = "json"
    STRUCTURED = "structured"
    SYSLOG = "syslog"
    APACHE_COMBINED = "apache_combined"
    NGINX = "nginx"
    KERNEL = "kernel"

@dataclass
class LogData:
    """Structured log data input"""
    message: str
    level: LogLevel
    timestamp: Optional[float] = None
    logger_name: Optional[str] = None
    source_file: Optional[str] = None
    line_number: Optional[int] = None
    function_name: Optional[str] = None
    thread_id: Optional[str] = None
    process_id: Optional[int] = None
    structured_data: Optional[Dict[str, Any]] = None
    raw_log: Optional[str] = None
    format_type: Optional[LogFormat] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.structured_data is None:
            self.structured_data = {}

class LogsProcessor(BaseObservabilityProcessor[LogData]):
    """
    Processor for logs data with parsing, extraction, and correlation.
    
    Handles various log formats, structured data extraction, and deep system
    integration for kernel logs, system call tracing, and security log analysis.
    """
    
    def __init__(self, processor_id: str = "logs_processor"):
        super().__init__(processor_id, PillarType.LOGS)
        self._log_patterns = {}
        self._error_sequences = {}
        self._structured_extractors = self._initialize_extractors()
        
    def _initialize_extractors(self) -> Dict[str, re.Pattern]:
        """Initialize regex patterns for structured data extraction"""
        return {
            'ip_address': re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
            'timestamp_iso': re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})'),
            'http_status': re.compile(r'\b[1-5]\d{2}\b'),
            'duration_ms': re.compile(r'\b\d+(?:\.\d+)?ms\b'),
            'user_id': re.compile(r'user[_-]?id[:\s=]+([a-zA-Z0-9-]+)', re.IGNORECASE),
            'session_id': re.compile(r'session[_-]?id[:\s=]+([a-zA-Z0-9-]+)', re.IGNORECASE),
            'trace_id': re.compile(r'trace[_-]?id[:\s=]+([a-fA-F0-9-]+)', re.IGNORECASE),
            'span_id': re.compile(r'span[_-]?id[:\s=]+([a-fA-F0-9-]+)', re.IGNORECASE),
            'error_code': re.compile(r'error[_-]?code[:\s=]+([A-Z0-9_]+)', re.IGNORECASE),
            'sql_query': re.compile(r'(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP)\s+.*?(?:;|$)', re.IGNORECASE | re.DOTALL),
            'file_path': re.compile(r'(?:/[^/\s]+)+/?'),
            'memory_size': re.compile(r'\b\d+(?:\.\d+)?\s*(?:B|KB|MB|GB|TB)\b', re.IGNORECASE),
            'pid': re.compile(r'\bpid[:\s=]+(\d+)', re.IGNORECASE),
            'cpu_percent': re.compile(r'\b\d+(?:\.\d+)?%\s*cpu', re.IGNORECASE)
        }
    
    async def _validate_input(self, data: LogData) -> BaseObservabilityProcessor.ValidationResult:
        """Validate logs input data"""
        try:
            # Check required fields
            if not data.message or not isinstance(data.message, str):
                return self.ValidationResult(
                    is_valid=False,
                    error_message="Log message is required and must be a string"
                )
            
            # Validate log level
            if not isinstance(data.level, LogLevel):
                return self.ValidationResult(
                    is_valid=False,
                    error_message="Invalid log level"
                )
            
            # Validate timestamp
            if data.timestamp is not None:
                if not isinstance(data.timestamp, (int, float)) or data.timestamp <= 0:
                    return self.ValidationResult(
                        is_valid=False,
                        error_message="Timestamp must be a positive number"
                    )
            
            # Validate numeric fields
            if data.line_number is not None and (not isinstance(data.line_number, int) or data.line_number < 0):
                return self.ValidationResult(
                    is_valid=False,
                    error_message="Line number must be a non-negative integer"
                )
            
            if data.process_id is not None and (not isinstance(data.process_id, int) or data.process_id < 0):
                return self.ValidationResult(
                    is_valid=False,
                    error_message="Process ID must be a non-negative integer"
                )
            
            # Validate structured data
            if data.structured_data is not None and not isinstance(data.structured_data, dict):
                return self.ValidationResult(
                    is_valid=False,
                    error_message="Structured data must be a dictionary"
                )
            
            # Validate format type
            if data.format_type is not None and not isinstance(data.format_type, LogFormat):
                return self.ValidationResult(
                    is_valid=False,
                    error_message="Invalid log format type"
                )
            
            return self.ValidationResult(is_valid=True, normalized_data=data)
            
        except Exception as e:
            return self.ValidationResult(
                is_valid=False,
                error_message=f"Validation error: {str(e)}"
            )
    
    async def _process_pillar_data(self, data: LogData, metadata: ProcessingMetadata) -> Dict[str, Any]:
        """Process logs data with parsing and enrichment"""
        
        # Create base processed data structure
        processed_data = {
            'message': data.message,
            'level': data.level.value,
            'timestamp': data.timestamp,
            'timestamp_ns': int(data.timestamp * 1_000_000_000),  # Nanosecond precision
            'logger_name': data.logger_name,
            'source_file': data.source_file,
            'line_number': data.line_number,
            'function_name': data.function_name,
            'thread_id': data.thread_id,
            'process_id': data.process_id,
            'structured_data': data.structured_data or {},
            'raw_log': data.raw_log or data.message,
            'format_type': data.format_type.value if data.format_type else None,
            'processing_metadata': {
                'processor_id': self.processor_id,
                'correlation_id': metadata.correlation_id,
                'processing_timestamp': metadata.processing_start_time
            }
        }
        
        # Parse and extract structured data from message
        await self._extract_structured_data(processed_data, data)
        
        # Detect log format if not specified
        if not data.format_type:
            processed_data['format_type'] = await self._detect_log_format(data)
        
        # Analyze log content and classify
        await self._analyze_log_content(processed_data, data)
        
        # Detect error patterns and sequences
        await self._detect_error_patterns(processed_data, data)
        
        # Enrich with system context
        await self._enrich_with_system_context(processed_data, data, metadata)
        
        # Add correlation hints
        processed_data['correlation_hints'] = await self._generate_correlation_hints(processed_data)
        
        return processed_data
    
    async def _extract_structured_data(self, processed_data: Dict[str, Any], data: LogData) -> None:
        """Extract structured data from log message using regex patterns"""
        
        extracted_data = {}
        message = data.message
        
        # Extract common patterns
        for pattern_name, pattern in self._structured_extractors.items():
            matches = pattern.findall(message)
            if matches:
                if pattern_name in ['user_id', 'session_id', 'trace_id', 'span_id', 'error_code']:
                    # Single capture group patterns
                    extracted_data[pattern_name] = matches[0] if len(matches) == 1 else matches
                else:
                    # Full match patterns
                    extracted_data[pattern_name] = matches[0] if len(matches) == 1 else matches
        
        # Try to parse JSON if message looks like JSON
        if message.strip().startswith('{') and message.strip().endswith('}'):
            try:
                json_data = json.loads(message)
                extracted_data['json_payload'] = json_data
                
                # Extract common JSON fields
                for field in ['user_id', 'session_id', 'trace_id', 'span_id', 'request_id', 'correlation_id']:
                    if field in json_data:
                        extracted_data[field] = json_data[field]
                        
            except json.JSONDecodeError:
                pass
        
        # Merge with existing structured data
        processed_data['structured_data'].update(extracted_data)
        processed_data['extracted_fields'] = list(extracted_data.keys())
    
    async def _detect_log_format(self, data: LogData) -> str:
        """Detect log format based on message structure"""
        
        message = data.message
        
        # JSON format detection
        if message.strip().startswith('{') and message.strip().endswith('}'):
            try:
                json.loads(message)
                return LogFormat.JSON.value
            except json.JSONDecodeError:
                pass
        
        # Syslog format detection (RFC 3164/5424)
        if re.match(r'^<\d+>', message) or re.match(r'^\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}', message):
            return LogFormat.SYSLOG.value
        
        # Apache Combined Log Format
        if re.match(r'^[\d\.]+ \S+ \S+ \[.*?\] ".*?" \d+ \d+ ".*?" ".*?"', message):
            return LogFormat.APACHE_COMBINED.value
        
        # Nginx format
        if ' - - [' in message and '] "' in message and '" ' in message:
            return LogFormat.NGINX.value
        
        # Kernel log format
        if re.match(r'^\[\s*\d+\.\d+\]', message) or 'kernel:' in message.lower():
            return LogFormat.KERNEL.value
        
        # Structured format (key=value pairs)
        if re.search(r'\w+=\w+', message) and message.count('=') >= 2:
            return LogFormat.STRUCTURED.value
        
        # Default to plain text
        return LogFormat.PLAIN_TEXT.value
    
    async def _analyze_log_content(self, processed_data: Dict[str, Any], data: LogData) -> None:
        """Analyze log content and classify the log entry"""
        
        message_lower = data.message.lower()
        
        # Content classification
        content_categories = []
        
        # Error/Exception analysis
        if data.level in [LogLevel.ERROR, LogLevel.FATAL] or any(keyword in message_lower 
                for keyword in ['error', 'exception', 'failed', 'failure', 'crash', 'panic']):
            content_categories.append('error')
            
            # Specific error types
            if any(keyword in message_lower for keyword in ['timeout', 'timed out']):
                content_categories.append('timeout_error')
            elif any(keyword in message_lower for keyword in ['connection', 'network']):
                content_categories.append('network_error')
            elif any(keyword in message_lower for keyword in ['database', 'sql', 'db']):
                content_categories.append('database_error')
            elif any(keyword in message_lower for keyword in ['memory', 'oom', 'out of memory']):
                content_categories.append('memory_error')
            elif any(keyword in message_lower for keyword in ['permission', 'access', 'forbidden']):
                content_categories.append('permission_error')
        
        # Performance analysis
        if any(keyword in message_lower for keyword in ['slow', 'performance', 'latency', 'response time']):
            content_categories.append('performance')
        
        # Security analysis
        if any(keyword in message_lower for keyword in ['auth', 'login', 'logout', 'security', 'breach', 'attack']):
            content_categories.append('security')
        
        # System analysis
        if any(keyword in message_lower for keyword in ['system', 'kernel', 'hardware', 'cpu', 'memory', 'disk']):
            content_categories.append('system')
        
        # Business logic analysis
        if any(keyword in message_lower for keyword in ['user', 'order', 'payment', 'transaction', 'business']):
            content_categories.append('business')
        
        # Calculate content complexity
        complexity_score = 0
        complexity_score += len(data.message) / 1000  # Length factor
        complexity_score += len(processed_data['extracted_fields']) * 0.1  # Structured data factor
        complexity_score += 0.5 if 'json_payload' in processed_data['structured_data'] else 0  # JSON factor
        
        processed_data['content_analysis'] = {
            'categories': content_categories,
            'complexity_score': min(10.0, complexity_score),
            'has_structured_data': len(processed_data['extracted_fields']) > 0,
            'message_length': len(data.message),
            'word_count': len(data.message.split()),
            'contains_stack_trace': 'at ' in data.message and ('Exception' in data.message or 'Error' in data.message)
        }
    
    async def _detect_error_patterns(self, processed_data: Dict[str, Any], data: LogData) -> None:
        """Detect error patterns and sequences for correlation"""
        
        if data.level not in [LogLevel.ERROR, LogLevel.FATAL]:
            return
        
        # Create error signature
        error_signature = self._create_error_signature(data.message)
        
        # Initialize error tracking
        if error_signature not in self._error_sequences:
            self._error_sequences[error_signature] = {
                'count': 0,
                'first_seen': data.timestamp,
                'last_seen': data.timestamp,
                'frequency_per_hour': 0.0,
                'recent_occurrences': [],
                'associated_files': set(),
                'associated_functions': set()
            }
        
        error_seq = self._error_sequences[error_signature]
        error_seq['count'] += 1
        error_seq['last_seen'] = data.timestamp
        
        # Track associated context
        if data.source_file:
            error_seq['associated_files'].add(data.source_file)
        if data.function_name:
            error_seq['associated_functions'].add(data.function_name)
        
        # Calculate frequency
        time_span_hours = (data.timestamp - error_seq['first_seen']) / 3600
        if time_span_hours > 0:
            error_seq['frequency_per_hour'] = error_seq['count'] / time_span_hours
        
        # Maintain recent occurrences
        error_seq['recent_occurrences'].append({
            'timestamp': data.timestamp,
            'source_file': data.source_file,
            'line_number': data.line_number,
            'message_snippet': data.message[:200]
        })
        
        # Keep only last 20 occurrences
        if len(error_seq['recent_occurrences']) > 20:
            error_seq['recent_occurrences'].pop(0)
        
        # Detect error patterns
        pattern_detected = False
        pattern_type = None
        
        # High frequency errors
        if error_seq['frequency_per_hour'] > 60:  # More than 1 per minute
            pattern_detected = True
            pattern_type = 'high_frequency_error'
        
        # Error bursts
        recent_count = len([occ for occ in error_seq['recent_occurrences'] 
                           if data.timestamp - occ['timestamp'] < 300])  # Last 5 minutes
        if recent_count > 10:
            pattern_detected = True
            pattern_type = 'error_burst'
        
        # Cascading errors (multiple files/functions)
        if len(error_seq['associated_files']) > 3 or len(error_seq['associated_functions']) > 5:
            pattern_detected = True
            pattern_type = 'cascading_error'
        
        processed_data['error_analysis'] = {
            'error_signature': error_signature,
            'total_occurrences': error_seq['count'],
            'frequency_per_hour': error_seq['frequency_per_hour'],
            'time_since_first_occurrence': data.timestamp - error_seq['first_seen'],
            'recent_occurrence_count': len(error_seq['recent_occurrences']),
            'pattern_detected': pattern_detected,
            'pattern_type': pattern_type,
            'associated_files_count': len(error_seq['associated_files']),
            'associated_functions_count': len(error_seq['associated_functions'])
        }
    
    def _create_error_signature(self, message: str) -> str:
        """Create a signature for error messages to group similar errors"""
        
        # Remove variable parts (numbers, IDs, timestamps, etc.)
        signature = re.sub(r'\b\d+\b', 'NUM', message)  # Replace numbers
        signature = re.sub(r'\b[a-fA-F0-9]{8,}\b', 'ID', signature)  # Replace hex IDs
        signature = re.sub(r'\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.*?\b', 'TIMESTAMP', signature)  # Replace timestamps
        signature = re.sub(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', 'IP', signature)  # Replace IP addresses
        signature = re.sub(r'/[^/\s]+/[^/\s]+', '/PATH', signature)  # Replace file paths
        
        # Normalize whitespace and truncate
        signature = ' '.join(signature.split())
        return signature[:200]  # Limit signature length
    
    async def _enrich_with_system_context(self, processed_data: Dict[str, Any], data: LogData, metadata: ProcessingMetadata) -> None:
        """Enrich with system-level context and kernel logs"""
        
        # Add system context if available
        if metadata.deep_system_context:
            processed_data['system_context'] = metadata.deep_system_context
        
        # Add kernel-level context for system logs
        if (processed_data['format_type'] == LogFormat.KERNEL.value or 
            processed_data['logger_name'] and 'kernel' in processed_data['logger_name'].lower()):
            
            processed_data['kernel_correlation'] = {
                'is_kernel_log': True,
                'kernel_subsystem': self._identify_kernel_subsystem(data.message),
                'deep_monitoring_candidate': True,
                'system_call_context': self._extract_syscall_context(data.message)
            }
            
            # Mock kernel log correlation for development
            processed_data['kernel_context'] = {
                'kernel_version': '5.15.0',
                'log_facility': self._identify_kernel_facility(data.message),
                'interrupt_context': 'interrupt' in data.message.lower(),
                'atomic_context': 'atomic' in data.message.lower(),
                'related_processes': self._extract_process_info(data.message)
            }
    
    def _identify_kernel_subsystem(self, message: str) -> str:
        """Identify kernel subsystem from log message"""
        message_lower = message.lower()
        
        if any(keyword in message_lower for keyword in ['mm:', 'oom', 'memory', 'page']):
            return 'memory_management'
        elif any(keyword in message_lower for keyword in ['block:', 'io', 'disk', 'scsi']):
            return 'block_io'
        elif any(keyword in message_lower for keyword in ['net:', 'tcp', 'udp', 'network']):
            return 'network'
        elif any(keyword in message_lower for keyword in ['sched:', 'task', 'process']):
            return 'scheduler'
        elif any(keyword in message_lower for keyword in ['fs:', 'filesystem', 'ext4', 'xfs']):
            return 'filesystem'
        elif any(keyword in message_lower for keyword in ['usb:', 'pci:', 'hardware']):
            return 'hardware'
        else:
            return 'general'
    
    def _identify_kernel_facility(self, message: str) -> str:
        """Identify kernel log facility"""
        message_lower = message.lower()
        
        if 'kern.' in message_lower:
            return 'kernel'
        elif 'daemon.' in message_lower:
            return 'daemon'
        elif 'auth.' in message_lower:
            return 'auth'
        elif 'mail.' in message_lower:
            return 'mail'
        else:
            return 'kernel'  # Default for kernel logs
    
    def _extract_syscall_context(self, message: str) -> Optional[Dict[str, Any]]:
        """Extract system call context from kernel logs"""
        
        # Look for system call patterns
        syscall_match = re.search(r'syscall[:\s]+(\w+)', message, re.IGNORECASE)
        if syscall_match:
            return {
                'syscall_name': syscall_match.group(1),
                'has_syscall_context': True
            }
        
        # Look for common syscall indicators
        syscall_indicators = ['open', 'read', 'write', 'close', 'mmap', 'fork', 'exec']
        for indicator in syscall_indicators:
            if indicator in message.lower():
                return {
                    'likely_syscall': indicator,
                    'has_syscall_context': True
                }
        
        return None
    
    def _extract_process_info(self, message: str) -> List[Dict[str, Any]]:
        """Extract process information from kernel logs"""
        
        processes = []
        
        # Extract PID patterns
        pid_matches = re.findall(r'pid[:\s]+(\d+)', message, re.IGNORECASE)
        for pid in pid_matches:
            processes.append({'pid': int(pid), 'type': 'pid'})
        
        # Extract process name patterns
        proc_matches = re.findall(r'comm[:\s]+"([^"]+)"', message, re.IGNORECASE)
        for proc_name in proc_matches:
            processes.append({'name': proc_name, 'type': 'process_name'})
        
        return processes
    
    async def _generate_correlation_hints(self, processed_data: Dict[str, Any]) -> List[str]:
        """Generate correlation hints for cross-pillar linking"""
        hints = []
        
        # Structured data correlation
        structured_data = processed_data['structured_data']
        
        if 'user_id' in structured_data:
            hints.append(f"user:{structured_data['user_id']}")
        
        if 'session_id' in structured_data:
            hints.append(f"session:{structured_data['session_id']}")
        
        if 'trace_id' in structured_data:
            hints.append(f"trace:{structured_data['trace_id']}")
        
        if 'span_id' in structured_data:
            hints.append(f"span:{structured_data['span_id']}")
        
        # Logger-based correlation
        if processed_data['logger_name']:
            hints.append(f"logger:{processed_data['logger_name']}")
        
        # File-based correlation
        if processed_data['source_file']:
            hints.append(f"source_file:{processed_data['source_file']}")
        
        # Level-based correlation
        hints.append(f"log_level:{processed_data['level']}")
        
        # Content category correlation
        if 'content_analysis' in processed_data:
            for category in processed_data['content_analysis']['categories']:
                hints.append(f"content_category:{category}")
        
        # Error pattern correlation
        if 'error_analysis' in processed_data:
            error_analysis = processed_data['error_analysis']
            hints.append(f"error_signature:{hash(error_analysis['error_signature']) % 10000}")
            if error_analysis['pattern_detected']:
                hints.append(f"error_pattern:{error_analysis['pattern_type']}")
        
        # Kernel correlation
        if 'kernel_correlation' in processed_data:
            kernel_ctx = processed_data['kernel_correlation']
            hints.append(f"kernel_subsystem:{kernel_ctx['kernel_subsystem']}")
        
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
        
        # Add structured data candidates
        structured_data = processed_data['structured_data']
        
        for field in ['user_id', 'session_id', 'trace_id', 'span_id', 'request_id']:
            if field in structured_data:
                candidates.append(f"{field}:{structured_data[field]}")
        
        # Add timestamp-based candidates (for temporal correlation)
        timestamp = processed_data['timestamp']
        # Create time windows for correlation (1s, 5s, 30s windows)
        for window in [1, 5, 30]:
            time_bucket = int(timestamp // window) * window
            candidates.append(f"time_window_{window}s:{time_bucket}")
        
        # Add logger-based candidates
        if processed_data['logger_name']:
            candidates.append(f"logger:{processed_data['logger_name']}")
        
        # Add error-based candidates
        if processed_data['level'] in ['error', 'fatal']:
            candidates.append(f"error_log:{processed_data['level']}")
            
            if 'error_analysis' in processed_data:
                error_sig = processed_data['error_analysis']['error_signature']
                candidates.append(f"error_signature:{hash(error_sig) % 10000}")
        
        # Add system-level candidates
        if 'kernel_correlation' in processed_data:
            kernel_ctx = processed_data['kernel_correlation']
            candidates.append(f"kernel_log:{kernel_ctx['kernel_subsystem']}")
        
        # Add performance candidates
        if 'performance' in processed_data.get('content_analysis', {}).get('categories', []):
            candidates.append("performance_issue:log_detected")
        
        return candidates
    
    async def get_error_patterns_summary(self) -> Dict[str, Any]:
        """Get summary of detected error patterns"""
        summary = {
            'total_error_patterns': len(self._error_sequences),
            'patterns': {}
        }
        
        for error_sig, error_data in self._error_sequences.items():
            summary['patterns'][error_sig[:50]] = {  # Truncate signature for display
                'count': error_data['count'],
                'frequency_per_hour': error_data['frequency_per_hour'],
                'first_seen': error_data['first_seen'],
                'last_seen': error_data['last_seen'],
                'associated_files_count': len(error_data['associated_files']),
                'recent_occurrence_count': len(error_data['recent_occurrences'])
            }
        
        return summary