"""
Utility functions for the integration app.
Provides data import/export utilities and external system connectors.
"""

import json
import csv
import xml.etree.ElementTree as ET
import yaml
import logging
import requests
import time
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings

from .models import (
    ExternalSystem, DataConnector, DataImportExportJob, 
    IntegrationLog, ServiceDiscovery
)

logger = logging.getLogger(__name__)


class DataTransformationEngine:
    """Engine for transforming data between different formats and applying rules."""
    
    @staticmethod
    def apply_transformation_rules(data: Any, rules: List[Dict[str, Any]]) -> Any:
        """Apply transformation rules to data."""
        transformed_data = data
        
        for rule in rules:
            rule_type = rule.get('type')
            
            if rule_type == 'field_mapping':
                transformed_data = DataTransformationEngine._apply_field_mapping(
                    transformed_data, rule.get('mapping', {})
                )
            elif rule_type == 'data_type_conversion':
                transformed_data = DataTransformationEngine._apply_type_conversion(
                    transformed_data, rule.get('conversions', {})
                )
            elif rule_type == 'value_transformation':
                transformed_data = DataTransformationEngine._apply_value_transformation(
                    transformed_data, rule.get('transformations', {})
                )
            elif rule_type == 'filtering':
                transformed_data = DataTransformationEngine._apply_filtering(
                    transformed_data, rule.get('filters', {})
                )
        
        return transformed_data
    
    @staticmethod
    def _apply_field_mapping(data: Any, mapping: Dict[str, str]) -> Any:
        """Apply field mapping transformations."""
        if isinstance(data, dict):
            mapped_data = {}
            for old_key, new_key in mapping.items():
                if old_key in data:
                    mapped_data[new_key] = data[old_key]
            # Keep unmapped fields
            for key, value in data.items():
                if key not in mapping:
                    mapped_data[key] = value
            return mapped_data
        elif isinstance(data, list):
            return [DataTransformationEngine._apply_field_mapping(item, mapping) for item in data]
        return data
    
    @staticmethod
    def _apply_type_conversion(data: Any, conversions: Dict[str, str]) -> Any:
        """Apply data type conversions."""
        if isinstance(data, dict):
            converted_data = {}
            for key, value in data.items():
                if key in conversions:
                    target_type = conversions[key]
                    try:
                        if target_type == 'int':
                            converted_data[key] = int(value)
                        elif target_type == 'float':
                            converted_data[key] = float(value)
                        elif target_type == 'str':
                            converted_data[key] = str(value)
                        elif target_type == 'bool':
                            converted_data[key] = bool(value)
                        elif target_type == 'datetime':
                            converted_data[key] = datetime.fromisoformat(str(value))
                        else:
                            converted_data[key] = value
                    except (ValueError, TypeError):
                        converted_data[key] = value  # Keep original if conversion fails
                else:
                    converted_data[key] = value
            return converted_data
        elif isinstance(data, list):
            return [DataTransformationEngine._apply_type_conversion(item, conversions) for item in data]
        return data
    
    @staticmethod
    def _apply_value_transformation(data: Any, transformations: Dict[str, Dict[str, Any]]) -> Any:
        """Apply value transformations like regex replacements, calculations, etc."""
        if isinstance(data, dict):
            transformed_data = {}
            for key, value in data.items():
                if key in transformations:
                    transform_config = transformations[key]
                    transform_type = transform_config.get('type')
                    
                    if transform_type == 'regex_replace':
                        import re
                        pattern = transform_config.get('pattern', '')
                        replacement = transform_config.get('replacement', '')
                        transformed_data[key] = re.sub(pattern, replacement, str(value))
                    elif transform_type == 'calculation':
                        # Simple calculation support
                        formula = transform_config.get('formula', '')
                        try:
                            # Basic safety check - only allow simple math operations
                            if all(c in '0123456789+-*/.() ' or c.isalpha() for c in formula):
                                transformed_data[key] = eval(formula.replace('value', str(value)))
                            else:
                                transformed_data[key] = value
                        except:
                            transformed_data[key] = value
                    else:
                        transformed_data[key] = value
                else:
                    transformed_data[key] = value
            return transformed_data
        elif isinstance(data, list):
            return [DataTransformationEngine._apply_value_transformation(item, transformations) for item in data]
        return data
    
    @staticmethod
    def _apply_filtering(data: Any, filters: Dict[str, Any]) -> Any:
        """Apply filtering rules to data."""
        if isinstance(data, list):
            filtered_data = []
            for item in data:
                if DataTransformationEngine._matches_filters(item, filters):
                    filtered_data.append(item)
            return filtered_data
        elif isinstance(data, dict):
            if DataTransformationEngine._matches_filters(data, filters):
                return data
            else:
                return None
        return data
    
    @staticmethod
    def _matches_filters(item: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if an item matches the filter criteria."""
        for field, criteria in filters.items():
            if field not in item:
                return False
            
            value = item[field]
            operator = criteria.get('operator', 'equals')
            filter_value = criteria.get('value')
            
            if operator == 'equals' and value != filter_value:
                return False
            elif operator == 'not_equals' and value == filter_value:
                return False
            elif operator == 'greater_than' and value <= filter_value:
                return False
            elif operator == 'less_than' and value >= filter_value:
                return False
            elif operator == 'contains' and filter_value not in str(value):
                return False
            elif operator == 'not_contains' and filter_value in str(value):
                return False
        
        return True


class DataFormatConverter:
    """Converter for different data formats (JSON, XML, CSV, YAML)."""
    
    @staticmethod
    def convert_to_format(data: Any, target_format: str) -> str:
        """Convert data to the specified format."""
        if target_format.lower() == 'json':
            return json.dumps(data, indent=2, default=str)
        elif target_format.lower() == 'xml':
            return DataFormatConverter._dict_to_xml(data)
        elif target_format.lower() == 'csv':
            return DataFormatConverter._dict_to_csv(data)
        elif target_format.lower() == 'yaml':
            return yaml.dump(data, default_flow_style=False)
        else:
            return str(data)
    
    @staticmethod
    def parse_from_format(data_str: str, source_format: str) -> Any:
        """Parse data from the specified format."""
        if source_format.lower() == 'json':
            return json.loads(data_str)
        elif source_format.lower() == 'xml':
            return DataFormatConverter._xml_to_dict(data_str)
        elif source_format.lower() == 'csv':
            return DataFormatConverter._csv_to_dict(data_str)
        elif source_format.lower() == 'yaml':
            return yaml.safe_load(data_str)
        else:
            return data_str
    
    @staticmethod
    def _dict_to_xml(data: Dict[str, Any], root_name: str = 'root') -> str:
        """Convert dictionary to XML string."""
        root = ET.Element(root_name)
        DataFormatConverter._dict_to_xml_element(data, root)
        return ET.tostring(root, encoding='unicode')
    
    @staticmethod
    def _dict_to_xml_element(data: Any, parent: ET.Element):
        """Recursively convert dictionary to XML elements."""
        if isinstance(data, dict):
            for key, value in data.items():
                child = ET.SubElement(parent, str(key))
                DataFormatConverter._dict_to_xml_element(value, child)
        elif isinstance(data, list):
            for item in data:
                child = ET.SubElement(parent, 'item')
                DataFormatConverter._dict_to_xml_element(item, child)
        else:
            parent.text = str(data)
    
    @staticmethod
    def _xml_to_dict(xml_str: str) -> Dict[str, Any]:
        """Convert XML string to dictionary."""
        root = ET.fromstring(xml_str)
        return {root.tag: DataFormatConverter._xml_element_to_dict(root)}
    
    @staticmethod
    def _xml_element_to_dict(element: ET.Element) -> Any:
        """Recursively convert XML element to dictionary."""
        result = {}
        
        # Handle attributes
        if element.attrib:
            result.update(element.attrib)
        
        # Handle children
        children = list(element)
        if children:
            child_dict = {}
            for child in children:
                child_data = DataFormatConverter._xml_element_to_dict(child)
                if child.tag in child_dict:
                    if not isinstance(child_dict[child.tag], list):
                        child_dict[child.tag] = [child_dict[child.tag]]
                    child_dict[child.tag].append(child_data)
                else:
                    child_dict[child.tag] = child_data
            result.update(child_dict)
        
        # Handle text content
        if element.text and element.text.strip():
            if result:
                result['text'] = element.text.strip()
            else:
                return element.text.strip()
        
        return result if result else None
    
    @staticmethod
    def _dict_to_csv(data: Any) -> str:
        """Convert dictionary or list of dictionaries to CSV string."""
        import io
        output = io.StringIO()
        
        if isinstance(data, list) and data and isinstance(data[0], dict):
            # List of dictionaries
            fieldnames = data[0].keys()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        elif isinstance(data, dict):
            # Single dictionary
            fieldnames = data.keys()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow(data)
        else:
            # Fallback to simple string representation
            output.write(str(data))
        
        return output.getvalue()
    
    @staticmethod
    def _csv_to_dict(csv_str: str) -> List[Dict[str, Any]]:
        """Convert CSV string to list of dictionaries."""
        import io
        input_stream = io.StringIO(csv_str)
        reader = csv.DictReader(input_stream)
        return list(reader)


class ExternalSystemConnector:
    """Connector for communicating with external systems."""
    
    def __init__(self, external_system: ExternalSystem):
        self.external_system = external_system
        self.session = requests.Session()
        self._setup_authentication()
    
    def _setup_authentication(self):
        """Setup authentication for the external system."""
        auth_type = self.external_system.auth_type
        auth_config = self.external_system.auth_config
        
        if auth_type == 'api_key':
            api_key = auth_config.get('api_key')
            header_name = auth_config.get('header_name', 'X-API-Key')
            self.session.headers[header_name] = api_key
        elif auth_type == 'bearer_token':
            token = auth_config.get('token')
            self.session.headers['Authorization'] = f'Bearer {token}'
        elif auth_type == 'basic_auth':
            username = auth_config.get('username')
            password = auth_config.get('password')
            self.session.auth = (username, password)
        elif auth_type == 'oauth2':
            # OAuth2 would require more complex implementation
            # This is a placeholder for future enhancement
            pass
    
    def test_connection(self) -> Dict[str, Any]:
        """Test connection to the external system."""
        try:
            health_url = self.external_system.health_check_url or self.external_system.base_url
            if not health_url:
                return {'success': False, 'error': 'No URL configured for health check'}
            
            start_time = time.time()
            response = self.session.get(
                health_url,
                timeout=self.external_system.timeout_seconds
            )
            duration = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            success = response.status_code < 400
            
            # Log the connection test
            IntegrationLog.objects.create(
                external_system=self.external_system,
                level='INFO' if success else 'ERROR',
                activity_type='connection',
                message=f'Connection test {"successful" if success else "failed"}',
                details={
                    'status_code': response.status_code,
                    'response_time_ms': duration,
                    'url': health_url
                },
                duration_ms=int(duration)
            )
            
            return {
                'success': success,
                'status_code': response.status_code,
                'response_time_ms': duration,
                'message': 'Connection successful' if success else f'HTTP {response.status_code}'
            }
            
        except requests.exceptions.Timeout:
            IntegrationLog.objects.create(
                external_system=self.external_system,
                level='ERROR',
                activity_type='connection',
                message='Connection test timed out',
                details={'timeout_seconds': self.external_system.timeout_seconds}
            )
            return {'success': False, 'error': 'Connection timeout'}
        except requests.exceptions.ConnectionError:
            IntegrationLog.objects.create(
                external_system=self.external_system,
                level='ERROR',
                activity_type='connection',
                message='Connection failed',
                details={'error': 'Connection error'}
            )
            return {'success': False, 'error': 'Connection failed'}
        except Exception as e:
            IntegrationLog.objects.create(
                external_system=self.external_system,
                level='ERROR',
                activity_type='connection',
                message=f'Connection test error: {str(e)}',
                details={'error': str(e)}
            )
            return {'success': False, 'error': str(e)}
    
    def fetch_data(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Fetch data from the external system."""
        try:
            url = f"{self.external_system.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
            
            start_time = time.time()
            response = self.session.get(
                url,
                params=params,
                timeout=self.external_system.timeout_seconds
            )
            duration = (time.time() - start_time) * 1000
            
            success = response.status_code < 400
            
            # Log the data fetch
            IntegrationLog.objects.create(
                external_system=self.external_system,
                level='INFO' if success else 'ERROR',
                activity_type='data_transfer',
                message=f'Data fetch {"successful" if success else "failed"}',
                details={
                    'endpoint': endpoint,
                    'status_code': response.status_code,
                    'response_time_ms': duration,
                    'params': params
                },
                duration_ms=int(duration)
            )
            
            if success:
                try:
                    data = response.json()
                    return {'success': True, 'data': data}
                except json.JSONDecodeError:
                    return {'success': True, 'data': response.text}
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'message': response.text
                }
                
        except Exception as e:
            IntegrationLog.objects.create(
                external_system=self.external_system,
                level='ERROR',
                activity_type='data_transfer',
                message=f'Data fetch error: {str(e)}',
                details={'endpoint': endpoint, 'error': str(e)}
            )
            return {'success': False, 'error': str(e)}
    
    def send_data(self, endpoint: str, data: Any, method: str = 'POST') -> Dict[str, Any]:
        """Send data to the external system."""
        try:
            url = f"{self.external_system.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
            
            start_time = time.time()
            
            if method.upper() == 'POST':
                response = self.session.post(
                    url,
                    json=data,
                    timeout=self.external_system.timeout_seconds
                )
            elif method.upper() == 'PUT':
                response = self.session.put(
                    url,
                    json=data,
                    timeout=self.external_system.timeout_seconds
                )
            elif method.upper() == 'PATCH':
                response = self.session.patch(
                    url,
                    json=data,
                    timeout=self.external_system.timeout_seconds
                )
            else:
                return {'success': False, 'error': f'Unsupported method: {method}'}
            
            duration = (time.time() - start_time) * 1000
            success = response.status_code < 400
            
            # Log the data send
            IntegrationLog.objects.create(
                external_system=self.external_system,
                level='INFO' if success else 'ERROR',
                activity_type='data_transfer',
                message=f'Data send {"successful" if success else "failed"}',
                details={
                    'endpoint': endpoint,
                    'method': method,
                    'status_code': response.status_code,
                    'response_time_ms': duration
                },
                duration_ms=int(duration)
            )
            
            if success:
                try:
                    response_data = response.json()
                    return {'success': True, 'data': response_data}
                except json.JSONDecodeError:
                    return {'success': True, 'data': response.text}
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'message': response.text
                }
                
        except Exception as e:
            IntegrationLog.objects.create(
                external_system=self.external_system,
                level='ERROR',
                activity_type='data_transfer',
                message=f'Data send error: {str(e)}',
                details={'endpoint': endpoint, 'method': method, 'error': str(e)}
            )
            return {'success': False, 'error': str(e)}


class ServiceDiscoveryManager:
    """Manager for service discovery and load balancing."""
    
    @staticmethod
    def register_service(service_config: Dict[str, Any]) -> ServiceDiscovery:
        """Register a service instance."""
        service, created = ServiceDiscovery.objects.update_or_create(
            service_name=service_config['service_name'],
            instance_id=service_config['instance_id'],
            defaults={
                'service_type': service_config['service_type'],
                'host': service_config['host'],
                'port': service_config['port'],
                'protocol': service_config.get('protocol', 'http'),
                'base_path': service_config.get('base_path', '/'),
                'version': service_config['version'],
                'environment': service_config.get('environment', 'development'),
                'region': service_config.get('region', ''),
                'availability_zone': service_config.get('availability_zone', ''),
                'health_check_url': service_config.get('health_check_url', ''),
                'weight': service_config.get('weight', 100),
                'max_connections': service_config.get('max_connections', 1000),
                'health_status': 'healthy',
            }
        )
        
        logger.info(f"Service {'registered' if created else 'updated'}: {service.service_name}:{service.instance_id}")
        return service
    
    @staticmethod
    def get_healthy_instances(service_name: str, environment: Optional[str] = None) -> List[ServiceDiscovery]:
        """Get healthy instances for a service."""
        queryset = ServiceDiscovery.objects.filter(
            service_name=service_name,
            is_active=True,
            health_status='healthy'
        )
        
        if environment:
            queryset = queryset.filter(environment=environment)
        
        # Order by weight (higher weight first) and current connections (lower first)
        return list(queryset.order_by('-weight', 'current_connections'))
    
    @staticmethod
    def select_instance(service_name: str, environment: Optional[str] = None) -> Optional[ServiceDiscovery]:
        """Select the best available instance using weighted round-robin."""
        instances = ServiceDiscoveryManager.get_healthy_instances(service_name, environment)
        
        if not instances:
            return None
        
        # Simple weighted selection - choose instance with highest weight and lowest connections
        best_instance = None
        best_score = -1
        
        for instance in instances:
            # Calculate score based on weight and current load
            load_factor = instance.current_connections / instance.max_connections if instance.max_connections > 0 else 0
            score = instance.weight * (1 - load_factor)
            
            if score > best_score:
                best_score = score
                best_instance = instance
        
        return best_instance
    
    @staticmethod
    def update_instance_health(instance_id: str, health_status: str, current_connections: Optional[int] = None):
        """Update instance health status."""
        try:
            instance = ServiceDiscovery.objects.get(instance_id=instance_id, is_active=True)
            instance.health_status = health_status
            instance.last_health_check = timezone.now()
            
            if current_connections is not None:
                instance.current_connections = current_connections
            
            instance.save()
            logger.info(f"Updated health status for {instance.service_name}:{instance_id} to {health_status}")
            
        except ServiceDiscovery.DoesNotExist:
            logger.warning(f"Service instance not found: {instance_id}")
    
    @staticmethod
    def cleanup_stale_instances(stale_threshold_minutes: int = 10):
        """Remove instances that haven't sent heartbeats recently."""
        threshold_time = timezone.now() - timedelta(minutes=stale_threshold_minutes)
        
        stale_instances = ServiceDiscovery.objects.filter(
            is_active=True,
            last_heartbeat__lt=threshold_time
        )
        
        count = stale_instances.count()
        if count > 0:
            stale_instances.update(is_active=False, health_status='unknown')
            logger.info(f"Marked {count} stale service instances as inactive")


class DataValidationEngine:
    """Engine for validating data against defined rules."""
    
    @staticmethod
    def validate_data(data: Any, validation_rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate data against validation rules."""
        errors = []
        warnings = []
        
        for rule in validation_rules:
            rule_type = rule.get('type')
            
            if rule_type == 'required_fields':
                field_errors = DataValidationEngine._validate_required_fields(data, rule.get('fields', []))
                errors.extend(field_errors)
            elif rule_type == 'data_types':
                type_errors = DataValidationEngine._validate_data_types(data, rule.get('types', {}))
                errors.extend(type_errors)
            elif rule_type == 'value_ranges':
                range_errors = DataValidationEngine._validate_value_ranges(data, rule.get('ranges', {}))
                errors.extend(range_errors)
            elif rule_type == 'format_validation':
                format_errors = DataValidationEngine._validate_formats(data, rule.get('formats', {}))
                errors.extend(format_errors)
            elif rule_type == 'business_rules':
                business_errors = DataValidationEngine._validate_business_rules(data, rule.get('rules', []))
                errors.extend(business_errors)
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    @staticmethod
    def _validate_required_fields(data: Any, required_fields: List[str]) -> List[str]:
        """Validate that required fields are present."""
        errors = []
        
        if isinstance(data, dict):
            for field in required_fields:
                if field not in data or data[field] is None:
                    errors.append(f"Required field '{field}' is missing or null")
        elif isinstance(data, list):
            for i, item in enumerate(data):
                item_errors = DataValidationEngine._validate_required_fields(item, required_fields)
                errors.extend([f"Item {i}: {error}" for error in item_errors])
        
        return errors
    
    @staticmethod
    def _validate_data_types(data: Any, type_definitions: Dict[str, str]) -> List[str]:
        """Validate data types."""
        errors = []
        
        if isinstance(data, dict):
            for field, expected_type in type_definitions.items():
                if field in data:
                    value = data[field]
                    if not DataValidationEngine._check_type(value, expected_type):
                        errors.append(f"Field '{field}' should be of type {expected_type}, got {type(value).__name__}")
        elif isinstance(data, list):
            for i, item in enumerate(data):
                item_errors = DataValidationEngine._validate_data_types(item, type_definitions)
                errors.extend([f"Item {i}: {error}" for error in item_errors])
        
        return errors
    
    @staticmethod
    def _check_type(value: Any, expected_type: str) -> bool:
        """Check if value matches expected type."""
        type_map = {
            'string': str,
            'integer': int,
            'float': float,
            'boolean': bool,
            'list': list,
            'dict': dict
        }
        
        expected_python_type = type_map.get(expected_type.lower())
        if expected_python_type:
            return isinstance(value, expected_python_type)
        
        return True  # Unknown type, assume valid
    
    @staticmethod
    def _validate_value_ranges(data: Any, range_definitions: Dict[str, Dict[str, Any]]) -> List[str]:
        """Validate value ranges."""
        errors = []
        
        if isinstance(data, dict):
            for field, range_config in range_definitions.items():
                if field in data:
                    value = data[field]
                    min_val = range_config.get('min')
                    max_val = range_config.get('max')
                    
                    if min_val is not None and value < min_val:
                        errors.append(f"Field '{field}' value {value} is below minimum {min_val}")
                    if max_val is not None and value > max_val:
                        errors.append(f"Field '{field}' value {value} is above maximum {max_val}")
        elif isinstance(data, list):
            for i, item in enumerate(data):
                item_errors = DataValidationEngine._validate_value_ranges(item, range_definitions)
                errors.extend([f"Item {i}: {error}" for error in item_errors])
        
        return errors
    
    @staticmethod
    def _validate_formats(data: Any, format_definitions: Dict[str, str]) -> List[str]:
        """Validate data formats using regex patterns."""
        import re
        errors = []
        
        if isinstance(data, dict):
            for field, pattern in format_definitions.items():
                if field in data:
                    value = str(data[field])
                    if not re.match(pattern, value):
                        errors.append(f"Field '{field}' value '{value}' does not match required format")
        elif isinstance(data, list):
            for i, item in enumerate(data):
                item_errors = DataValidationEngine._validate_formats(item, format_definitions)
                errors.extend([f"Item {i}: {error}" for error in item_errors])
        
        return errors
    
    @staticmethod
    def _validate_business_rules(data: Any, business_rules: List[Dict[str, Any]]) -> List[str]:
        """Validate custom business rules."""
        errors = []
        
        for rule in business_rules:
            rule_name = rule.get('name', 'Unknown rule')
            condition = rule.get('condition', '')
            error_message = rule.get('error_message', f'Business rule violation: {rule_name}')
            
            try:
                # Simple condition evaluation - in production, this should be more secure
                if isinstance(data, dict):
                    # Replace field references with actual values
                    eval_condition = condition
                    for field, value in data.items():
                        eval_condition = eval_condition.replace(f'data.{field}', str(value))
                    
                    # Basic safety check
                    if all(c in '0123456789+-*/.()< >= != and or not ' or c.isalpha() or c == '_' for c in eval_condition):
                        if not eval(eval_condition):
                            errors.append(error_message)
            except:
                # If evaluation fails, skip the rule
                pass
        
        return errors