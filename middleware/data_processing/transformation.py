"""
Data Transformation Module

Provides comprehensive data transformation and normalization capabilities including:
- Data format standardization
- Unit conversion and normalization
- Data type transformation
- Polymorphic data handling
"""

import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import numpy as np
import structlog

logger = structlog.get_logger()


class DataType(Enum):
    """Supported data types for transformation"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    JSON = "json"
    LIST = "list"
    DICT = "dict"


@dataclass
class NormalizedData:
    """Container for normalized data with metadata"""
    data: Any
    original_type: str
    normalized_type: str
    transformations_applied: List[str]
    metadata: Dict[str, Any]
    timestamp: datetime


class DataTransformer:
    """Comprehensive data transformer with normalization capabilities"""
    
    def __init__(self):
        self.logger = structlog.get_logger()
        self.unit_conversions = self._initialize_unit_conversions()
        self.format_patterns = self._initialize_format_patterns()
    
    def normalize_data(self, data: Any, target_format: Optional[str] = None) -> NormalizedData:
        """
        Normalize data to consistent formats and units
        
        Args:
            data: Input data to normalize
            target_format: Optional target format specification
            
        Returns:
            NormalizedData with normalized content and metadata
        """
        original_type = type(data).__name__
        transformations = []
        metadata = {}
        
        try:
            # Detect data type and apply appropriate normalization
            if isinstance(data, dict):
                normalized_data, dict_transformations = self._normalize_dict(data)
                transformations.extend(dict_transformations)
                normalized_type = "dict"
                
            elif isinstance(data, list):
                normalized_data, list_transformations = self._normalize_list(data)
                transformations.extend(list_transformations)
                normalized_type = "list"
                
            elif isinstance(data, str):
                normalized_data, str_transformations = self._normalize_string(data, target_format)
                transformations.extend(str_transformations)
                normalized_type = "string"
                
            elif isinstance(data, (int, float)):
                normalized_data, num_transformations = self._normalize_number(data, target_format)
                transformations.extend(num_transformations)
                normalized_type = "number"
                
            elif isinstance(data, bool):
                normalized_data = data
                normalized_type = "boolean"
                
            elif isinstance(data, datetime):
                normalized_data, dt_transformations = self._normalize_datetime(data)
                transformations.extend(dt_transformations)
                normalized_type = "datetime"
                
            else:
                # Handle other types by converting to string
                normalized_data = str(data)
                transformations.append("converted_to_string")
                normalized_type = "string"
            
            # Add metadata about the transformation
            metadata = {
                "original_size": self._calculate_size(data),
                "normalized_size": self._calculate_size(normalized_data),
                "complexity_score": self._calculate_complexity(data),
                "transformation_count": len(transformations)
            }
            
            self.logger.info(
                "Data normalization completed",
                original_type=original_type,
                normalized_type=normalized_type,
                transformations=transformations,
                metadata=metadata
            )
            
            return NormalizedData(
                data=normalized_data,
                original_type=original_type,
                normalized_type=normalized_type,
                transformations_applied=transformations,
                metadata=metadata,
                timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            self.logger.error(
                "Data normalization failed",
                error=str(e),
                original_type=original_type,
                data_preview=str(data)[:100] if data else None
            )
            
            # Return original data with error metadata
            return NormalizedData(
                data=data,
                original_type=original_type,
                normalized_type=original_type,
                transformations_applied=["normalization_failed"],
                metadata={"error": str(e)},
                timestamp=datetime.now(timezone.utc)
            )
    
    def _normalize_dict(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """Normalize dictionary data"""
        normalized = {}
        transformations = []
        
        for key, value in data.items():
            # Normalize key names
            normalized_key = self._normalize_key_name(key)
            if normalized_key != key:
                transformations.append(f"key_normalized_{key}_to_{normalized_key}")
            
            # Recursively normalize values
            if isinstance(value, (dict, list)):
                normalized_value = self.normalize_data(value)
                normalized[normalized_key] = normalized_value.data
                transformations.extend([f"nested_{t}" for t in normalized_value.transformations_applied])
            else:
                normalized_value = self.normalize_data(value)
                normalized[normalized_key] = normalized_value.data
                transformations.extend([f"value_{t}" for t in normalized_value.transformations_applied])
        
        # Sort keys for consistency
        normalized = dict(sorted(normalized.items()))
        transformations.append("keys_sorted")
        
        return normalized, transformations
    
    def _normalize_list(self, data: List[Any]) -> Tuple[List[Any], List[str]]:
        """Normalize list data"""
        normalized = []
        transformations = []
        
        for i, item in enumerate(data):
            normalized_item = self.normalize_data(item)
            normalized.append(normalized_item.data)
            transformations.extend([f"item_{i}_{t}" for t in normalized_item.transformations_applied])
        
        # Remove duplicates if they exist
        if len(normalized) != len(set(str(item) for item in normalized)):
            transformations.append("duplicates_detected")
        
        return normalized, transformations
    
    def _normalize_string(self, data: str, target_format: Optional[str] = None) -> Tuple[str, List[str]]:
        """Normalize string data"""
        normalized = data
        transformations = []
        
        # Basic string cleaning
        if normalized != normalized.strip():
            normalized = normalized.strip()
            transformations.append("whitespace_trimmed")
        
        # Normalize line endings
        if '\r\n' in normalized or '\r' in normalized:
            normalized = normalized.replace('\r\n', '\n').replace('\r', '\n')
            transformations.append("line_endings_normalized")
        
        # Handle specific format requirements
        if target_format:
            if target_format.lower() == 'email':
                normalized = normalized.lower()
                transformations.append("email_lowercased")
            elif target_format.lower() == 'url':
                normalized = normalized.lower().rstrip('/')
                transformations.append("url_normalized")
            elif target_format.lower() == 'phone':
                normalized = re.sub(r'[^\d+]', '', normalized)
                transformations.append("phone_digits_only")
        
        # Detect and normalize common patterns
        if self._is_json_string(normalized):
            try:
                parsed = json.loads(normalized)
                normalized = json.dumps(parsed, sort_keys=True, separators=(',', ':'))
                transformations.append("json_normalized")
            except json.JSONDecodeError:
                pass
        
        # Normalize unicode
        if normalized != normalized.encode('utf-8', 'ignore').decode('utf-8'):
            normalized = normalized.encode('utf-8', 'ignore').decode('utf-8')
            transformations.append("unicode_normalized")
        
        return normalized, transformations
    
    def _normalize_number(self, data: Union[int, float], target_format: Optional[str] = None) -> Tuple[Union[int, float], List[str]]:
        """Normalize numeric data"""
        normalized = data
        transformations = []
        
        # Handle unit conversions if target format specified
        if target_format and isinstance(data, (int, float)):
            if target_format in self.unit_conversions:
                conversion_factor = self.unit_conversions[target_format]
                normalized = data * conversion_factor
                transformations.append(f"unit_converted_to_{target_format}")
        
        # Normalize precision for floats
        if isinstance(normalized, float):
            # Round to reasonable precision (6 decimal places)
            rounded = round(normalized, 6)
            if rounded != normalized:
                normalized = rounded
                transformations.append("precision_normalized")
            
            # Convert to int if it's a whole number
            if normalized.is_integer():
                normalized = int(normalized)
                transformations.append("converted_to_integer")
        
        # Handle special float values
        if isinstance(normalized, float):
            if np.isnan(normalized):
                normalized = None
                transformations.append("nan_to_null")
            elif np.isinf(normalized):
                normalized = None
                transformations.append("inf_to_null")
        
        return normalized, transformations
    
    def _normalize_datetime(self, data: datetime) -> Tuple[str, List[str]]:
        """Normalize datetime data"""
        transformations = []
        
        # Ensure timezone awareness
        if data.tzinfo is None:
            data = data.replace(tzinfo=timezone.utc)
            transformations.append("timezone_added_utc")
        
        # Convert to UTC
        if data.tzinfo != timezone.utc:
            data = data.astimezone(timezone.utc)
            transformations.append("converted_to_utc")
        
        # Normalize to ISO format
        normalized = data.isoformat()
        transformations.append("iso_format")
        
        return normalized, transformations
    
    def _normalize_key_name(self, key: str) -> str:
        """Normalize dictionary key names"""
        # Convert to snake_case
        normalized = re.sub(r'([A-Z])', r'_\1', key).lower()
        normalized = re.sub(r'[^a-z0-9_]', '_', normalized)
        normalized = re.sub(r'_+', '_', normalized)
        normalized = normalized.strip('_')
        
        return normalized or key  # Return original if normalization results in empty string
    
    def _is_json_string(self, data: str) -> bool:
        """Check if string contains JSON data"""
        data = data.strip()
        return (data.startswith('{') and data.endswith('}')) or \
               (data.startswith('[') and data.endswith(']'))
    
    def _calculate_size(self, data: Any) -> int:
        """Calculate approximate size of data"""
        try:
            if isinstance(data, str):
                return len(data.encode('utf-8'))
            elif isinstance(data, (list, dict)):
                return len(str(data).encode('utf-8'))
            else:
                return len(str(data).encode('utf-8'))
        except:
            return 0
    
    def _calculate_complexity(self, data: Any) -> int:
        """Calculate complexity score of data structure"""
        if isinstance(data, dict):
            return len(data) + sum(self._calculate_complexity(v) for v in data.values())
        elif isinstance(data, list):
            return len(data) + sum(self._calculate_complexity(item) for item in data)
        else:
            return 1
    
    def _initialize_unit_conversions(self) -> Dict[str, float]:
        """Initialize unit conversion factors"""
        return {
            # Time conversions (to milliseconds)
            'seconds_to_ms': 1000,
            'minutes_to_ms': 60000,
            'hours_to_ms': 3600000,
            
            # Size conversions (to bytes)
            'kb_to_bytes': 1024,
            'mb_to_bytes': 1024 * 1024,
            'gb_to_bytes': 1024 * 1024 * 1024,
            
            # Percentage conversions
            'decimal_to_percent': 100,
            'percent_to_decimal': 0.01,
        }
    
    def _initialize_format_patterns(self) -> Dict[str, str]:
        """Initialize format patterns for validation"""
        return {
            'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'url': r'^https?://[^\s/$.?#].[^\s]*$',
            'ipv4': r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$',
            'uuid': r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
            'phone': r'^\+?[1-9]\d{1,14}$',
        }
    
    def transform_for_polymorphism(self, data: Any) -> Dict[str, Any]:
        """
        Transform data to support polymorphic handling
        
        Args:
            data: Input data of any type
            
        Returns:
            Dictionary with type information and normalized data
        """
        try:
            normalized = self.normalize_data(data)
            
            return {
                'type': normalized.normalized_type,
                'original_type': normalized.original_type,
                'data': normalized.data,
                'metadata': {
                    'transformations': normalized.transformations_applied,
                    'size': normalized.metadata.get('normalized_size', 0),
                    'complexity': normalized.metadata.get('complexity_score', 0),
                    'timestamp': normalized.timestamp.isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(
                "Polymorphic transformation failed",
                error=str(e),
                data_type=type(data).__name__
            )
            
            return {
                'type': 'unknown',
                'original_type': type(data).__name__,
                'data': str(data),
                'metadata': {
                    'transformations': ['polymorphic_fallback'],
                    'error': str(e),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            }
    
    def batch_normalize(self, data_list: List[Any], target_format: Optional[str] = None) -> List[NormalizedData]:
        """
        Normalize a batch of data items efficiently
        
        Args:
            data_list: List of data items to normalize
            target_format: Optional target format for all items
            
        Returns:
            List of NormalizedData objects
        """
        results = []
        
        self.logger.info(
            "Starting batch normalization",
            batch_size=len(data_list),
            target_format=target_format
        )
        
        for i, data in enumerate(data_list):
            try:
                normalized = self.normalize_data(data, target_format)
                results.append(normalized)
            except Exception as e:
                self.logger.error(
                    "Batch normalization item failed",
                    index=i,
                    error=str(e)
                )
                # Add failed item with error metadata
                results.append(NormalizedData(
                    data=data,
                    original_type=type(data).__name__,
                    normalized_type="error",
                    transformations_applied=["batch_normalization_failed"],
                    metadata={"error": str(e), "index": i},
                    timestamp=datetime.now(timezone.utc)
                ))
        
        self.logger.info(
            "Batch normalization completed",
            total_items=len(data_list),
            successful_items=len([r for r in results if r.normalized_type != "error"]),
            failed_items=len([r for r in results if r.normalized_type == "error"])
        )
        
        return results