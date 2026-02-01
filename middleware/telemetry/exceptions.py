"""
Telemetry system exceptions.
Custom exceptions for telemetry collection, processing, and analysis.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime


class TelemetryError(Exception):
    """Base exception for telemetry operations"""
    
    def __init__(
        self,
        message: str,
        error_code: str = "TELEMETRY_ERROR",
        details: Optional[Dict[str, Any]] = None,
        telemetry_id: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.telemetry_id = telemetry_id
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary"""
        return {
            "error": self.message,
            "error_code": self.error_code,
            "details": self.details,
            "telemetry_id": self.telemetry_id,
            "timestamp": self.timestamp.isoformat()
        }


class ValidationError(TelemetryError):
    """Telemetry data validation error"""
    
    def __init__(
        self,
        message: str,
        field_errors: Optional[List[Dict[str, Any]]] = None,
        telemetry_id: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details={"field_errors": field_errors or []},
            telemetry_id=telemetry_id
        )
        self.field_errors = field_errors or []


class ProcessingError(TelemetryError):
    """Telemetry processing error"""
    
    def __init__(
        self,
        message: str,
        processing_stage: str,
        telemetry_id: Optional[str] = None,
        processor_version: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code="PROCESSING_ERROR",
            details={
                "processing_stage": processing_stage,
                "processor_version": processor_version
            },
            telemetry_id=telemetry_id
        )
        self.processing_stage = processing_stage
        self.processor_version = processor_version


class EnrichmentError(TelemetryError):
    """Telemetry enrichment error"""
    
    def __init__(
        self,
        message: str,
        enrichment_source: str,
        telemetry_id: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code="ENRICHMENT_ERROR",
            details={"enrichment_source": enrichment_source},
            telemetry_id=telemetry_id
        )
        self.enrichment_source = enrichment_source


class CorrelationError(TelemetryError):
    """Telemetry correlation error"""
    
    def __init__(
        self,
        message: str,
        correlation_rule_id: Optional[str] = None,
        telemetry_ids: Optional[List[str]] = None
    ):
        super().__init__(
            message=message,
            error_code="CORRELATION_ERROR",
            details={
                "correlation_rule_id": correlation_rule_id,
                "telemetry_ids": telemetry_ids or []
            }
        )
        self.correlation_rule_id = correlation_rule_id
        self.telemetry_ids = telemetry_ids or []


class AnalysisError(TelemetryError):
    """Telemetry analysis error"""
    
    def __init__(
        self,
        message: str,
        analysis_pattern_id: Optional[str] = None,
        telemetry_ids: Optional[List[str]] = None
    ):
        super().__init__(
            message=message,
            error_code="ANALYSIS_ERROR",
            details={
                "analysis_pattern_id": analysis_pattern_id,
                "telemetry_ids": telemetry_ids or []
            }
        )
        self.analysis_pattern_id = analysis_pattern_id
        self.telemetry_ids = telemetry_ids or []


class StorageError(TelemetryError):
    """Telemetry storage error"""
    
    def __init__(
        self,
        message: str,
        storage_backend: str,
        telemetry_id: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code="STORAGE_ERROR",
            details={"storage_backend": storage_backend},
            telemetry_id=telemetry_id
        )
        self.storage_backend = storage_backend


class ConfigurationError(TelemetryError):
    """Telemetry configuration error"""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_value: Optional[Any] = None
    ):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details={
                "config_key": config_key,
                "config_value": config_value
            }
        )
        self.config_key = config_key
        self.config_value = config_value


class RateLimitError(TelemetryError):
    """Telemetry rate limit error"""
    
    def __init__(
        self,
        message: str,
        limit: int,
        window_seconds: int,
        current_rate: float
    ):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            details={
                "limit": limit,
                "window_seconds": window_seconds,
                "current_rate": current_rate
            }
        )
        self.limit = limit
        self.window_seconds = window_seconds
        self.current_rate = current_rate


class TimeoutError(TelemetryError):
    """Telemetry operation timeout error"""
    
    def __init__(
        self,
        message: str,
        operation: str,
        timeout_seconds: float,
        telemetry_id: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code="TIMEOUT_ERROR",
            details={
                "operation": operation,
                "timeout_seconds": timeout_seconds
            },
            telemetry_id=telemetry_id
        )
        self.operation = operation
        self.timeout_seconds = timeout_seconds


class BatchProcessingError(TelemetryError):
    """Batch processing error"""
    
    def __init__(
        self,
        message: str,
        batch_id: str,
        failed_items: List[str],
        successful_items: int = 0,
        total_items: int = 0
    ):
        super().__init__(
            message=message,
            error_code="BATCH_PROCESSING_ERROR",
            details={
                "batch_id": batch_id,
                "failed_items": failed_items,
                "successful_items": successful_items,
                "total_items": total_items
            }
        )
        self.batch_id = batch_id
        self.failed_items = failed_items
        self.successful_items = successful_items
        self.total_items = total_items


class SchemaError(TelemetryError):
    """Telemetry schema error"""
    
    def __init__(
        self,
        message: str,
        schema_name: str,
        schema_version: Optional[str] = None,
        telemetry_id: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code="SCHEMA_ERROR",
            details={
                "schema_name": schema_name,
                "schema_version": schema_version
            },
            telemetry_id=telemetry_id
        )
        self.schema_name = schema_name
        self.schema_version = schema_version


class SerializationError(TelemetryError):
    """Telemetry serialization error"""
    
    def __init__(
        self,
        message: str,
        serialization_format: str,
        telemetry_id: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code="SERIALIZATION_ERROR",
            details={"serialization_format": serialization_format},
            telemetry_id=telemetry_id
        )
        self.serialization_format = serialization_format


class NetworkError(TelemetryError):
    """Network communication error"""
    
    def __init__(
        self,
        message: str,
        endpoint: str,
        status_code: Optional[int] = None,
        telemetry_id: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code="NETWORK_ERROR",
            details={
                "endpoint": endpoint,
                "status_code": status_code
            },
            telemetry_id=telemetry_id
        )
        self.endpoint = endpoint
        self.status_code = status_code


class ResourceError(TelemetryError):
    """Resource limitation error"""
    
    def __init__(
        self,
        message: str,
        resource_type: str,
        current_usage: float,
        limit: float
    ):
        super().__init__(
            message=message,
            error_code="RESOURCE_ERROR",
            details={
                "resource_type": resource_type,
                "current_usage": current_usage,
                "limit": limit
            }
        )
        self.resource_type = resource_type
        self.current_usage = current_usage
        self.limit = limit