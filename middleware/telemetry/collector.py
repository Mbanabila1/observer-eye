"""
Telemetry data collector for Observer Eye Platform.
Handles ingestion of telemetry data from various sources with validation,
rate limiting, and batch processing capabilities.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timezone
import json
import uuid

import structlog
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from .models import (
    TelemetryData, TelemetryBatch, TelemetryType, TelemetrySource,
    SeverityLevel, TelemetryMetrics
)
from .exceptions import (
    TelemetryError, ValidationError, RateLimitError, BatchProcessingError,
    ConfigurationError, ResourceError
)
from caching.cache_manager import CacheManager

logger = structlog.get_logger(__name__)
tracer = trace.get_tracer(__name__)


class TelemetryCollector:
    """
    Telemetry data collector with comprehensive ingestion capabilities.
    Supports multiple data formats, rate limiting, and batch processing.
    """
    
    def __init__(
        self,
        cache_manager: Optional[CacheManager] = None,
        max_batch_size: int = 1000,
        batch_timeout_seconds: int = 30,
        rate_limit_per_second: int = 10000,
        enable_validation: bool = True,
        enable_deduplication: bool = True,
        deduplication_window_seconds: int = 300
    ):
        self.cache_manager = cache_manager
        self.max_batch_size = max_batch_size
        self.batch_timeout_seconds = batch_timeout_seconds
        self.rate_limit_per_second = rate_limit_per_second
        self.enable_validation = enable_validation
        self.enable_deduplication = enable_deduplication
        self.deduplication_window_seconds = deduplication_window_seconds
        
        # Internal state
        self._current_batch: List[TelemetryData] = []
        self._batch_lock = asyncio.Lock()
        self._rate_limiter = RateLimiter(rate_limit_per_second)
        self._metrics = TelemetryMetrics()
        self._deduplication_cache: Dict[str, datetime] = {}
        self._batch_processors: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()
        
        # Start background batch processor
        self._batch_processor_task = None
        
        logger.info(
            "Telemetry collector initialized",
            max_batch_size=max_batch_size,
            rate_limit_per_second=rate_limit_per_second,
            enable_validation=enable_validation,
            enable_deduplication=enable_deduplication
        )
    
    async def start(self) -> None:
        """Start the telemetry collector"""
        if self._batch_processor_task is None:
            self._batch_processor_task = asyncio.create_task(self._batch_processor())
            logger.info("Telemetry collector started")
    
    async def stop(self) -> None:
        """Stop the telemetry collector"""
        self._shutdown_event.set()
        
        if self._batch_processor_task:
            await self._batch_processor_task
            self._batch_processor_task = None
        
        # Process any remaining batches
        await self._flush_current_batch()
        
        logger.info("Telemetry collector stopped")
    
    async def collect_single(
        self,
        telemetry_data: Union[Dict[str, Any], TelemetryData],
        source_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> str:
        """
        Collect a single telemetry data point.
        
        Args:
            telemetry_data: Telemetry data to collect
            source_ip: Source IP address
            user_agent: User agent string
        
        Returns:
            str: Telemetry ID
        """
        with tracer.start_as_current_span("collect_single") as span:
            try:
                # Check rate limit
                await self._rate_limiter.check_rate_limit()
                
                # Convert to TelemetryData if needed
                if isinstance(telemetry_data, dict):
                    telemetry = await self._parse_telemetry_data(telemetry_data)
                else:
                    telemetry = telemetry_data
                
                # Validate telemetry data
                if self.enable_validation:
                    await self._validate_telemetry(telemetry)
                
                # Check for duplicates
                if self.enable_deduplication:
                    if await self._is_duplicate(telemetry):
                        logger.debug(
                            "Duplicate telemetry data detected",
                            telemetry_id=telemetry.id,
                            name=telemetry.name
                        )
                        return telemetry.id
                
                # Add to current batch
                await self._add_to_batch(telemetry)
                
                # Update metrics
                self._metrics.total_received += 1
                
                span.set_attribute("telemetry.id", telemetry.id)
                span.set_attribute("telemetry.type", telemetry.type.value)
                span.set_attribute("telemetry.source", telemetry.source.value)
                span.set_status(Status(StatusCode.OK))
                
                logger.debug(
                    "Telemetry data collected",
                    telemetry_id=telemetry.id,
                    type=telemetry.type.value,
                    source=telemetry.source.value,
                    name=telemetry.name
                )
                
                return telemetry.id
                
            except Exception as e:
                self._metrics.total_failed += 1
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                
                logger.error(
                    "Failed to collect telemetry data",
                    error=str(e),
                    telemetry_data=telemetry_data
                )
                raise
    
    async def collect_batch(
        self,
        telemetry_batch: Union[List[Dict[str, Any]], List[TelemetryData], TelemetryBatch],
        source_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> List[str]:
        """
        Collect a batch of telemetry data.
        
        Args:
            telemetry_batch: Batch of telemetry data
            source_ip: Source IP address
            user_agent: User agent string
        
        Returns:
            List[str]: List of telemetry IDs
        """
        with tracer.start_as_current_span("collect_batch") as span:
            try:
                # Convert to TelemetryBatch if needed
                if isinstance(telemetry_batch, TelemetryBatch):
                    batch = telemetry_batch
                elif isinstance(telemetry_batch, list):
                    telemetry_data = []
                    for item in telemetry_batch:
                        if isinstance(item, dict):
                            telemetry_data.append(await self._parse_telemetry_data(item))
                        else:
                            telemetry_data.append(item)
                    
                    batch = TelemetryBatch(
                        telemetry_data=telemetry_data,
                        batch_size=len(telemetry_data)
                    )
                else:
                    raise ValidationError("Invalid batch format")
                
                # Check rate limit for batch
                await self._rate_limiter.check_batch_rate_limit(batch.batch_size)
                
                collected_ids = []
                failed_items = []
                
                for telemetry in batch.telemetry_data:
                    try:
                        # Validate telemetry data
                        if self.enable_validation:
                            await self._validate_telemetry(telemetry)
                        
                        # Check for duplicates
                        if self.enable_deduplication:
                            if await self._is_duplicate(telemetry):
                                logger.debug(
                                    "Duplicate telemetry data in batch",
                                    telemetry_id=telemetry.id,
                                    batch_id=batch.batch_id
                                )
                                continue
                        
                        # Add to current batch
                        await self._add_to_batch(telemetry)
                        collected_ids.append(telemetry.id)
                        
                        self._metrics.total_received += 1
                        
                    except Exception as e:
                        failed_items.append({
                            "telemetry_id": telemetry.id,
                            "error": str(e)
                        })
                        self._metrics.total_failed += 1
                        
                        logger.error(
                            "Failed to collect telemetry item in batch",
                            telemetry_id=telemetry.id,
                            batch_id=batch.batch_id,
                            error=str(e)
                        )
                
                span.set_attribute("batch.id", batch.batch_id)
                span.set_attribute("batch.size", batch.batch_size)
                span.set_attribute("batch.collected", len(collected_ids))
                span.set_attribute("batch.failed", len(failed_items))
                
                if failed_items:
                    span.set_status(Status(StatusCode.ERROR, f"{len(failed_items)} items failed"))
                    
                    if len(failed_items) == batch.batch_size:
                        # All items failed
                        raise BatchProcessingError(
                            message="All items in batch failed",
                            batch_id=batch.batch_id,
                            failed_items=[item["telemetry_id"] for item in failed_items],
                            total_items=batch.batch_size
                        )
                else:
                    span.set_status(Status(StatusCode.OK))
                
                logger.info(
                    "Batch telemetry collection completed",
                    batch_id=batch.batch_id,
                    total_items=batch.batch_size,
                    collected_items=len(collected_ids),
                    failed_items=len(failed_items)
                )
                
                return collected_ids
                
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                
                logger.error(
                    "Failed to collect telemetry batch",
                    error=str(e),
                    batch_size=len(telemetry_batch) if isinstance(telemetry_batch, list) else "unknown"
                )
                raise
    
    async def _parse_telemetry_data(self, data: Dict[str, Any]) -> TelemetryData:
        """Parse raw telemetry data into TelemetryData model"""
        try:
            # Set default values if not provided
            if 'id' not in data:
                data['id'] = str(uuid.uuid4())
            
            if 'timestamp' not in data:
                data['timestamp'] = datetime.now(timezone.utc)
            elif isinstance(data['timestamp'], str):
                data['timestamp'] = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
            
            if 'received_at' not in data:
                data['received_at'] = datetime.now(timezone.utc)
            
            # Ensure required fields have defaults
            if 'type' not in data:
                data['type'] = TelemetryType.METRIC
            
            if 'source' not in data:
                data['source'] = TelemetrySource.APPLICATION
            
            if 'severity' not in data:
                data['severity'] = SeverityLevel.INFO
            
            # Parse enum fields
            if isinstance(data.get('type'), str):
                data['type'] = TelemetryType(data['type'].lower())
            
            if isinstance(data.get('source'), str):
                data['source'] = TelemetrySource(data['source'].lower())
            
            if isinstance(data.get('severity'), str):
                data['severity'] = SeverityLevel(data['severity'].lower())
            
            return TelemetryData(**data)
            
        except Exception as e:
            raise ValidationError(
                message=f"Failed to parse telemetry data: {str(e)}",
                field_errors=[{"field": "data", "message": str(e), "code": "parse_error"}]
            )
    
    async def _validate_telemetry(self, telemetry: TelemetryData) -> None:
        """Validate telemetry data"""
        errors = []
        
        # Check required fields
        if not telemetry.name:
            errors.append({"field": "name", "message": "Name is required", "code": "required"})
        
        if telemetry.value is None:
            errors.append({"field": "value", "message": "Value is required", "code": "required"})
        
        # Validate timestamp
        if telemetry.timestamp > datetime.now(timezone.utc):
            errors.append({
                "field": "timestamp",
                "message": "Timestamp cannot be in the future",
                "code": "invalid_timestamp"
            })
        
        # Validate confidence score
        if not (0.0 <= telemetry.confidence <= 1.0):
            errors.append({
                "field": "confidence",
                "message": "Confidence must be between 0.0 and 1.0",
                "code": "invalid_range"
            })
        
        if errors:
            raise ValidationError(
                message="Telemetry validation failed",
                field_errors=errors,
                telemetry_id=telemetry.id
            )
    
    async def _is_duplicate(self, telemetry: TelemetryData) -> bool:
        """Check if telemetry data is a duplicate"""
        # Create deduplication key
        dedup_key = self._create_deduplication_key(telemetry)
        
        # Check in-memory cache first
        if dedup_key in self._deduplication_cache:
            last_seen = self._deduplication_cache[dedup_key]
            if (datetime.now(timezone.utc) - last_seen).total_seconds() < self.deduplication_window_seconds:
                return True
        
        # Check external cache if available
        if self.cache_manager:
            cache_key = f"telemetry:dedup:{dedup_key}"
            cached_value = await self.cache_manager.get(cache_key)
            if cached_value:
                return True
            
            # Store in cache
            await self.cache_manager.set(
                cache_key,
                telemetry.id,
                ttl=self.deduplication_window_seconds
            )
        
        # Update in-memory cache
        self._deduplication_cache[dedup_key] = datetime.now(timezone.utc)
        
        # Clean up old entries
        await self._cleanup_deduplication_cache()
        
        return False
    
    def _create_deduplication_key(self, telemetry: TelemetryData) -> str:
        """Create deduplication key for telemetry data"""
        key_parts = [
            telemetry.type.value,
            telemetry.source.value,
            telemetry.name,
            str(telemetry.value),
            telemetry.service_name or "",
            telemetry.host or "",
            str(int(telemetry.timestamp.timestamp() // 60))  # Round to minute
        ]
        return ":".join(key_parts)
    
    async def _cleanup_deduplication_cache(self) -> None:
        """Clean up old entries from deduplication cache"""
        cutoff_time = datetime.now(timezone.utc)
        cutoff_time = cutoff_time.replace(second=cutoff_time.second - self.deduplication_window_seconds)
        
        keys_to_remove = [
            key for key, timestamp in self._deduplication_cache.items()
            if timestamp < cutoff_time
        ]
        
        for key in keys_to_remove:
            del self._deduplication_cache[key]
    
    async def _add_to_batch(self, telemetry: TelemetryData) -> None:
        """Add telemetry data to current batch"""
        async with self._batch_lock:
            self._current_batch.append(telemetry)
            
            # Check if batch is full
            if len(self._current_batch) >= self.max_batch_size:
                await self._process_current_batch()
    
    async def _batch_processor(self) -> None:
        """Background batch processor"""
        while not self._shutdown_event.is_set():
            try:
                # Wait for timeout or shutdown
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=self.batch_timeout_seconds
                )
                break  # Shutdown event was set
                
            except asyncio.TimeoutError:
                # Timeout reached, process current batch
                await self._process_current_batch()
    
    async def _process_current_batch(self) -> None:
        """Process the current batch of telemetry data"""
        async with self._batch_lock:
            if not self._current_batch:
                return
            
            batch_to_process = self._current_batch.copy()
            self._current_batch.clear()
        
        if batch_to_process:
            batch = TelemetryBatch(
                telemetry_data=batch_to_process,
                batch_size=len(batch_to_process)
            )
            
            try:
                # Process batch (this would typically send to processing pipeline)
                await self._send_batch_for_processing(batch)
                
                self._metrics.total_processed += len(batch_to_process)
                
                logger.info(
                    "Batch processed successfully",
                    batch_id=batch.batch_id,
                    batch_size=batch.batch_size
                )
                
            except Exception as e:
                self._metrics.total_failed += len(batch_to_process)
                
                logger.error(
                    "Failed to process batch",
                    batch_id=batch.batch_id,
                    batch_size=batch.batch_size,
                    error=str(e)
                )
    
    async def _send_batch_for_processing(self, batch: TelemetryBatch) -> None:
        """Send batch for processing (placeholder for actual processing pipeline)"""
        # This would typically send the batch to the telemetry processor
        # For now, we'll just log it
        logger.debug(
            "Sending batch for processing",
            batch_id=batch.batch_id,
            batch_size=batch.batch_size
        )
    
    async def _flush_current_batch(self) -> None:
        """Flush any remaining telemetry data in the current batch"""
        await self._process_current_batch()
    
    def get_metrics(self) -> TelemetryMetrics:
        """Get current telemetry collection metrics"""
        self._metrics.metrics_end_time = datetime.now(timezone.utc)
        
        # Calculate rates
        time_diff = (self._metrics.metrics_end_time - self._metrics.metrics_start_time).total_seconds()
        if time_diff > 0:
            self._metrics.processing_rate_per_second = self._metrics.total_processed / time_diff
        
        return self._metrics
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        return {
            "status": "healthy",
            "batch_processor_running": self._batch_processor_task is not None and not self._batch_processor_task.done(),
            "current_batch_size": len(self._current_batch),
            "deduplication_cache_size": len(self._deduplication_cache),
            "metrics": self.get_metrics().dict()
        }


class RateLimiter:
    """Rate limiter for telemetry collection"""
    
    def __init__(self, rate_per_second: int):
        self.rate_per_second = rate_per_second
        self.tokens = rate_per_second
        self.last_update = time.time()
        self.lock = asyncio.Lock()
    
    async def check_rate_limit(self) -> None:
        """Check if request is within rate limit"""
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            
            # Add tokens based on elapsed time
            self.tokens = min(
                self.rate_per_second,
                self.tokens + elapsed * self.rate_per_second
            )
            self.last_update = now
            
            if self.tokens < 1:
                raise RateLimitError(
                    message="Rate limit exceeded",
                    limit=self.rate_per_second,
                    window_seconds=1,
                    current_rate=self.rate_per_second - self.tokens
                )
            
            self.tokens -= 1
    
    async def check_batch_rate_limit(self, batch_size: int) -> None:
        """Check if batch is within rate limit"""
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            
            # Add tokens based on elapsed time
            self.tokens = min(
                self.rate_per_second,
                self.tokens + elapsed * self.rate_per_second
            )
            self.last_update = now
            
            if self.tokens < batch_size:
                raise RateLimitError(
                    message=f"Batch rate limit exceeded (batch size: {batch_size})",
                    limit=self.rate_per_second,
                    window_seconds=1,
                    current_rate=self.rate_per_second - self.tokens
                )
            
            self.tokens -= batch_size