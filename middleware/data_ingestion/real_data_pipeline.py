"""
Real Data Ingestion Pipeline for FastAPI Middleware

This module provides real-time data ingestion capabilities for the middleware layer,
processing data from various sources and forwarding to the Django backend.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import httpx
import structlog

from ..performance.metrics import PerformanceMonitor
from ..caching.cache_manager import CacheManager
from ..error_handling.exceptions import DataIngestionError

logger = structlog.get_logger(__name__)


class StreamingDataType(Enum):
    """Types of streaming data."""
    REAL_TIME_METRICS = "real_time_metrics"
    LOG_STREAM = "log_stream"
    TELEMETRY_STREAM = "telemetry_stream"
    EVENT_STREAM = "event_stream"
    ALERT_STREAM = "alert_stream"


@dataclass
class StreamingConfig:
    """Configuration for streaming data ingestion."""
    buffer_size: int = 1000
    flush_interval_seconds: int = 5
    max_retry_attempts: int = 3
    enable_compression: bool = True
    enable_batching: bool = True
    quality_threshold: float = 0.95


class RealTimeDataBuffer:
    """Buffer for real-time data before processing."""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.buffer: List[Dict[str, Any]] = []
        self.lock = asyncio.Lock()
        
    async def add(self, data: Dict[str, Any]) -> bool:
        """Add data to buffer. Returns True if buffer is full."""
        async with self.lock:
            self.buffer.append(data)
            if len(self.buffer) >= self.max_size:
                return True
            return False
    
    async def flush(self) -> List[Dict[str, Any]]:
        """Flush and return all buffered data."""
        async with self.lock:
            data = self.buffer.copy()
            self.buffer.clear()
            return data
    
    async def size(self) -> int:
        """Get current buffer size."""
        async with self.lock:
            return len(self.buffer)


class DataQualityAnalyzer:
    """Analyzes the quality of incoming data streams."""
    
    def __init__(self):
        self.quality_metrics = {
            'completeness': 0.0,
            'accuracy': 0.0,
            'timeliness': 0.0,
            'consistency': 0.0
        }
    
    async def analyze_batch(self, data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Analyze data quality for a batch."""
        if not data:
            return self.quality_metrics
        
        # Completeness: percentage of records with all required fields
        required_fields = ['timestamp', 'source', 'data_type']
        complete_records = 0
        
        for record in data:
            if all(field in record and record[field] is not None for field in required_fields):
                complete_records += 1
        
        completeness = complete_records / len(data)
        
        # Timeliness: percentage of records with recent timestamps
        now = datetime.now(timezone.utc)
        timely_records = 0
        
        for record in data:
            if 'timestamp' in record:
                try:
                    if isinstance(record['timestamp'], str):
                        timestamp = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
                    else:
                        timestamp = record['timestamp']
                    
                    # Consider records within last 5 minutes as timely
                    if (now - timestamp).total_seconds() <= 300:
                        timely_records += 1
                except (ValueError, TypeError):
                    pass
        
        timeliness = timely_records / len(data) if data else 0
        
        # Consistency: check for duplicate records
        unique_records = set()
        consistent_records = 0
        
        for record in data:
            record_key = f"{record.get('source', '')}-{record.get('timestamp', '')}-{record.get('data_type', '')}"
            if record_key not in unique_records:
                unique_records.add(record_key)
                consistent_records += 1
        
        consistency = consistent_records / len(data) if data else 0
        
        # Accuracy: basic validation of data types and ranges
        accurate_records = 0
        for record in data:
            is_accurate = True
            
            # Check numeric values are within reasonable ranges
            if 'value' in record:
                try:
                    value = float(record['value'])
                    if value < -1e10 or value > 1e10:  # Reasonable range check
                        is_accurate = False
                except (ValueError, TypeError):
                    is_accurate = False
            
            if is_accurate:
                accurate_records += 1
        
        accuracy = accurate_records / len(data) if data else 0
        
        return {
            'completeness': completeness,
            'accuracy': accuracy,
            'timeliness': timeliness,
            'consistency': consistency,
            'overall': (completeness + accuracy + timeliness + consistency) / 4
        }


class RealDataIngestionService:
    """Service for ingesting real data through the middleware."""
    
    def __init__(self, django_backend_url: str, config: StreamingConfig):
        self.django_backend_url = django_backend_url
        self.config = config
        self.buffers: Dict[StreamingDataType, RealTimeDataBuffer] = {}
        self.quality_analyzer = DataQualityAnalyzer()
        self.performance_monitor = PerformanceMonitor()
        self.cache_manager = CacheManager()
        
        # Initialize buffers for each data type
        for data_type in StreamingDataType:
            self.buffers[data_type] = RealTimeDataBuffer(config.buffer_size)
        
        # Start background flush task
        self.flush_task = None
        self.running = False
    
    async def start(self):
        """Start the ingestion service."""
        self.running = True
        self.flush_task = asyncio.create_task(self._periodic_flush())
        logger.info("Real data ingestion service started")
    
    async def stop(self):
        """Stop the ingestion service."""
        self.running = False
        if self.flush_task:
            self.flush_task.cancel()
            try:
                await self.flush_task
            except asyncio.CancelledError:
                pass
        
        # Flush remaining data
        await self._flush_all_buffers()
        logger.info("Real data ingestion service stopped")
    
    async def ingest_streaming_data(self, data: Dict[str, Any], 
                                  data_type: StreamingDataType) -> Dict[str, Any]:
        """
        Ingest streaming data in real-time.
        
        Args:
            data: The data record to ingest
            data_type: Type of streaming data
            
        Returns:
            Ingestion result
        """
        try:
            # Add metadata
            data['ingestion_timestamp'] = datetime.now(timezone.utc).isoformat()
            data['middleware_source'] = 'fastapi_middleware'
            
            # Add to appropriate buffer
            buffer = self.buffers.get(data_type)
            if not buffer:
                raise DataIngestionError(f"Unknown data type: {data_type}")
            
            buffer_full = await buffer.add(data)
            
            # If buffer is full, trigger immediate flush
            if buffer_full:
                await self._flush_buffer(data_type)
            
            return {
                'success': True,
                'message': 'Data queued for processing',
                'buffer_size': await buffer.size(),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to ingest streaming data", error=str(e), data_type=data_type.value)
            raise DataIngestionError(f"Ingestion failed: {str(e)}")
    
    async def ingest_batch_data(self, data_batch: List[Dict[str, Any]], 
                              data_type: StreamingDataType) -> Dict[str, Any]:
        """
        Ingest a batch of data.
        
        Args:
            data_batch: List of data records
            data_type: Type of data
            
        Returns:
            Batch ingestion result
        """
        try:
            # Analyze data quality
            quality_metrics = await self.quality_analyzer.analyze_batch(data_batch)
            
            if quality_metrics['overall'] < self.config.quality_threshold:
                logger.warning("Data quality below threshold", 
                             quality=quality_metrics['overall'],
                             threshold=self.config.quality_threshold)
            
            # Process batch directly to Django backend
            result = await self._send_to_backend(data_batch, data_type)
            
            # Cache quality metrics
            await self.cache_manager.set(
                f"data_quality:{data_type.value}",
                quality_metrics,
                ttl=300  # 5 minutes
            )
            
            return {
                'success': result['success'],
                'records_processed': len(data_batch),
                'quality_metrics': quality_metrics,
                'backend_response': result,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to ingest batch data", error=str(e), data_type=data_type.value)
            raise DataIngestionError(f"Batch ingestion failed: {str(e)}")
    
    async def get_ingestion_stats(self) -> Dict[str, Any]:
        """Get current ingestion statistics."""
        stats = {
            'service_status': 'running' if self.running else 'stopped',
            'buffer_sizes': {},
            'quality_metrics': {},
            'performance_metrics': await self.performance_monitor.get_current_metrics(),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Get buffer sizes
        for data_type, buffer in self.buffers.items():
            stats['buffer_sizes'][data_type.value] = await buffer.size()
        
        # Get cached quality metrics
        for data_type in StreamingDataType:
            quality_key = f"data_quality:{data_type.value}"
            quality_metrics = await self.cache_manager.get(quality_key)
            if quality_metrics:
                stats['quality_metrics'][data_type.value] = quality_metrics
        
        return stats
    
    async def _periodic_flush(self):
        """Periodically flush buffers."""
        while self.running:
            try:
                await asyncio.sleep(self.config.flush_interval_seconds)
                await self._flush_all_buffers()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in periodic flush", error=str(e))
    
    async def _flush_all_buffers(self):
        """Flush all data buffers."""
        for data_type in StreamingDataType:
            await self._flush_buffer(data_type)
    
    async def _flush_buffer(self, data_type: StreamingDataType):
        """Flush a specific buffer."""
        try:
            buffer = self.buffers[data_type]
            data = await buffer.flush()
            
            if data:
                logger.info("Flushing buffer", data_type=data_type.value, count=len(data))
                await self._send_to_backend(data, data_type)
                
        except Exception as e:
            logger.error("Failed to flush buffer", data_type=data_type.value, error=str(e))
    
    async def _send_to_backend(self, data: List[Dict[str, Any]], 
                             data_type: StreamingDataType) -> Dict[str, Any]:
        """Send data to Django backend."""
        try:
            # Determine the appropriate backend endpoint
            endpoint_map = {
                StreamingDataType.REAL_TIME_METRICS: 'ingest/metrics/',
                StreamingDataType.LOG_STREAM: 'ingest/logs/',
                StreamingDataType.TELEMETRY_STREAM: 'ingest/telemetry/',
                StreamingDataType.EVENT_STREAM: 'ingest/bulk/',
                StreamingDataType.ALERT_STREAM: 'ingest/bulk/'
            }
            
            endpoint = endpoint_map.get(data_type, 'ingest/bulk/')
            url = f"{self.django_backend_url}/{endpoint}"
            
            # Prepare payload based on data type
            if data_type == StreamingDataType.REAL_TIME_METRICS:
                payload = {
                    'source': 'middleware_streaming',
                    'metrics': data
                }
            elif data_type == StreamingDataType.LOG_STREAM:
                payload = {
                    'source': 'middleware_streaming',
                    'logs': data
                }
            elif data_type == StreamingDataType.TELEMETRY_STREAM:
                payload = {
                    'source': 'middleware_streaming',
                    'telemetry': data
                }
            else:
                payload = {
                    'source': 'middleware_streaming',
                    'data': data
                }
            
            # Send to backend with retry logic
            for attempt in range(self.config.max_retry_attempts):
                try:
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        response = await client.post(url, json=payload)
                        response.raise_for_status()
                        return response.json()
                        
                except httpx.RequestError as e:
                    if attempt == self.config.max_retry_attempts - 1:
                        raise
                    logger.warning("Backend request failed, retrying", 
                                 attempt=attempt + 1, error=str(e))
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
            
        except Exception as e:
            logger.error("Failed to send data to backend", error=str(e))
            raise DataIngestionError(f"Backend communication failed: {str(e)}")


# Global service instance
_ingestion_service: Optional[RealDataIngestionService] = None


async def get_ingestion_service() -> RealDataIngestionService:
    """Get the global ingestion service instance."""
    global _ingestion_service
    if _ingestion_service is None:
        import os
        django_url = os.getenv('DJANGO_BACKEND_URL', 'http://localhost:8000')
        config = StreamingConfig()
        _ingestion_service = RealDataIngestionService(django_url, config)
        await _ingestion_service.start()
    
    return _ingestion_service


async def shutdown_ingestion_service():
    """Shutdown the global ingestion service."""
    global _ingestion_service
    if _ingestion_service:
        await _ingestion_service.stop()
        _ingestion_service = None