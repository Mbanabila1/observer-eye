"""
Events Processor

Specialized processor for events data - discrete occurrences and state changes.
Handles event classification, severity analysis, and real-time event correlation
with deep system integration for kernel events and security incidents.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import structlog

from .base_processor import BaseObservabilityProcessor, PillarType, ProcessingMetadata

logger = structlog.get_logger(__name__)

class EventSeverity(Enum):
    """Event severity levels"""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"

class EventCategory(Enum):
    """Event categories for classification"""
    SYSTEM = "system"
    APPLICATION = "application"
    SECURITY = "security"
    NETWORK = "network"
    USER = "user"
    INFRASTRUCTURE = "infrastructure"
    BUSINESS = "business"

@dataclass
class EventData:
    """Structured event data input"""
    event_type: str
    severity: EventSeverity
    message: str
    timestamp: Optional[float] = None
    source: Optional[str] = None
    category: Optional[EventCategory] = None
    attributes: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.attributes is None:
            self.attributes = {}
        if self.tags is None:
            self.tags = []

class EventsProcessor(BaseObservabilityProcessor[EventData]):
    """
    Processor for events data with real-time classification and correlation.
    
    Handles event severity analysis, pattern detection, and deep system
    integration for kernel events and security incident correlation.
    """
    
    def __init__(self, processor_id: str = "events_processor"):
        super().__init__(processor_id, PillarType.EVENTS)
        self._event_patterns = {}
        self._security_incidents = {}
        self._event_sequences = {}
        
    async def _validate_input(self, data: EventData) -> BaseObservabilityProcessor.ValidationResult:
        """Validate events input data"""
        try:
            # Check required fields
            if not data.event_type or not isinstance(data.event_type, str):
                return self.ValidationResult(
                    is_valid=False,
                    error_message="Event type is required and must be a string"
                )
            
            if not data.message or not isinstance(data.message, str):
                return self.ValidationResult(
                    is_valid=False,
                    error_message="Event message is required and must be a string"
                )
            
            # Validate severity
            if not isinstance(data.severity, EventSeverity):
                return self.ValidationResult(
                    is_valid=False,
                    error_message="Invalid event severity"
                )
            
            # Validate timestamp
            if data.timestamp is not None:
                if not isinstance(data.timestamp, (int, float)) or data.timestamp <= 0:
                    return self.ValidationResult(
                        is_valid=False,
                        error_message="Timestamp must be a positive number"
                    )
            
            # Validate category
            if data.category is not None and not isinstance(data.category, EventCategory):
                return self.ValidationResult(
                    is_valid=False,
                    error_message="Invalid event category"
                )
            
            # Validate attributes
            if data.attributes is not None and not isinstance(data.attributes, dict):
                return self.ValidationResult(
                    is_valid=False,
                    error_message="Attributes must be a dictionary"
                )
            
            # Validate tags
            if data.tags is not None:
                if not isinstance(data.tags, list):
                    return self.ValidationResult(
                        is_valid=False,
                        error_message="Tags must be a list"
                    )
                
                # Ensure all tags are strings
                for tag in data.tags:
                    if not isinstance(tag, str):
                        return self.ValidationResult(
                            is_valid=False,
                            error_message="All tags must be strings"
                        )
            
            return self.ValidationResult(is_valid=True, normalized_data=data)
            
        except Exception as e:
            return self.ValidationResult(
                is_valid=False,
                error_message=f"Validation error: {str(e)}"
            )
    
    async def _process_pillar_data(self, data: EventData, metadata: ProcessingMetadata) -> Dict[str, Any]:
        """Process events data with classification and enrichment"""
        
        # Create base processed data structure
        processed_data = {
            'event_type': data.event_type,
            'severity': data.severity.value,
            'message': data.message,
            'timestamp': data.timestamp,
            'timestamp_ns': int(data.timestamp * 1_000_000_000),  # Nanosecond precision
            'source': data.source,
            'category': data.category.value if data.category else None,
            'attributes': data.attributes or {},
            'tags': data.tags or [],
            'user_id': data.user_id,
            'session_id': data.session_id,
            'processing_metadata': {
                'processor_id': self.processor_id,
                'correlation_id': metadata.correlation_id,
                'processing_timestamp': metadata.processing_start_time
            }
        }
        
        # Classify event automatically if category not provided
        if not data.category:
            processed_data['category'] = await self._classify_event(data)
        
        # Analyze event severity and impact
        await self._analyze_event_severity(processed_data, data)
        
        # Detect event patterns and sequences
        await self._detect_event_patterns(processed_data, data)
        
        # Enrich with security context
        await self._enrich_with_security_context(processed_data, data, metadata)
        
        # Enrich with system context
        await self._enrich_with_system_context(processed_data, metadata)
        
        # Add correlation hints
        processed_data['correlation_hints'] = await self._generate_correlation_hints(processed_data)
        
        return processed_data
    
    async def _classify_event(self, data: EventData) -> str:
        """Automatically classify event based on type and content"""
        
        event_type_lower = data.event_type.lower()
        message_lower = data.message.lower()
        
        # Security event classification
        security_keywords = ['auth', 'login', 'logout', 'permission', 'access', 'security', 'breach', 'attack', 'malware']
        if any(keyword in event_type_lower or keyword in message_lower for keyword in security_keywords):
            return EventCategory.SECURITY.value
        
        # System event classification
        system_keywords = ['kernel', 'system', 'boot', 'shutdown', 'crash', 'panic', 'oom', 'disk', 'memory']
        if any(keyword in event_type_lower or keyword in message_lower for keyword in system_keywords):
            return EventCategory.SYSTEM.value
        
        # Network event classification
        network_keywords = ['network', 'connection', 'tcp', 'udp', 'dns', 'http', 'ssl', 'tls', 'firewall']
        if any(keyword in event_type_lower or keyword in message_lower for keyword in network_keywords):
            return EventCategory.NETWORK.value
        
        # Application event classification
        app_keywords = ['application', 'service', 'api', 'request', 'response', 'error', 'exception']
        if any(keyword in event_type_lower or keyword in message_lower for keyword in app_keywords):
            return EventCategory.APPLICATION.value
        
        # User event classification
        user_keywords = ['user', 'click', 'view', 'action', 'session', 'interaction']
        if any(keyword in event_type_lower or keyword in message_lower for keyword in user_keywords):
            return EventCategory.USER.value
        
        # Default to application
        return EventCategory.APPLICATION.value
    
    async def _analyze_event_severity(self, processed_data: Dict[str, Any], data: EventData) -> None:
        """Analyze event severity and calculate impact score"""
        
        severity_scores = {
            EventSeverity.DEBUG: 1,
            EventSeverity.INFO: 2,
            EventSeverity.WARNING: 3,
            EventSeverity.ERROR: 4,
            EventSeverity.CRITICAL: 5
        }
        
        base_score = severity_scores[data.severity]
        
        # Adjust score based on event characteristics
        impact_multipliers = {
            EventCategory.SECURITY: 1.5,
            EventCategory.SYSTEM: 1.3,
            EventCategory.NETWORK: 1.2,
            EventCategory.APPLICATION: 1.0,
            EventCategory.USER: 0.8,
            EventCategory.INFRASTRUCTURE: 1.4,
            EventCategory.BUSINESS: 1.1
        }
        
        category = EventCategory(processed_data['category']) if processed_data['category'] else EventCategory.APPLICATION
        multiplier = impact_multipliers.get(category, 1.0)
        
        # Calculate final impact score
        impact_score = min(10.0, base_score * multiplier)
        
        processed_data['severity_analysis'] = {
            'base_severity': data.severity.value,
            'severity_score': base_score,
            'category_multiplier': multiplier,
            'impact_score': impact_score,
            'requires_immediate_attention': impact_score >= 7.0,
            'escalation_recommended': impact_score >= 8.5
        }
        
        # Add urgency classification
        if impact_score >= 8.5:
            processed_data['urgency'] = 'critical'
        elif impact_score >= 6.0:
            processed_data['urgency'] = 'high'
        elif impact_score >= 4.0:
            processed_data['urgency'] = 'medium'
        else:
            processed_data['urgency'] = 'low'
    
    async def _detect_event_patterns(self, processed_data: Dict[str, Any], data: EventData) -> None:
        """Detect event patterns and sequences for correlation"""
        
        event_key = f"{data.event_type}:{data.source or 'unknown'}"
        
        # Initialize pattern tracking
        if event_key not in self._event_patterns:
            self._event_patterns[event_key] = {
                'count': 0,
                'first_seen': data.timestamp,
                'last_seen': data.timestamp,
                'frequency_per_minute': 0.0,
                'recent_events': []
            }
        
        pattern = self._event_patterns[event_key]
        pattern['count'] += 1
        pattern['last_seen'] = data.timestamp
        
        # Calculate frequency
        time_span = data.timestamp - pattern['first_seen']
        if time_span > 0:
            pattern['frequency_per_minute'] = (pattern['count'] / time_span) * 60
        
        # Maintain recent events buffer
        pattern['recent_events'].append({
            'timestamp': data.timestamp,
            'severity': data.severity.value,
            'message': data.message[:100]  # Truncate for storage
        })
        
        # Keep only last 50 events
        if len(pattern['recent_events']) > 50:
            pattern['recent_events'].pop(0)
        
        # Detect anomalous patterns
        anomaly_detected = False
        anomaly_type = None
        
        # High frequency detection
        if pattern['frequency_per_minute'] > 100:  # More than 100 events per minute
            anomaly_detected = True
            anomaly_type = 'high_frequency'
        
        # Burst detection (many events in short time)
        recent_count = len([e for e in pattern['recent_events'] 
                           if data.timestamp - e['timestamp'] < 60])  # Last minute
        if recent_count > 20:
            anomaly_detected = True
            anomaly_type = 'burst_pattern'
        
        # Severity escalation detection
        recent_severities = [e['severity'] for e in pattern['recent_events'][-10:]]
        if len(recent_severities) >= 5:
            severity_scores = [{'debug': 1, 'info': 2, 'warning': 3, 'error': 4, 'critical': 5}[s] 
                             for s in recent_severities]
            if len(severity_scores) >= 3 and all(severity_scores[i] <= severity_scores[i+1] 
                                               for i in range(len(severity_scores)-1)):
                anomaly_detected = True
                anomaly_type = 'severity_escalation'
        
        processed_data['pattern_analysis'] = {
            'event_pattern_key': event_key,
            'total_occurrences': pattern['count'],
            'frequency_per_minute': pattern['frequency_per_minute'],
            'time_since_first_occurrence': time_span,
            'recent_event_count': len(pattern['recent_events']),
            'anomaly_detected': anomaly_detected,
            'anomaly_type': anomaly_type,
            'pattern_stability': 'stable' if pattern['frequency_per_minute'] < 10 else 'unstable'
        }
    
    async def _enrich_with_security_context(self, processed_data: Dict[str, Any], data: EventData, metadata: ProcessingMetadata) -> None:
        """Enrich with security context and threat analysis"""
        
        if processed_data['category'] == EventCategory.SECURITY.value:
            # Security event analysis
            security_context = {
                'is_security_event': True,
                'threat_level': self._assess_threat_level(data),
                'security_domain': self._identify_security_domain(data),
                'requires_investigation': data.severity in [EventSeverity.ERROR, EventSeverity.CRITICAL]
            }
            
            # Check for known attack patterns
            attack_patterns = await self._check_attack_patterns(data)
            if attack_patterns:
                security_context['attack_patterns'] = attack_patterns
                security_context['threat_level'] = 'high'
            
            # Add to security incidents tracking
            if security_context['threat_level'] in ['high', 'critical']:
                incident_id = f"sec_{int(data.timestamp)}_{hash(data.message) % 10000}"
                self._security_incidents[incident_id] = {
                    'event_type': data.event_type,
                    'severity': data.severity.value,
                    'timestamp': data.timestamp,
                    'source': data.source,
                    'correlation_id': metadata.correlation_id
                }
                security_context['incident_id'] = incident_id
            
            processed_data['security_context'] = security_context
    
    def _assess_threat_level(self, data: EventData) -> str:
        """Assess threat level based on event characteristics"""
        
        if data.severity == EventSeverity.CRITICAL:
            return 'critical'
        elif data.severity == EventSeverity.ERROR:
            return 'high'
        elif data.severity == EventSeverity.WARNING:
            return 'medium'
        else:
            return 'low'
    
    def _identify_security_domain(self, data: EventData) -> str:
        """Identify security domain for the event"""
        
        message_lower = data.message.lower()
        event_type_lower = data.event_type.lower()
        
        if any(keyword in message_lower or keyword in event_type_lower 
               for keyword in ['auth', 'login', 'logout', 'credential']):
            return 'authentication'
        elif any(keyword in message_lower or keyword in event_type_lower 
                 for keyword in ['permission', 'access', 'authorization', 'role']):
            return 'authorization'
        elif any(keyword in message_lower or keyword in event_type_lower 
                 for keyword in ['network', 'firewall', 'intrusion', 'scan']):
            return 'network_security'
        elif any(keyword in message_lower or keyword in event_type_lower 
                 for keyword in ['malware', 'virus', 'trojan', 'ransomware']):
            return 'malware'
        elif any(keyword in message_lower or keyword in event_type_lower 
                 for keyword in ['data', 'leak', 'breach', 'exposure']):
            return 'data_protection'
        else:
            return 'general_security'
    
    async def _check_attack_patterns(self, data: EventData) -> Optional[List[str]]:
        """Check for known attack patterns in the event"""
        
        patterns = []
        message_lower = data.message.lower()
        
        # SQL injection patterns
        if any(pattern in message_lower for pattern in ['union select', 'drop table', '1=1', 'or 1=1']):
            patterns.append('sql_injection')
        
        # XSS patterns
        if any(pattern in message_lower for pattern in ['<script>', 'javascript:', 'onerror=']):
            patterns.append('xss_attempt')
        
        # Brute force patterns
        if 'failed login' in message_lower or 'authentication failed' in message_lower:
            patterns.append('brute_force_candidate')
        
        # Directory traversal
        if any(pattern in message_lower for pattern in ['../', '..\\', '/etc/passwd']):
            patterns.append('directory_traversal')
        
        # Command injection
        if any(pattern in message_lower for pattern in [';cat ', '|nc ', '&& rm']):
            patterns.append('command_injection')
        
        return patterns if patterns else None
    
    async def _enrich_with_system_context(self, processed_data: Dict[str, Any], metadata: ProcessingMetadata) -> None:
        """Enrich with system-level context and kernel events"""
        
        # Add system context if available
        if metadata.deep_system_context:
            processed_data['system_context'] = metadata.deep_system_context
        
        # Add kernel-level context for system events
        if processed_data['category'] == EventCategory.SYSTEM.value:
            processed_data['kernel_correlation'] = {
                'is_system_event': True,
                'kernel_subsystem': self._identify_kernel_subsystem(processed_data['event_type']),
                'deep_monitoring_candidate': True
            }
            
            # Mock kernel event correlation for development
            processed_data['kernel_events'] = {
                'related_syscalls': ['open', 'read', 'write', 'close'],
                'kernel_module': self._identify_kernel_module(processed_data['event_type']),
                'interrupt_context': False,
                'process_context': True
            }
    
    def _identify_kernel_subsystem(self, event_type: str) -> str:
        """Identify kernel subsystem for system events"""
        event_lower = event_type.lower()
        
        if any(keyword in event_lower for keyword in ['memory', 'oom', 'swap']):
            return 'memory_management'
        elif any(keyword in event_lower for keyword in ['disk', 'io', 'filesystem']):
            return 'block_io'
        elif any(keyword in event_lower for keyword in ['network', 'tcp', 'udp']):
            return 'network_stack'
        elif any(keyword in event_lower for keyword in ['process', 'task', 'schedule']):
            return 'process_scheduler'
        else:
            return 'general'
    
    def _identify_kernel_module(self, event_type: str) -> str:
        """Identify likely kernel module for system events"""
        event_lower = event_type.lower()
        
        if 'network' in event_lower:
            return 'netfilter'
        elif 'disk' in event_lower or 'io' in event_lower:
            return 'block'
        elif 'memory' in event_lower:
            return 'mm'
        else:
            return 'kernel'
    
    async def _generate_correlation_hints(self, processed_data: Dict[str, Any]) -> List[str]:
        """Generate correlation hints for cross-pillar linking"""
        hints = []
        
        # Service-based correlation
        if processed_data['source']:
            hints.append(f"source:{processed_data['source']}")
        
        # User-based correlation
        if processed_data['user_id']:
            hints.append(f"user:{processed_data['user_id']}")
        
        # Session-based correlation
        if processed_data['session_id']:
            hints.append(f"session:{processed_data['session_id']}")
        
        # Category correlation
        hints.append(f"category:{processed_data['category']}")
        
        # Severity correlation
        hints.append(f"severity:{processed_data['severity']}")
        
        # Event type correlation
        hints.append(f"event_type:{processed_data['event_type']}")
        
        # Security correlation
        if 'security_context' in processed_data:
            security_ctx = processed_data['security_context']
            hints.append(f"security_domain:{security_ctx['security_domain']}")
            hints.append(f"threat_level:{security_ctx['threat_level']}")
        
        # System correlation
        if 'kernel_correlation' in processed_data:
            kernel_ctx = processed_data['kernel_correlation']
            hints.append(f"kernel_subsystem:{kernel_ctx['kernel_subsystem']}")
        
        # Pattern correlation
        if 'pattern_analysis' in processed_data:
            pattern = processed_data['pattern_analysis']
            hints.append(f"event_pattern:{pattern['event_pattern_key']}")
            if pattern['anomaly_detected']:
                hints.append(f"anomaly:{pattern['anomaly_type']}")
        
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
        
        # Add user-based candidates
        if processed_data['user_id']:
            candidates.append(f"user:{processed_data['user_id']}")
        
        # Add session-based candidates
        if processed_data['session_id']:
            candidates.append(f"session:{processed_data['session_id']}")
        
        # Add source-based candidates
        if processed_data['source']:
            candidates.append(f"source:{processed_data['source']}")
        
        # Add timestamp-based candidates (for temporal correlation)
        timestamp = processed_data['timestamp']
        # Create time windows for correlation (1s, 5s, 30s windows)
        for window in [1, 5, 30]:
            time_bucket = int(timestamp // window) * window
            candidates.append(f"time_window_{window}s:{time_bucket}")
        
        # Add event-specific candidates
        candidates.append(f"event_type:{processed_data['event_type']}")
        candidates.append(f"category:{processed_data['category']}")
        
        # Add severity-based candidates
        if processed_data['severity'] in ['error', 'critical']:
            candidates.append(f"high_severity_event:{processed_data['severity']}")
        
        # Add security incident candidates
        if 'security_context' in processed_data:
            security_ctx = processed_data['security_context']
            candidates.append(f"security_event:{security_ctx['security_domain']}")
            if 'incident_id' in security_ctx:
                candidates.append(f"security_incident:{security_ctx['incident_id']}")
        
        # Add system event candidates
        if 'kernel_correlation' in processed_data:
            candidates.append(f"system_event:{processed_data['kernel_correlation']['kernel_subsystem']}")
        
        return candidates
    
    async def get_security_incidents_summary(self) -> Dict[str, Any]:
        """Get summary of current security incidents"""
        return {
            'total_incidents': len(self._security_incidents),
            'incidents': dict(list(self._security_incidents.items())[-10:])  # Last 10 incidents
        }
    
    async def get_event_patterns_summary(self) -> Dict[str, Any]:
        """Get summary of detected event patterns"""
        summary = {
            'total_patterns': len(self._event_patterns),
            'patterns': {}
        }
        
        for pattern_key, pattern_data in self._event_patterns.items():
            summary['patterns'][pattern_key] = {
                'count': pattern_data['count'],
                'frequency_per_minute': pattern_data['frequency_per_minute'],
                'first_seen': pattern_data['first_seen'],
                'last_seen': pattern_data['last_seen'],
                'recent_event_count': len(pattern_data['recent_events'])
            }
        
        return summary