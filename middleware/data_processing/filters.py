"""
Data Filtering Module

Provides comprehensive data filtering capabilities including:
- Invalid data filtering and removal
- Polymorphic data handling
- Content-based filtering
- Rule-based data filtering
"""

import re
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Callable, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import structlog

logger = structlog.get_logger()


class FilterAction(Enum):
    """Actions that can be taken on filtered data"""
    INCLUDE = "include"
    EXCLUDE = "exclude"
    TRANSFORM = "transform"
    FLAG = "flag"


class FilterType(Enum):
    """Types of filters available"""
    VALIDATION = "validation"
    CONTENT = "content"
    STRUCTURE = "structure"
    SECURITY = "security"
    BUSINESS_RULE = "business_rule"


@dataclass
class FilterRule:
    """Configuration for a data filter rule"""
    name: str
    filter_type: FilterType
    condition: Union[str, Callable[[Any], bool]]
    action: FilterAction
    description: str
    priority: int = 0
    enabled: bool = True
    metadata: Dict[str, Any] = None


@dataclass
class FilterResult:
    """Result of applying a filter"""
    original_data: Any
    filtered_data: Any
    rules_applied: List[str]
    items_included: int
    items_excluded: int
    items_transformed: int
    items_flagged: int
    metadata: Dict[str, Any]
    timestamp: datetime


@dataclass
class FilterConfig:
    """Configuration for data filtering"""
    rules: List[FilterRule]
    strict_mode: bool = False
    preserve_structure: bool = True
    log_filtered_items: bool = True


class DataFilter:
    """Comprehensive data filter with polymorphic support"""
    
    def __init__(self, config: Optional[FilterConfig] = None):
        self.logger = structlog.get_logger()
        self.config = config or FilterConfig(rules=[])
        self.default_rules = self._initialize_default_rules()
        self.stats = {
            'total_filtered': 0,
            'total_included': 0,
            'total_excluded': 0,
            'total_transformed': 0,
            'total_flagged': 0
        }
    
    def filter_data(self, data: Any, custom_rules: Optional[List[FilterRule]] = None) -> FilterResult:
        """
        Filter data based on configured rules
        
        Args:
            data: Input data to filter
            custom_rules: Optional additional rules to apply
            
        Returns:
            FilterResult with filtered data and metadata
        """
        original_data = data
        rules_to_apply = self._get_active_rules(custom_rules)
        rules_applied = []
        
        stats = {
            'included': 0,
            'excluded': 0,
            'transformed': 0,
            'flagged': 0
        }
        
        try:
            if isinstance(data, list):
                filtered_data, list_stats, list_rules = self._filter_list(data, rules_to_apply)
                stats.update(list_stats)
                rules_applied.extend(list_rules)
                
            elif isinstance(data, dict):
                filtered_data, dict_stats, dict_rules = self._filter_dict(data, rules_to_apply)
                stats.update(dict_stats)
                rules_applied.extend(dict_rules)
                
            else:
                # Single item filtering
                filtered_data, item_stats, item_rules = self._filter_single_item(data, rules_to_apply)
                stats.update(item_stats)
                rules_applied.extend(item_rules)
            
            # Update global stats
            self.stats['total_filtered'] += 1
            self.stats['total_included'] += stats['included']
            self.stats['total_excluded'] += stats['excluded']
            self.stats['total_transformed'] += stats['transformed']
            self.stats['total_flagged'] += stats['flagged']
            
            metadata = {
                'filter_stats': stats,
                'rules_count': len(rules_to_apply),
                'data_type': type(original_data).__name__,
                'strict_mode': self.config.strict_mode,
                'preserve_structure': self.config.preserve_structure
            }
            
            self.logger.info(
                "Data filtering completed",
                original_type=type(original_data).__name__,
                filtered_type=type(filtered_data).__name__,
                rules_applied=len(rules_applied),
                stats=stats
            )
            
            return FilterResult(
                original_data=original_data,
                filtered_data=filtered_data,
                rules_applied=rules_applied,
                items_included=stats['included'],
                items_excluded=stats['excluded'],
                items_transformed=stats['transformed'],
                items_flagged=stats['flagged'],
                metadata=metadata,
                timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            self.logger.error(
                "Data filtering failed",
                error=str(e),
                data_type=type(data).__name__
            )
            
            return FilterResult(
                original_data=original_data,
                filtered_data=original_data,  # Return original on error
                rules_applied=["filtering_failed"],
                items_included=0,
                items_excluded=0,
                items_transformed=0,
                items_flagged=0,
                metadata={"error": str(e)},
                timestamp=datetime.now(timezone.utc)
            )
    
    def _filter_list(self, data: List[Any], rules: List[FilterRule]) -> Tuple[List[Any], Dict[str, int], List[str]]:
        """Filter list data"""
        filtered_items = []
        stats = {'included': 0, 'excluded': 0, 'transformed': 0, 'flagged': 0}
        rules_applied = []
        
        for i, item in enumerate(data):
            item_result = self._apply_rules_to_item(item, rules, f"list_item_{i}")
            
            if item_result['action'] == FilterAction.INCLUDE:
                filtered_items.append(item_result['data'])
                stats['included'] += 1
            elif item_result['action'] == FilterAction.EXCLUDE:
                stats['excluded'] += 1
                if self.config.log_filtered_items:
                    self.logger.debug(
                        "List item excluded",
                        index=i,
                        reason=item_result['reason'],
                        item_preview=str(item)[:100]
                    )
            elif item_result['action'] == FilterAction.TRANSFORM:
                filtered_items.append(item_result['data'])
                stats['transformed'] += 1
            elif item_result['action'] == FilterAction.FLAG:
                filtered_items.append(item_result['data'])
                stats['flagged'] += 1
                self.logger.warning(
                    "List item flagged",
                    index=i,
                    reason=item_result['reason'],
                    item_preview=str(item)[:100]
                )
            
            rules_applied.extend(item_result['rules_applied'])
        
        return filtered_items, stats, rules_applied
    
    def _filter_dict(self, data: Dict[str, Any], rules: List[FilterRule]) -> Tuple[Dict[str, Any], Dict[str, int], List[str]]:
        """Filter dictionary data"""
        filtered_dict = {}
        stats = {'included': 0, 'excluded': 0, 'transformed': 0, 'flagged': 0}
        rules_applied = []
        
        for key, value in data.items():
            # Apply rules to key-value pair
            item_result = self._apply_rules_to_item(
                {'key': key, 'value': value}, 
                rules, 
                f"dict_key_{key}"
            )
            
            if item_result['action'] == FilterAction.INCLUDE:
                filtered_dict[key] = value
                stats['included'] += 1
            elif item_result['action'] == FilterAction.EXCLUDE:
                stats['excluded'] += 1
                if self.config.log_filtered_items:
                    self.logger.debug(
                        "Dict item excluded",
                        key=key,
                        reason=item_result['reason'],
                        value_preview=str(value)[:100]
                    )
            elif item_result['action'] == FilterAction.TRANSFORM:
                # Apply transformation to value
                transformed_data = item_result['data']
                if isinstance(transformed_data, dict) and 'value' in transformed_data:
                    filtered_dict[key] = transformed_data['value']
                else:
                    filtered_dict[key] = transformed_data
                stats['transformed'] += 1
            elif item_result['action'] == FilterAction.FLAG:
                filtered_dict[key] = value
                stats['flagged'] += 1
                self.logger.warning(
                    "Dict item flagged",
                    key=key,
                    reason=item_result['reason'],
                    value_preview=str(value)[:100]
                )
            
            rules_applied.extend(item_result['rules_applied'])
        
        return filtered_dict, stats, rules_applied
    
    def _filter_single_item(self, data: Any, rules: List[FilterRule]) -> Tuple[Any, Dict[str, int], List[str]]:
        """Filter single data item"""
        stats = {'included': 0, 'excluded': 0, 'transformed': 0, 'flagged': 0}
        
        item_result = self._apply_rules_to_item(data, rules, "single_item")
        
        if item_result['action'] == FilterAction.INCLUDE:
            stats['included'] = 1
            return item_result['data'], stats, item_result['rules_applied']
        elif item_result['action'] == FilterAction.EXCLUDE:
            stats['excluded'] = 1
            return None, stats, item_result['rules_applied']
        elif item_result['action'] == FilterAction.TRANSFORM:
            stats['transformed'] = 1
            return item_result['data'], stats, item_result['rules_applied']
        elif item_result['action'] == FilterAction.FLAG:
            stats['flagged'] = 1
            return item_result['data'], stats, item_result['rules_applied']
        
        # Default to include
        stats['included'] = 1
        return data, stats, []
    
    def _apply_rules_to_item(self, item: Any, rules: List[FilterRule], context: str) -> Dict[str, Any]:
        """Apply filtering rules to a single item"""
        current_data = item
        final_action = FilterAction.INCLUDE
        rules_applied = []
        reason = "default_include"
        
        # Sort rules by priority (higher priority first)
        sorted_rules = sorted(rules, key=lambda r: r.priority, reverse=True)
        
        for rule in sorted_rules:
            if not rule.enabled:
                continue
            
            try:
                # Check if rule condition matches
                if self._evaluate_rule_condition(current_data, rule):
                    rules_applied.append(rule.name)
                    
                    if rule.action == FilterAction.EXCLUDE:
                        final_action = FilterAction.EXCLUDE
                        reason = f"excluded_by_{rule.name}"
                        break  # Exclusion takes precedence
                    
                    elif rule.action == FilterAction.TRANSFORM:
                        # Apply transformation
                        current_data = self._apply_transformation(current_data, rule)
                        final_action = FilterAction.TRANSFORM
                        reason = f"transformed_by_{rule.name}"
                    
                    elif rule.action == FilterAction.FLAG:
                        final_action = FilterAction.FLAG
                        reason = f"flagged_by_{rule.name}"
                    
                    # In strict mode, first matching rule wins
                    if self.config.strict_mode:
                        break
                        
            except Exception as e:
                self.logger.error(
                    "Rule evaluation failed",
                    rule_name=rule.name,
                    context=context,
                    error=str(e)
                )
                continue
        
        return {
            'data': current_data,
            'action': final_action,
            'reason': reason,
            'rules_applied': rules_applied
        }
    
    def _evaluate_rule_condition(self, data: Any, rule: FilterRule) -> bool:
        """Evaluate if a rule condition matches the data"""
        try:
            if callable(rule.condition):
                return rule.condition(data)
            
            elif isinstance(rule.condition, str):
                # String-based conditions
                if rule.filter_type == FilterType.VALIDATION:
                    return self._evaluate_validation_condition(data, rule.condition)
                elif rule.filter_type == FilterType.CONTENT:
                    return self._evaluate_content_condition(data, rule.condition)
                elif rule.filter_type == FilterType.STRUCTURE:
                    return self._evaluate_structure_condition(data, rule.condition)
                elif rule.filter_type == FilterType.SECURITY:
                    return self._evaluate_security_condition(data, rule.condition)
                elif rule.filter_type == FilterType.BUSINESS_RULE:
                    return self._evaluate_business_rule_condition(data, rule.condition)
            
            return False
            
        except Exception as e:
            self.logger.error(
                "Rule condition evaluation failed",
                rule_name=rule.name,
                condition=str(rule.condition),
                error=str(e)
            )
            return False
    
    def _evaluate_validation_condition(self, data: Any, condition: str) -> bool:
        """Evaluate validation-based conditions"""
        if condition == "is_null":
            return data is None
        elif condition == "is_empty":
            return not data or (isinstance(data, (str, list, dict)) and len(data) == 0)
        elif condition == "is_valid_json":
            if isinstance(data, str):
                try:
                    json.loads(data)
                    return True
                except json.JSONDecodeError:
                    return False
            return False
        elif condition == "is_numeric":
            return isinstance(data, (int, float)) or (isinstance(data, str) and data.replace('.', '').replace('-', '').isdigit())
        elif condition == "is_string":
            return isinstance(data, str)
        elif condition == "is_boolean":
            return isinstance(data, bool)
        elif condition == "is_list":
            return isinstance(data, list)
        elif condition == "is_dict":
            return isinstance(data, dict)
        
        return False
    
    def _evaluate_content_condition(self, data: Any, condition: str) -> bool:
        """Evaluate content-based conditions"""
        if not isinstance(data, str):
            data = str(data)
        
        if condition.startswith("contains:"):
            pattern = condition[9:]  # Remove "contains:" prefix
            return pattern.lower() in data.lower()
        elif condition.startswith("regex:"):
            pattern = condition[6:]  # Remove "regex:" prefix
            return bool(re.search(pattern, data, re.IGNORECASE))
        elif condition.startswith("starts_with:"):
            prefix = condition[12:]  # Remove "starts_with:" prefix
            return data.lower().startswith(prefix.lower())
        elif condition.startswith("ends_with:"):
            suffix = condition[10:]  # Remove "ends_with:" prefix
            return data.lower().endswith(suffix.lower())
        elif condition == "has_special_chars":
            return bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', data))
        elif condition == "has_numbers":
            return bool(re.search(r'\d', data))
        elif condition == "has_uppercase":
            return bool(re.search(r'[A-Z]', data))
        elif condition == "has_lowercase":
            return bool(re.search(r'[a-z]', data))
        
        return False
    
    def _evaluate_structure_condition(self, data: Any, condition: str) -> bool:
        """Evaluate structure-based conditions"""
        if condition.startswith("min_length:"):
            min_len = int(condition[11:])
            return len(str(data)) >= min_len
        elif condition.startswith("max_length:"):
            max_len = int(condition[11:])
            return len(str(data)) <= max_len
        elif condition.startswith("has_key:"):
            key = condition[8:]
            return isinstance(data, dict) and key in data
        elif condition.startswith("list_min_size:"):
            min_size = int(condition[14:])
            return isinstance(data, list) and len(data) >= min_size
        elif condition.startswith("list_max_size:"):
            max_size = int(condition[14:])
            return isinstance(data, list) and len(data) <= max_size
        elif condition == "is_nested":
            return isinstance(data, (dict, list)) and any(
                isinstance(v, (dict, list)) for v in (data.values() if isinstance(data, dict) else data)
            )
        
        return False
    
    def _evaluate_security_condition(self, data: Any, condition: str) -> bool:
        """Evaluate security-based conditions"""
        if not isinstance(data, str):
            data = str(data)
        
        if condition == "has_script_tags":
            return bool(re.search(r'<script[^>]*>', data, re.IGNORECASE))
        elif condition == "has_sql_injection":
            sql_patterns = [r'union\s+select', r'drop\s+table', r'delete\s+from', r'insert\s+into']
            return any(re.search(pattern, data, re.IGNORECASE) for pattern in sql_patterns)
        elif condition == "has_xss_patterns":
            xss_patterns = [r'javascript:', r'on\w+\s*=', r'<iframe', r'<object', r'<embed']
            return any(re.search(pattern, data, re.IGNORECASE) for pattern in xss_patterns)
        elif condition == "has_sensitive_data":
            sensitive_patterns = [
                r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Credit card
                r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
                r'password\s*[:=]',  # Password field
                r'token\s*[:=]'  # Token field
            ]
            return any(re.search(pattern, data, re.IGNORECASE) for pattern in sensitive_patterns)
        
        return False
    
    def _evaluate_business_rule_condition(self, data: Any, condition: str) -> bool:
        """Evaluate business rule conditions"""
        # This would be customized based on specific business requirements
        # For now, implement some common patterns
        
        if condition == "is_valid_email":
            if isinstance(data, str):
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                return bool(re.match(email_pattern, data))
        elif condition == "is_valid_phone":
            if isinstance(data, str):
                phone_pattern = r'^\+?[1-9]\d{1,14}$'
                return bool(re.match(phone_pattern, re.sub(r'[^\d+]', '', data)))
        elif condition == "is_valid_url":
            if isinstance(data, str):
                url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
                return bool(re.match(url_pattern, data))
        elif condition == "is_recent_timestamp":
            if isinstance(data, str):
                try:
                    dt = datetime.fromisoformat(data.replace('Z', '+00:00'))
                    age_hours = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
                    return age_hours <= 24  # Within last 24 hours
                except:
                    return False
        
        return False
    
    def _apply_transformation(self, data: Any, rule: FilterRule) -> Any:
        """Apply transformation based on rule"""
        # This is a simplified transformation system
        # In practice, this would be more sophisticated
        
        if rule.metadata and 'transform_function' in rule.metadata:
            transform_func = rule.metadata['transform_function']
            if callable(transform_func):
                return transform_func(data)
        
        # Default transformations
        if isinstance(data, str):
            if rule.name == "normalize_whitespace":
                return re.sub(r'\s+', ' ', data).strip()
            elif rule.name == "lowercase":
                return data.lower()
            elif rule.name == "remove_special_chars":
                return re.sub(r'[^a-zA-Z0-9\s]', '', data)
        
        return data
    
    def _get_active_rules(self, custom_rules: Optional[List[FilterRule]] = None) -> List[FilterRule]:
        """Get list of active rules to apply"""
        rules = []
        
        # Add default rules
        rules.extend([rule for rule in self.default_rules if rule.enabled])
        
        # Add configured rules
        rules.extend([rule for rule in self.config.rules if rule.enabled])
        
        # Add custom rules
        if custom_rules:
            rules.extend([rule for rule in custom_rules if rule.enabled])
        
        return rules
    
    def _initialize_default_rules(self) -> List[FilterRule]:
        """Initialize default filtering rules"""
        return [
            FilterRule(
                name="exclude_null_values",
                filter_type=FilterType.VALIDATION,
                condition="is_null",
                action=FilterAction.EXCLUDE,
                description="Exclude null/None values",
                priority=100
            ),
            FilterRule(
                name="exclude_empty_strings",
                filter_type=FilterType.VALIDATION,
                condition="is_empty",
                action=FilterAction.EXCLUDE,
                description="Exclude empty strings, lists, and dicts",
                priority=90
            ),
            FilterRule(
                name="flag_security_threats",
                filter_type=FilterType.SECURITY,
                condition="has_xss_patterns",
                action=FilterAction.FLAG,
                description="Flag potential XSS patterns",
                priority=200
            ),
            FilterRule(
                name="exclude_sql_injection",
                filter_type=FilterType.SECURITY,
                condition="has_sql_injection",
                action=FilterAction.EXCLUDE,
                description="Exclude SQL injection patterns",
                priority=300
            ),
            FilterRule(
                name="normalize_whitespace",
                filter_type=FilterType.CONTENT,
                condition=lambda x: isinstance(x, str) and re.search(r'\s{2,}', x),
                action=FilterAction.TRANSFORM,
                description="Normalize excessive whitespace",
                priority=50
            )
        ]
    
    def add_rule(self, rule: FilterRule):
        """Add a new filtering rule"""
        self.config.rules.append(rule)
        self.logger.info(
            "Filter rule added",
            rule_name=rule.name,
            filter_type=rule.filter_type.value,
            action=rule.action.value
        )
    
    def remove_rule(self, rule_name: str):
        """Remove a filtering rule by name"""
        self.config.rules = [rule for rule in self.config.rules if rule.name != rule_name]
        self.logger.info("Filter rule removed", rule_name=rule_name)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get filtering statistics"""
        return {
            'global_stats': self.stats.copy(),
            'active_rules_count': len([rule for rule in self._get_active_rules() if rule.enabled]),
            'total_rules_count': len(self._get_active_rules()),
            'config': {
                'strict_mode': self.config.strict_mode,
                'preserve_structure': self.config.preserve_structure,
                'log_filtered_items': self.config.log_filtered_items
            }
        }