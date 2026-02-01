"""
Data Ingestion Module for Observer Eye Middleware

This module provides real-time data ingestion capabilities for the FastAPI middleware layer.
"""

from .real_data_pipeline import (
    RealDataIngestionService,
    StreamingDataType,
    StreamingConfig,
    DataQualityAnalyzer,
    get_ingestion_service,
    shutdown_ingestion_service
)

__all__ = [
    'RealDataIngestionService',
    'StreamingDataType', 
    'StreamingConfig',
    'DataQualityAnalyzer',
    'get_ingestion_service',
    'shutdown_ingestion_service'
]