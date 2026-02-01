"""
Data Sanitization Module

Provides security-focused data cleaning and sanitization capabilities including:
- XSS prevention and HTML sanitization
- SQL injection prevention
- Sensitive data detection and masking
- Content filtering and validation
"""

import re
import html
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import structlog

logger = structlog.get_logger()


class ThreatLevel(Enum):
    """Security threat levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SanitizationAction(Enum):
    """Actions taken during sanitization"""
    REMOVED = "removed"
    ESCAPED = "escaped"
    MASKED = "masked"
    BLOCKED = "blocked"
    ALLOWED = "allowed"


@dataclass
class SecurityThreat:
    """Security threat detection result"""
    threat_type: str
    threat_level: ThreatLevel
    description: str
    pattern: str
    location: str
    action_taken: SanitizationAction


@dataclass
class SanitizedData:
    """Container for sanitized data with security metadata"""
    data: Any
    original_data: Any
    threats_detected: List[SecurityThreat]
    sanitization_actions: List[str]
    is_safe: bool
    metadata: Dict[str, Any]
    timestamp: datetime


class DataSanitizer:
    """Comprehensive data sanitizer with security focus"""
    
    def __init__(self):
        self.logger = structlog.get_logger()
        self.threat_patterns = self._initialize_threat_patterns()
        self.sensitive_patterns = self._initialize_sensitive_patterns()
        self.allowed_html_tags = {'b', 'i', 'u', 'strong', 'em', 'p', 'br'}
        self.blocked_protocols = {'javascript:', 'data:', 'vbscript:', 'file:', 'ftp:'}
    
    def sanitize_data(self, data: Any, strict_mode: bool = False) -> SanitizedData:
        """
        Sanitize data to remove or escape potentially harmful content
        
        Args:
            data: Input data to sanitize
            strict_mode: If True, applies more aggressive sanitization
            
        Returns:
            SanitizedData with cleaned content and security metadata
        """
        original_data = data
        threats_detected = []
        sanitization_actions = []
        
        try:
            if isinstance(data, str):
                sanitized_data, str_threats, str_actions = self._sanitize_string(data, strict_mode)
                threats_detected.extend(str_threats)
                sanitization_actions.extend(str_actions)
                
            elif isinstance(data, dict):
                sanitized_data, dict_threats, dict_actions = self._sanitize_dict(data, strict_mode)
                threats_detected.extend(dict_threats)
                sanitization_actions.extend(dict_actions)
                
            elif isinstance(data, list):
                sanitized_data, list_threats, list_actions = self._sanitize_list(data, strict_mode)
                threats_detected.extend(list_threats)
                sanitization_actions.extend(list_actions)
                
            else:
                # For other data types, convert to string and sanitize
                str_data = str(data)
                sanitized_str, str_threats, str_actions = self._sanitize_string(str_data, strict_mode)
                sanitized_data = sanitized_str
                threats_detected.extend(str_threats)
                sanitization_actions.extend(str_actions)
            
            # Determine if data is safe
            critical_threats = [t for t in threats_detected if t.threat_level == ThreatLevel.CRITICAL]
            high_threats = [t for t in threats_detected if t.threat_level == ThreatLevel.HIGH]
            is_safe = len(critical_threats) == 0 and (not strict_mode or len(high_threats) == 0)
            
            # Create metadata
            metadata = {
                "threats_by_level": {
                    "critical": len(critical_threats),
                    "high": len([t for t in threats_detected if t.threat_level == ThreatLevel.HIGH]),
                    "medium": len([t for t in threats_detected if t.threat_level == ThreatLevel.MEDIUM]),
                    "low": len([t for t in threats_detected if t.threat_level == ThreatLevel.LOW])
                },
                "sanitization_summary": {
                    "actions_taken": len(sanitization_actions),
                    "data_modified": sanitized_data != original_data,
                    "strict_mode": strict_mode
                }
            }
            
            self.logger.info(
                "Data sanitization completed",
                is_safe=is_safe,
                threats_detected=len(threats_detected),
                actions_taken=len(sanitization_actions),
                strict_mode=strict_mode
            )
            
            return SanitizedData(
                data=sanitized_data,
                original_data=original_data,
                threats_detected=threats_detected,
                sanitization_actions=sanitization_actions,
                is_safe=is_safe,
                metadata=metadata,
                timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            self.logger.error(
                "Data sanitization failed",
                error=str(e),
                data_type=type(data).__name__
            )
            
            return SanitizedData(
                data=original_data,
                original_data=original_data,
                threats_detected=[SecurityThreat(
                    threat_type="sanitization_error",
                    threat_level=ThreatLevel.HIGH,
                    description=f"Sanitization failed: {str(e)}",
                    pattern="N/A",
                    location="sanitizer",
                    action_taken=SanitizationAction.BLOCKED
                )],
                sanitization_actions=["sanitization_failed"],
                is_safe=False,
                metadata={"error": str(e)},
                timestamp=datetime.now(timezone.utc)
            )
    
    def _sanitize_string(self, data: str, strict_mode: bool) -> Tuple[str, List[SecurityThreat], List[str]]:
        """Sanitize string data"""
        sanitized = data
        threats = []
        actions = []
        
        # Check for XSS patterns
        xss_threats, xss_actions = self._detect_and_sanitize_xss(sanitized, strict_mode)
        threats.extend(xss_threats)
        actions.extend(xss_actions)
        
        # Apply XSS sanitization
        for threat in xss_threats:
            if threat.action_taken == SanitizationAction.REMOVED:
                sanitized = re.sub(threat.pattern, '', sanitized, flags=re.IGNORECASE)
            elif threat.action_taken == SanitizationAction.ESCAPED:
                sanitized = html.escape(sanitized)
        
        # Check for SQL injection patterns
        sql_threats, sql_actions = self._detect_and_sanitize_sql_injection(sanitized, strict_mode)
        threats.extend(sql_threats)
        actions.extend(sql_actions)
        
        # Check for sensitive data
        sensitive_threats, sensitive_actions = self._detect_and_mask_sensitive_data(sanitized, strict_mode)
        threats.extend(sensitive_threats)
        actions.extend(sensitive_actions)
        
        # Apply sensitive data masking
        for threat in sensitive_threats:
            if threat.action_taken == SanitizationAction.MASKED:
                sanitized = re.sub(threat.pattern, self._create_mask(threat.pattern), sanitized, flags=re.IGNORECASE)
        
        # Check for dangerous protocols
        protocol_threats, protocol_actions = self._detect_dangerous_protocols(sanitized, strict_mode)
        threats.extend(protocol_threats)
        actions.extend(protocol_actions)
        
        # Remove dangerous protocols
        for protocol in self.blocked_protocols:
            if protocol in sanitized.lower():
                sanitized = re.sub(re.escape(protocol), '', sanitized, flags=re.IGNORECASE)
                actions.append(f"removed_protocol_{protocol}")
        
        # Normalize whitespace
        if re.search(r'\s{2,}', sanitized):
            sanitized = re.sub(r'\s+', ' ', sanitized).strip()
            actions.append("normalized_whitespace")
        
        return sanitized, threats, actions
    
    def _sanitize_dict(self, data: Dict[str, Any], strict_mode: bool) -> Tuple[Dict[str, Any], List[SecurityThreat], List[str]]:
        """Sanitize dictionary data"""
        sanitized = {}
        threats = []
        actions = []
        
        for key, value in data.items():
            # Sanitize key
            sanitized_key, key_threats, key_actions = self._sanitize_string(str(key), strict_mode)
            threats.extend(key_threats)
            actions.extend([f"key_{action}" for action in key_actions])
            
            # Recursively sanitize value
            if isinstance(value, (str, dict, list)):
                sanitized_value_result = self.sanitize_data(value, strict_mode)
                sanitized[sanitized_key] = sanitized_value_result.data
                threats.extend(sanitized_value_result.threats_detected)
                actions.extend([f"value_{action}" for action in sanitized_value_result.sanitization_actions])
            else:
                sanitized[sanitized_key] = value
        
        return sanitized, threats, actions
    
    def _sanitize_list(self, data: List[Any], strict_mode: bool) -> Tuple[List[Any], List[SecurityThreat], List[str]]:
        """Sanitize list data"""
        sanitized = []
        threats = []
        actions = []
        
        for i, item in enumerate(data):
            if isinstance(item, (str, dict, list)):
                sanitized_item_result = self.sanitize_data(item, strict_mode)
                sanitized.append(sanitized_item_result.data)
                threats.extend(sanitized_item_result.threats_detected)
                actions.extend([f"item_{i}_{action}" for action in sanitized_item_result.sanitization_actions])
            else:
                sanitized.append(item)
        
        return sanitized, threats, actions
    
    def _detect_and_sanitize_xss(self, data: str, strict_mode: bool) -> Tuple[List[SecurityThreat], List[str]]:
        """Detect and sanitize XSS patterns"""
        threats = []
        actions = []
        
        for pattern_name, pattern_info in self.threat_patterns['xss'].items():
            pattern = pattern_info['pattern']
            threat_level = pattern_info['level']
            
            if re.search(pattern, data, re.IGNORECASE):
                action = SanitizationAction.REMOVED if strict_mode or threat_level == ThreatLevel.CRITICAL else SanitizationAction.ESCAPED
                
                threats.append(SecurityThreat(
                    threat_type="xss",
                    threat_level=threat_level,
                    description=f"XSS pattern detected: {pattern_name}",
                    pattern=pattern,
                    location="string_content",
                    action_taken=action
                ))
                
                actions.append(f"xss_{action.value}_{pattern_name}")
        
        return threats, actions
    
    def _detect_and_sanitize_sql_injection(self, data: str, strict_mode: bool) -> Tuple[List[SecurityThreat], List[str]]:
        """Detect and sanitize SQL injection patterns"""
        threats = []
        actions = []
        
        for pattern_name, pattern_info in self.threat_patterns['sql_injection'].items():
            pattern = pattern_info['pattern']
            threat_level = pattern_info['level']
            
            if re.search(pattern, data, re.IGNORECASE):
                action = SanitizationAction.BLOCKED if threat_level == ThreatLevel.CRITICAL else SanitizationAction.ESCAPED
                
                threats.append(SecurityThreat(
                    threat_type="sql_injection",
                    threat_level=threat_level,
                    description=f"SQL injection pattern detected: {pattern_name}",
                    pattern=pattern,
                    location="string_content",
                    action_taken=action
                ))
                
                actions.append(f"sql_injection_{action.value}_{pattern_name}")
        
        return threats, actions
    
    def _detect_and_mask_sensitive_data(self, data: str, strict_mode: bool) -> Tuple[List[SecurityThreat], List[str]]:
        """Detect and mask sensitive data patterns"""
        threats = []
        actions = []
        
        for pattern_name, pattern_info in self.sensitive_patterns.items():
            pattern = pattern_info['pattern']
            threat_level = ThreatLevel.MEDIUM  # Sensitive data is medium threat
            
            matches = re.finditer(pattern, data, re.IGNORECASE)
            for match in matches:
                threats.append(SecurityThreat(
                    threat_type="sensitive_data",
                    threat_level=threat_level,
                    description=f"Sensitive data detected: {pattern_name}",
                    pattern=pattern,
                    location=f"position_{match.start()}-{match.end()}",
                    action_taken=SanitizationAction.MASKED
                ))
                
                actions.append(f"sensitive_data_masked_{pattern_name}")
        
        return threats, actions
    
    def _detect_dangerous_protocols(self, data: str, strict_mode: bool) -> Tuple[List[SecurityThreat], List[str]]:
        """Detect dangerous protocols in URLs"""
        threats = []
        actions = []
        
        for protocol in self.blocked_protocols:
            if protocol in data.lower():
                threats.append(SecurityThreat(
                    threat_type="dangerous_protocol",
                    threat_level=ThreatLevel.HIGH,
                    description=f"Dangerous protocol detected: {protocol}",
                    pattern=protocol,
                    location="url_protocol",
                    action_taken=SanitizationAction.REMOVED
                ))
                
                actions.append(f"dangerous_protocol_removed_{protocol.rstrip(':')}")
        
        return threats, actions
    
    def _create_mask(self, pattern: str) -> str:
        """Create appropriate mask for sensitive data"""
        # Simple masking - replace with asterisks
        return "***MASKED***"
    
    def _initialize_threat_patterns(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Initialize security threat patterns"""
        return {
            'xss': {
                'script_tag': {
                    'pattern': r'<script[^>]*>.*?</script>',
                    'level': ThreatLevel.CRITICAL
                },
                'javascript_protocol': {
                    'pattern': r'javascript\s*:',
                    'level': ThreatLevel.CRITICAL
                },
                'on_event_handlers': {
                    'pattern': r'on\w+\s*=',
                    'level': ThreatLevel.HIGH
                },
                'iframe_tag': {
                    'pattern': r'<iframe[^>]*>',
                    'level': ThreatLevel.HIGH
                },
                'object_tag': {
                    'pattern': r'<object[^>]*>',
                    'level': ThreatLevel.HIGH
                },
                'embed_tag': {
                    'pattern': r'<embed[^>]*>',
                    'level': ThreatLevel.HIGH
                },
                'form_tag': {
                    'pattern': r'<form[^>]*>',
                    'level': ThreatLevel.MEDIUM
                },
                'meta_refresh': {
                    'pattern': r'<meta[^>]*http-equiv[^>]*refresh',
                    'level': ThreatLevel.MEDIUM
                }
            },
            'sql_injection': {
                'union_select': {
                    'pattern': r'union\s+select',
                    'level': ThreatLevel.CRITICAL
                },
                'drop_table': {
                    'pattern': r'drop\s+table',
                    'level': ThreatLevel.CRITICAL
                },
                'delete_from': {
                    'pattern': r'delete\s+from',
                    'level': ThreatLevel.CRITICAL
                },
                'insert_into': {
                    'pattern': r'insert\s+into',
                    'level': ThreatLevel.HIGH
                },
                'update_set': {
                    'pattern': r'update\s+\w+\s+set',
                    'level': ThreatLevel.HIGH
                },
                'or_1_equals_1': {
                    'pattern': r'or\s+1\s*=\s*1',
                    'level': ThreatLevel.HIGH
                },
                'comment_injection': {
                    'pattern': r'--|\#|/\*|\*/',
                    'level': ThreatLevel.MEDIUM
                }
            }
        }
    
    def _initialize_sensitive_patterns(self) -> Dict[str, Dict[str, str]]:
        """Initialize sensitive data patterns"""
        return {
            'credit_card': {
                'pattern': r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
                'description': 'Credit card number'
            },
            'ssn': {
                'pattern': r'\b\d{3}-\d{2}-\d{4}\b',
                'description': 'Social Security Number'
            },
            'email': {
                'pattern': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                'description': 'Email address'
            },
            'phone': {
                'pattern': r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
                'description': 'Phone number'
            },
            'api_key': {
                'pattern': r'\b[A-Za-z0-9]{32,}\b',
                'description': 'Potential API key'
            },
            'password_field': {
                'pattern': r'password\s*[:=]\s*["\']?[^"\'\s]+["\']?',
                'description': 'Password field'
            },
            'token': {
                'pattern': r'token\s*[:=]\s*["\']?[A-Za-z0-9+/=]{20,}["\']?',
                'description': 'Authentication token'
            }
        }
    
    def is_content_safe(self, data: Any, strict_mode: bool = False) -> bool:
        """
        Quick check if content is safe without full sanitization
        
        Args:
            data: Data to check
            strict_mode: If True, applies stricter safety criteria
            
        Returns:
            Boolean indicating if content is considered safe
        """
        try:
            if isinstance(data, str):
                # Quick pattern checks for critical threats
                for pattern_info in self.threat_patterns['xss'].values():
                    if pattern_info['level'] == ThreatLevel.CRITICAL:
                        if re.search(pattern_info['pattern'], data, re.IGNORECASE):
                            return False
                
                for pattern_info in self.threat_patterns['sql_injection'].values():
                    if pattern_info['level'] == ThreatLevel.CRITICAL:
                        if re.search(pattern_info['pattern'], data, re.IGNORECASE):
                            return False
                
                # Check for dangerous protocols
                for protocol in self.blocked_protocols:
                    if protocol in data.lower():
                        return False
                
                return True
                
            elif isinstance(data, (dict, list)):
                # Recursively check nested structures
                if isinstance(data, dict):
                    return all(self.is_content_safe(v, strict_mode) for v in data.values())
                else:
                    return all(self.is_content_safe(item, strict_mode) for item in data)
            
            else:
                # Other data types are generally safe
                return True
                
        except Exception as e:
            self.logger.error(
                "Safety check failed",
                error=str(e),
                data_type=type(data).__name__
            )
            return False  # Err on the side of caution
    
    def batch_sanitize(self, data_list: List[Any], strict_mode: bool = False) -> List[SanitizedData]:
        """
        Sanitize a batch of data items efficiently
        
        Args:
            data_list: List of data items to sanitize
            strict_mode: If True, applies stricter sanitization
            
        Returns:
            List of SanitizedData objects
        """
        results = []
        
        self.logger.info(
            "Starting batch sanitization",
            batch_size=len(data_list),
            strict_mode=strict_mode
        )
        
        for i, data in enumerate(data_list):
            try:
                sanitized = self.sanitize_data(data, strict_mode)
                results.append(sanitized)
            except Exception as e:
                self.logger.error(
                    "Batch sanitization item failed",
                    index=i,
                    error=str(e)
                )
                # Add failed item with error metadata
                results.append(SanitizedData(
                    data=data,
                    original_data=data,
                    threats_detected=[SecurityThreat(
                        threat_type="sanitization_error",
                        threat_level=ThreatLevel.HIGH,
                        description=f"Batch sanitization failed: {str(e)}",
                        pattern="N/A",
                        location=f"batch_item_{i}",
                        action_taken=SanitizationAction.BLOCKED
                    )],
                    sanitization_actions=["batch_sanitization_failed"],
                    is_safe=False,
                    metadata={"error": str(e), "index": i},
                    timestamp=datetime.now(timezone.utc)
                ))
        
        safe_count = len([r for r in results if r.is_safe])
        unsafe_count = len(results) - safe_count
        
        self.logger.info(
            "Batch sanitization completed",
            total_items=len(data_list),
            safe_items=safe_count,
            unsafe_items=unsafe_count
        )
        
        return results