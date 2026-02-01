"""
Data Validation Module

Provides comprehensive data validation capabilities including:
- Schema validation for incoming data
- Format and structure validation
- Business rule enforcement
- Validation middleware for FastAPI
"""

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Type
from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel, ValidationError, validator
import structlog

logger = structlog.get_logger()


class ValidationStatus(Enum):
    """Validation status enumeration"""
    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"


@dataclass
class ValidationError:
    """Validation error details"""
    field: str
    message: str
    code: str
    value: Any = None


@dataclass
class ValidationResult:
    """Result of data validation"""
    status: ValidationStatus
    errors: List[ValidationError]
    warnings: List[ValidationError]
    validated_data: Optional[Dict[str, Any]] = None
    
    @property
    def is_valid(self) -> bool:
        """Check if validation passed"""
        return self.status == ValidationStatus.VALID
    
    @property
    def has_warnings(self) -> bool:
        """Check if validation has warnings"""
        return len(self.warnings) > 0


class BaseDataSchema(BaseModel):
    """Base schema for data validation"""
    
    class Config:
        extra = "forbid"  # Forbid extra fields
        validate_assignment = True
        use_enum_values = True


class TelemetryDataSchema(BaseDataSchema):
    """Schema for telemetry data validation"""
    timestamp: datetime
    source: str
    metric_name: str
    metric_value: Union[int, float, str, Dict[str, Any]]
    tags: Optional[Dict[str, str]] = {}
    
    @validator('source')
    def validate_source(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Source cannot be empty')
        if len(v) > 100:
            raise ValueError('Source name too long (max 100 characters)')
        return v.strip()
    
    @validator('metric_name')
    def validate_metric_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Metric name cannot be empty')
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_.-]*$', v):
            raise ValueError('Invalid metric name format')
        return v.strip()


class PerformanceDataSchema(BaseDataSchema):
    """Schema for performance data validation"""
    service_name: str
    metric_type: str
    value: float
    unit: str
    timestamp: datetime
    
    @validator('value')
    def validate_value(cls, v):
        if v < 0:
            raise ValueError('Performance values cannot be negative')
        return v
    
    @validator('unit')
    def validate_unit(cls, v):
        allowed_units = ['ms', 's', 'bytes', 'kb', 'mb', 'gb', 'percent', 'count']
        if v.lower() not in allowed_units:
            raise ValueError(f'Invalid unit. Allowed: {allowed_units}')
        return v.lower()


class UserDataSchema(BaseDataSchema):
    """Schema for user data validation"""
    username: str
    email: str
    identity_provider: str
    external_id: str
    
    @validator('email')
    def validate_email(cls, v):
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v.lower()
    
    @validator('identity_provider')
    def validate_provider(cls, v):
        allowed_providers = ['github', 'gitlab', 'google', 'microsoft']
        if v.lower() not in allowed_providers:
            raise ValueError(f'Invalid identity provider. Allowed: {allowed_providers}')
        return v.lower()


class DataValidator:
    """Comprehensive data validator with schema support"""
    
    def __init__(self):
        self.schemas = {
            'telemetry': TelemetryDataSchema,
            'performance': PerformanceDataSchema,
            'user': UserDataSchema
        }
        self.logger = structlog.get_logger()
    
    def validate_data(self, data: Any, schema_name: Optional[str] = None) -> ValidationResult:
        """
        Validate data against schema or general validation rules
        
        Args:
            data: Data to validate
            schema_name: Optional schema name for specific validation
            
        Returns:
            ValidationResult with validation status and details
        """
        errors = []
        warnings = []
        validated_data = None
        
        try:
            # Basic data structure validation
            if data is None:
                errors.append(ValidationError(
                    field="data",
                    message="Data cannot be None",
                    code="NULL_DATA"
                ))
                return ValidationResult(
                    status=ValidationStatus.INVALID,
                    errors=errors,
                    warnings=warnings
                )
            
            # Schema-specific validation
            if schema_name and schema_name in self.schemas:
                try:
                    schema_class = self.schemas[schema_name]
                    validated_instance = schema_class(**data)
                    validated_data = validated_instance.dict()
                    
                    self.logger.info(
                        "Data validation successful",
                        schema=schema_name,
                        data_keys=list(data.keys()) if isinstance(data, dict) else "non-dict"
                    )
                    
                except ValidationError as e:
                    for error in e.errors():
                        errors.append(ValidationError(
                            field='.'.join(str(loc) for loc in error['loc']),
                            message=error['msg'],
                            code=error['type'],
                            value=error.get('input')
                        ))
                
            else:
                # General validation for unknown schemas
                validated_data = self._general_validation(data, errors, warnings)
            
            # Determine final status
            if errors:
                status = ValidationStatus.INVALID
                self.logger.warning(
                    "Data validation failed",
                    schema=schema_name,
                    error_count=len(errors),
                    warning_count=len(warnings)
                )
            else:
                status = ValidationStatus.VALID
                self.logger.info(
                    "Data validation passed",
                    schema=schema_name,
                    warning_count=len(warnings)
                )
            
            return ValidationResult(
                status=status,
                errors=errors,
                warnings=warnings,
                validated_data=validated_data
            )
            
        except Exception as e:
            self.logger.error(
                "Unexpected error during validation",
                error=str(e),
                schema=schema_name
            )
            errors.append(ValidationError(
                field="validation",
                message=f"Validation error: {str(e)}",
                code="VALIDATION_ERROR"
            ))
            
            return ValidationResult(
                status=ValidationStatus.INVALID,
                errors=errors,
                warnings=warnings
            )
    
    def _general_validation(self, data: Any, errors: List[ValidationError], warnings: List[ValidationError]) -> Any:
        """Perform general validation for unknown data types"""
        
        if isinstance(data, dict):
            # Validate dictionary structure
            if len(data) == 0:
                warnings.append(ValidationError(
                    field="data",
                    message="Empty dictionary received",
                    code="EMPTY_DICT"
                ))
            
            # Check for suspicious keys
            suspicious_keys = ['password', 'secret', 'token', 'key', 'private']
            for key in data.keys():
                if any(suspicious in key.lower() for suspicious in suspicious_keys):
                    warnings.append(ValidationError(
                        field=key,
                        message="Potentially sensitive data detected",
                        code="SENSITIVE_DATA"
                    ))
            
            return data
            
        elif isinstance(data, list):
            # Validate list structure
            if len(data) == 0:
                warnings.append(ValidationError(
                    field="data",
                    message="Empty list received",
                    code="EMPTY_LIST"
                ))
            
            # Validate list items
            validated_items = []
            for i, item in enumerate(data):
                item_result = self._general_validation(item, [], [])
                validated_items.append(item_result)
            
            return validated_items
            
        elif isinstance(data, str):
            # String validation
            if len(data.strip()) == 0:
                warnings.append(ValidationError(
                    field="data",
                    message="Empty string received",
                    code="EMPTY_STRING"
                ))
            
            # Check for potential injection attacks
            suspicious_patterns = [
                r'<script.*?>.*?</script>',  # XSS
                r'union\s+select',  # SQL injection
                r'javascript:',  # JavaScript injection
                r'data:text/html',  # Data URI XSS
            ]
            
            for pattern in suspicious_patterns:
                if re.search(pattern, data, re.IGNORECASE):
                    errors.append(ValidationError(
                        field="data",
                        message="Potentially malicious content detected",
                        code="MALICIOUS_CONTENT"
                    ))
                    break
            
            return data.strip()
            
        else:
            # Other data types
            return data
    
    def register_schema(self, name: str, schema_class: Type[BaseModel]):
        """Register a new validation schema"""
        self.schemas[name] = schema_class
        self.logger.info("Schema registered", schema_name=name)


# FastAPI Middleware for automatic validation
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class ValidationMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for automatic data validation"""
    
    def __init__(self, app, validator: DataValidator = None):
        super().__init__(app)
        self.validator = validator or DataValidator()
        self.logger = structlog.get_logger()
    
    async def dispatch(self, request: Request, call_next):
        """Process request with validation"""
        
        # Skip validation for certain endpoints
        skip_paths = ['/health', '/docs', '/redoc', '/openapi.json']
        if any(request.url.path.startswith(path) for path in skip_paths):
            return await call_next(request)
        
        # Skip validation for GET requests
        if request.method == 'GET':
            return await call_next(request)
        
        try:
            # Read request body for validation
            body = await request.body()
            if body:
                try:
                    data = json.loads(body)
                    
                    # Determine schema based on endpoint
                    schema_name = self._determine_schema(request.url.path)
                    
                    # Validate data
                    validation_result = self.validator.validate_data(data, schema_name)
                    
                    if not validation_result.is_valid:
                        self.logger.warning(
                            "Request validation failed",
                            path=request.url.path,
                            errors=[error.__dict__ for error in validation_result.errors]
                        )
                        
                        return JSONResponse(
                            status_code=400,
                            content={
                                "error": "Validation failed",
                                "details": [
                                    {
                                        "field": error.field,
                                        "message": error.message,
                                        "code": error.code
                                    }
                                    for error in validation_result.errors
                                ],
                                "timestamp": datetime.utcnow().isoformat()
                            }
                        )
                    
                    # Log warnings if any
                    if validation_result.has_warnings:
                        self.logger.info(
                            "Request validation passed with warnings",
                            path=request.url.path,
                            warnings=[warning.__dict__ for warning in validation_result.warnings]
                        )
                
                except json.JSONDecodeError:
                    self.logger.warning(
                        "Invalid JSON in request body",
                        path=request.url.path
                    )
                    return JSONResponse(
                        status_code=400,
                        content={
                            "error": "Invalid JSON format",
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
            
            # Continue with request processing
            response = await call_next(request)
            return response
            
        except Exception as e:
            self.logger.error(
                "Validation middleware error",
                error=str(e),
                path=request.url.path
            )
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal validation error",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
    
    def _determine_schema(self, path: str) -> Optional[str]:
        """Determine validation schema based on request path"""
        if '/telemetry' in path:
            return 'telemetry'
        elif '/performance' in path or '/metrics' in path:
            return 'performance'
        elif '/user' in path or '/auth' in path:
            return 'user'
        return None