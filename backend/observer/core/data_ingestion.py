"""
Real Data Ingestion System for Observer Eye Platform

This module provides mechanisms for ingesting real telemetry and monitoring data
from various sources without using mock or seed data.
"""

import logging
import json
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum

from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone as django_timezone

logger = logging.getLogger(__name__)


class DataSourceType(Enum):
    """Types of data sources for ingestion."""
    METRICS_API = "metrics_api"
    LOG_STREAM = "log_stream"
    TELEMETRY_ENDPOINT = "telemetry_endpoint"
    WEBHOOK = "webhook"
    FILE_UPLOAD = "file_upload"
    REAL_TIME_STREAM = "real_time_stream"


class DataValidationLevel(Enum):
    """Levels of data validation."""
    STRICT = "strict"
    MODERATE = "moderate"
    LENIENT = "lenient"


@dataclass
class DataIngestionConfig:
    """Configuration for data ingestion."""
    source_type: DataSourceType
    validation_level: DataValidationLevel
    batch_size: int = 1000
    max_retries: int = 3
    timeout_seconds: int = 30
    enable_deduplication: bool = True
    enable_compression: bool = False


@dataclass
class IngestionResult:
    """Result of a data ingestion operation."""
    success: bool
    records_processed: int
    records_failed: int
    errors: List[str]
    warnings: List[str]
    processing_time_ms: float
    timestamp: datetime


class DataQualityValidator:
    """Validates data quality for ingested data."""
    
    def __init__(self, validation_level: DataValidationLevel = DataValidationLevel.MODERATE):
        self.validation_level = validation_level
        self.required_fields = {
            'timestamp': datetime,
            'source': str,
            'data_type': str
        }
    
    def validate_record(self, record: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate a single data record.
        
        Args:
            record: The data record to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check required fields
        for field, expected_type in self.required_fields.items():
            if field not in record:
                errors.append(f"Missing required field: {field}")
                continue
            
            if not isinstance(record[field], expected_type) and record[field] is not None:
                # Try to convert timestamp strings
                if field == 'timestamp' and isinstance(record[field], str):
                    try:
                        record[field] = datetime.fromisoformat(record[field].replace('Z', '+00:00'))
                    except ValueError:
                        errors.append(f"Invalid timestamp format: {record[field]}")
                else:
                    errors.append(f"Field {field} has wrong type. Expected {expected_type.__name__}, got {type(record[field]).__name__}")
        
        # Validate timestamp is not in the future (with 5 minute tolerance)
        if 'timestamp' in record and isinstance(record['timestamp'], datetime):
            now = datetime.now(timezone.utc)
            if record['timestamp'] > now.replace(minute=now.minute + 5):
                if self.validation_level == DataValidationLevel.STRICT:
                    errors.append("Timestamp is too far in the future")
                else:
                    # Just log a warning for non-strict validation
                    logger.warning(f"Future timestamp detected: {record['timestamp']}")
        
        # Validate data size
        record_size = len(json.dumps(record, default=str))
        if record_size > 1024 * 1024:  # 1MB limit
            errors.append(f"Record size ({record_size} bytes) exceeds maximum allowed size")
        
        # Additional validation based on data type
        if 'data_type' in record:
            data_type = record['data_type']
            if data_type == 'metrics' and 'value' not in record:
                errors.append("Metrics records must contain a 'value' field")
            elif data_type == 'log' and 'message' not in record:
                errors.append("Log records must contain a 'message' field")
        
        return len(errors) == 0, errors
    
    def validate_batch(self, records: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], List[str]]:
        """
        Validate a batch of records.
        
        Args:
            records: List of records to validate
            
        Returns:
            Tuple of (valid_records, all_errors)
        """
        valid_records = []
        all_errors = []
        
        for i, record in enumerate(records):
            is_valid, errors = self.validate_record(record)
            if is_valid:
                valid_records.append(record)
            else:
                all_errors.extend([f"Record {i}: {error}" for error in errors])
        
        return valid_records, all_errors


class DataDeduplicator:
    """Handles deduplication of ingested data."""
    
    def __init__(self):
        self.seen_hashes = set()
    
    def generate_record_hash(self, record: Dict[str, Any]) -> str:
        """Generate a hash for a record to detect duplicates."""
        # Create a hash based on key fields
        key_fields = ['timestamp', 'source', 'data_type']
        hash_data = {}
        
        for field in key_fields:
            if field in record:
                hash_data[field] = record[field]
        
        # Add data content hash
        if 'data' in record:
            hash_data['data'] = record['data']
        elif 'value' in record:
            hash_data['value'] = record['value']
        elif 'message' in record:
            hash_data['message'] = record['message']
        
        return str(hash(json.dumps(hash_data, sort_keys=True, default=str)))
    
    def deduplicate_batch(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate records from a batch."""
        unique_records = []
        
        for record in records:
            record_hash = self.generate_record_hash(record)
            if record_hash not in self.seen_hashes:
                self.seen_hashes.add(record_hash)
                unique_records.append(record)
        
        return unique_records


class RealDataIngestionPipeline:
    """Main pipeline for ingesting real data into the Observer Eye platform."""
    
    def __init__(self, config: DataIngestionConfig):
        self.config = config
        self.validator = DataQualityValidator(config.validation_level)
        self.deduplicator = DataDeduplicator() if config.enable_deduplication else None
        
    async def ingest_data(self, data: Union[Dict[str, Any], List[Dict[str, Any]]], 
                         source_identifier: str) -> IngestionResult:
        """
        Ingest data from a real source.
        
        Args:
            data: The data to ingest (single record or batch)
            source_identifier: Identifier for the data source
            
        Returns:
            IngestionResult with processing details
        """
        start_time = datetime.now()
        
        try:
            # Normalize input to list
            if isinstance(data, dict):
                records = [data]
            else:
                records = data
            
            # Add source identifier to all records
            for record in records:
                record['source'] = source_identifier
                if 'timestamp' not in record:
                    record['timestamp'] = datetime.now(timezone.utc)
            
            # Validate data quality
            valid_records, validation_errors = self.validator.validate_batch(records)
            
            # Deduplicate if enabled
            if self.deduplicator:
                valid_records = self.deduplicator.deduplicate_batch(valid_records)
            
            # Process in batches
            processed_count = 0
            failed_count = len(records) - len(valid_records)
            processing_errors = []
            
            for i in range(0, len(valid_records), self.config.batch_size):
                batch = valid_records[i:i + self.config.batch_size]
                
                try:
                    await self._process_batch(batch)
                    processed_count += len(batch)
                except Exception as e:
                    logger.error(f"Failed to process batch: {str(e)}")
                    processing_errors.append(f"Batch processing error: {str(e)}")
                    failed_count += len(batch)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return IngestionResult(
                success=failed_count == 0,
                records_processed=processed_count,
                records_failed=failed_count,
                errors=validation_errors + processing_errors,
                warnings=[],
                processing_time_ms=processing_time,
                timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            logger.error(f"Data ingestion failed: {str(e)}")
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return IngestionResult(
                success=False,
                records_processed=0,
                records_failed=len(records) if isinstance(data, list) else 1,
                errors=[f"Pipeline error: {str(e)}"],
                warnings=[],
                processing_time_ms=processing_time,
                timestamp=datetime.now(timezone.utc)
            )
    
    async def _process_batch(self, batch: List[Dict[str, Any]]):
        """Process a batch of validated records."""
        # This is where you would save to your actual models
        # For now, we'll just log the successful processing
        
        with transaction.atomic():
            for record in batch:
                # Route to appropriate model based on data_type
                data_type = record.get('data_type', 'unknown')
                
                if data_type == 'metrics':
                    await self._save_metrics_record(record)
                elif data_type == 'log':
                    await self._save_log_record(record)
                elif data_type == 'telemetry':
                    await self._save_telemetry_record(record)
                else:
                    logger.warning(f"Unknown data type: {data_type}")
    
    async def _save_metrics_record(self, record: Dict[str, Any]):
        """Save a metrics record to the appropriate model."""
        # Import here to avoid circular imports
        from appmetrics.models import ApplicationMetric
        
        try:
            metric = ApplicationMetric(
                timestamp=record['timestamp'],
                source=record['source'],
                metric_name=record.get('metric_name', 'unknown'),
                value=record.get('value', 0),
                unit=record.get('unit', ''),
                tags=record.get('tags', {}),
                metadata=record.get('metadata', {})
            )
            metric.save()
            
        except Exception as e:
            logger.error(f"Failed to save metrics record: {str(e)}")
            raise
    
    async def _save_log_record(self, record: Dict[str, Any]):
        """Save a log record to the appropriate model."""
        # This would save to your logging model
        logger.info(f"Processing log record from {record['source']}: {record.get('message', '')}")
    
    async def _save_telemetry_record(self, record: Dict[str, Any]):
        """Save a telemetry record to the appropriate model."""
        # This would save to your telemetry model
        logger.info(f"Processing telemetry record from {record['source']}")


# Factory function for creating ingestion pipelines
def create_ingestion_pipeline(source_type: DataSourceType, 
                            validation_level: DataValidationLevel = DataValidationLevel.MODERATE,
                            **kwargs) -> RealDataIngestionPipeline:
    """
    Factory function to create a data ingestion pipeline.
    
    Args:
        source_type: Type of data source
        validation_level: Level of validation to apply
        **kwargs: Additional configuration options
        
    Returns:
        Configured RealDataIngestionPipeline instance
    """
    config = DataIngestionConfig(
        source_type=source_type,
        validation_level=validation_level,
        **kwargs
    )
    
    return RealDataIngestionPipeline(config)


# Example usage functions (these would be called by your actual endpoints)
async def ingest_metrics_data(metrics_data: List[Dict[str, Any]], source: str) -> IngestionResult:
    """Ingest real metrics data."""
    pipeline = create_ingestion_pipeline(DataSourceType.METRICS_API)
    return await pipeline.ingest_data(metrics_data, source)


async def ingest_log_data(log_data: List[Dict[str, Any]], source: str) -> IngestionResult:
    """Ingest real log data."""
    pipeline = create_ingestion_pipeline(DataSourceType.LOG_STREAM)
    return await pipeline.ingest_data(log_data, source)


async def ingest_telemetry_data(telemetry_data: List[Dict[str, Any]], source: str) -> IngestionResult:
    """Ingest real telemetry data."""
    pipeline = create_ingestion_pipeline(DataSourceType.TELEMETRY_ENDPOINT)
    return await pipeline.ingest_data(telemetry_data, source)