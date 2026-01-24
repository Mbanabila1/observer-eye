"""
Base Observability Processor

Defines the polymorphic interface and common functionality for all four pillars
data processors. Implements the abstract base class that ensures consistent
behavior across metrics, events, logs, and traces processors.
"""

import asyncio
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union, TypeVar, Generic
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)

class PillarType(Enum):
    """Four pillars of observability"""
    METRICS = "metrics"
    EVENTS = "events"
    LOGS = "logs"
    TRACES = "traces"

class ProcessingStatus(Enum):
    """Processing status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CORRELATED = "correlated"

@dataclass
class ProcessingMetadata:
    """Metadata for processing operations"""
    processor_id: str
    pillar_type: PillarType
    processing_start_time: float
    processing_end_time: Optional[float] = None
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    deep_system_context: Optional[Dict[str, Any]] = None
    kernel_metrics: Optional[Dict[str, Any]] = None
    payload_inspection_results: Optional[Dict[str, Any]] = None
    
    @property
    def processing_duration_ms(self) -> Optional[float]:
        """Calculate processing duration in milliseconds"""
        if self.processing_end_time is None:
            return None
        return (self.processing_end_time - self.processing_start_time) * 1000

@dataclass
class ProcessingResult:
    """Result of data processing operation"""
    status: ProcessingStatus
    processed_data: Dict[str, Any]
    metadata: ProcessingMetadata
    correlation_candidates: List[str] = field(default_factory=list)
    deep_system_insights: Optional[Dict[str, Any]] = None
    error_details: Optional[str] = None
    
    @property
    def is_successful(self) -> bool:
        """Check if processing was successful"""
        return self.status in [ProcessingStatus.COMPLETED, ProcessingStatus.CORRELATED]
    
    @property
    def processing_latency_ms(self) -> Optional[float]:
        """Get processing latency in milliseconds"""
        return self.metadata.processing_duration_ms

# Type variable for generic processor data
T = TypeVar('T')

class BaseObservabilityProcessor(ABC, Generic[T]):
    """
    Abstract base class for all four pillars processors.
    
    Implements the polymorphic interface that ensures consistent behavior
    across metrics, events, logs, and traces processors while allowing
    specialized implementations for each pillar type.
    """
    
    def __init__(self, processor_id: str, pillar_type: PillarType):
        self.processor_id = processor_id
        self.pillar_type = pillar_type
        self.logger = structlog.get_logger(__name__).bind(
            processor_id=processor_id,
            pillar_type=pillar_type.value
        )
        self._processing_stats = {
            'total_processed': 0,
            'successful_processed': 0,
            'failed_processed': 0,
            'average_latency_ms': 0.0,
            'last_processing_time': None
        }
    
    async def process(self, data: T, correlation_id: Optional[str] = None) -> ProcessingResult:
        """
        Main processing method that orchestrates the complete processing pipeline.
        
        Args:
            data: Input data to process (type varies by pillar)
            correlation_id: Optional correlation ID for cross-pillar linking
            
        Returns:
            ProcessingResult with processed data and metadata
        """
        # Create processing metadata
        metadata = ProcessingMetadata(
            processor_id=self.processor_id,
            pillar_type=self.pillar_type,
            processing_start_time=time.time(),
            correlation_id=correlation_id or str(uuid.uuid4())
        )
        
        try:
            self.logger.info("Starting data processing", 
                           correlation_id=metadata.correlation_id)
            
            # Validate input data
            validation_result = await self._validate_input(data)
            if not validation_result.is_valid:
                return ProcessingResult(
                    status=ProcessingStatus.FAILED,
                    processed_data={},
                    metadata=metadata,
                    error_details=f"Validation failed: {validation_result.error_message}"
                )
            
            # Enrich with deep system context
            await self._enrich_with_deep_system_context(metadata)
            
            # Perform pillar-specific processing
            processed_data = await self._process_pillar_data(data, metadata)
            
            # Extract correlation candidates
            correlation_candidates = await self._extract_correlation_candidates(
                processed_data, metadata
            )
            
            # Generate deep system insights
            deep_insights = await self._generate_deep_system_insights(
                processed_data, metadata
            )
            
            # Mark processing as completed
            metadata.processing_end_time = time.time()
            
            # Update statistics
            self._update_processing_stats(metadata, True)
            
            result = ProcessingResult(
                status=ProcessingStatus.COMPLETED,
                processed_data=processed_data,
                metadata=metadata,
                correlation_candidates=correlation_candidates,
                deep_system_insights=deep_insights
            )
            
            self.logger.info("Data processing completed successfully",
                           correlation_id=metadata.correlation_id,
                           processing_duration_ms=result.processing_latency_ms,
                           correlation_candidates_count=len(correlation_candidates))
            
            return result
            
        except Exception as e:
            metadata.processing_end_time = time.time()
            self._update_processing_stats(metadata, False)
            
            self.logger.error("Data processing failed",
                            correlation_id=metadata.correlation_id,
                            error=str(e))
            
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                processed_data={},
                metadata=metadata,
                error_details=str(e)
            )
    
    @dataclass
    class ValidationResult:
        """Result of input validation"""
        is_valid: bool
        error_message: Optional[str] = None
        normalized_data: Optional[Any] = None
    
    @abstractmethod
    async def _validate_input(self, data: T) -> 'BaseObservabilityProcessor.ValidationResult':
        """
        Validate input data for the specific pillar type.
        
        Args:
            data: Input data to validate
            
        Returns:
            ValidationResult indicating if data is valid
        """
        pass
    
    @abstractmethod
    async def _process_pillar_data(self, data: T, metadata: ProcessingMetadata) -> Dict[str, Any]:
        """
        Process data specific to this pillar type.
        
        Args:
            data: Validated input data
            metadata: Processing metadata with context
            
        Returns:
            Processed data dictionary
        """
        pass
    
    @abstractmethod
    async def _extract_correlation_candidates(
        self, 
        processed_data: Dict[str, Any], 
        metadata: ProcessingMetadata
    ) -> List[str]:
        """
        Extract correlation candidates for cross-pillar linking.
        
        Args:
            processed_data: Processed data from this pillar
            metadata: Processing metadata
            
        Returns:
            List of correlation candidate identifiers
        """
        pass
    
    async def _enrich_with_deep_system_context(self, metadata: ProcessingMetadata) -> None:
        """
        Enrich processing metadata with deep system context.
        
        This method can be overridden by processors that need specific
        deep system integration capabilities.
        """
        # Default implementation - can be overridden
        metadata.deep_system_context = {
            'timestamp_ns': time.time_ns(),
            'processor_type': self.pillar_type.value,
            'system_load': await self._get_current_system_load()
        }
    
    async def _generate_deep_system_insights(
        self, 
        processed_data: Dict[str, Any], 
        metadata: ProcessingMetadata
    ) -> Optional[Dict[str, Any]]:
        """
        Generate insights from deep system integration.
        
        Args:
            processed_data: Processed pillar data
            metadata: Processing metadata with deep system context
            
        Returns:
            Deep system insights or None if not available
        """
        # Default implementation - can be overridden
        if metadata.deep_system_context:
            return {
                'processing_efficiency': self._calculate_processing_efficiency(metadata),
                'system_impact': await self._assess_system_impact(processed_data),
                'correlation_strength': self._calculate_correlation_strength(processed_data)
            }
        return None
    
    async def _get_current_system_load(self) -> Dict[str, float]:
        """Get current system load metrics"""
        try:
            import psutil
            return {
                'cpu_percent': psutil.cpu_percent(interval=0.1),
                'memory_percent': psutil.virtual_memory().percent,
                'load_avg_1m': psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0.0
            }
        except Exception:
            return {'cpu_percent': 0.0, 'memory_percent': 0.0, 'load_avg_1m': 0.0}
    
    def _calculate_processing_efficiency(self, metadata: ProcessingMetadata) -> float:
        """Calculate processing efficiency score (0.0 to 1.0)"""
        if metadata.processing_duration_ms is None:
            return 0.0
        
        # Efficiency based on processing speed (lower latency = higher efficiency)
        # Target: sub-millisecond processing for optimal efficiency
        target_latency_ms = 1.0
        efficiency = max(0.0, min(1.0, target_latency_ms / metadata.processing_duration_ms))
        return efficiency
    
    async def _assess_system_impact(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the system impact of processing this data"""
        data_size = len(str(processed_data))
        return {
            'data_size_bytes': data_size,
            'complexity_score': min(1.0, data_size / 10000),  # Normalize to 0-1
            'processing_intensity': 'low' if data_size < 1000 else 'medium' if data_size < 10000 else 'high'
        }
    
    def _calculate_correlation_strength(self, processed_data: Dict[str, Any]) -> float:
        """Calculate correlation strength based on data richness"""
        # Simple heuristic: more structured data = higher correlation potential
        correlation_indicators = 0
        
        if 'timestamp' in processed_data:
            correlation_indicators += 1
        if 'service_name' in processed_data or 'source' in processed_data:
            correlation_indicators += 1
        if 'trace_id' in processed_data or 'span_id' in processed_data:
            correlation_indicators += 2  # Traces have high correlation value
        if 'user_id' in processed_data or 'session_id' in processed_data:
            correlation_indicators += 1
        
        return min(1.0, correlation_indicators / 5.0)  # Normalize to 0-1
    
    def _update_processing_stats(self, metadata: ProcessingMetadata, success: bool) -> None:
        """Update internal processing statistics"""
        self._processing_stats['total_processed'] += 1
        
        if success:
            self._processing_stats['successful_processed'] += 1
            
            # Update average latency
            if metadata.processing_duration_ms is not None:
                current_avg = self._processing_stats['average_latency_ms']
                total_successful = self._processing_stats['successful_processed']
                
                # Incremental average calculation
                new_avg = ((current_avg * (total_successful - 1)) + metadata.processing_duration_ms) / total_successful
                self._processing_stats['average_latency_ms'] = new_avg
        else:
            self._processing_stats['failed_processed'] += 1
        
        self._processing_stats['last_processing_time'] = time.time()
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get current processing statistics"""
        stats = self._processing_stats.copy()
        stats['success_rate'] = (
            stats['successful_processed'] / stats['total_processed'] 
            if stats['total_processed'] > 0 else 0.0
        )
        stats['pillar_type'] = self.pillar_type.value
        stats['processor_id'] = self.processor_id
        return stats
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check for this processor"""
        stats = self.get_processing_stats()
        
        # Determine health status
        health_status = "healthy"
        if stats['success_rate'] < 0.95 and stats['total_processed'] > 10:
            health_status = "degraded"
        elif stats['success_rate'] < 0.8 and stats['total_processed'] > 10:
            health_status = "unhealthy"
        
        return {
            'processor_id': self.processor_id,
            'pillar_type': self.pillar_type.value,
            'status': health_status,
            'statistics': stats,
            'last_check': time.time()
        }