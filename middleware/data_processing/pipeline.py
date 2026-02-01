"""
Data Processing Pipeline

Integrates validation, transformation, sanitization, and filtering into a comprehensive
data processing pipeline for the Observer Eye Platform.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import structlog

from .validation import DataValidator, ValidationResult
from .transformation import DataTransformer, NormalizedData
from .sanitization import DataSanitizer, SanitizedData
from .filters import DataFilter, FilterConfig, FilterResult, FilterRule

logger = structlog.get_logger()


class PipelineStage(Enum):
    """Pipeline processing stages"""
    VALIDATION = "validation"
    FILTERING = "filtering"
    SANITIZATION = "sanitization"
    TRANSFORMATION = "transformation"


class ProcessingMode(Enum):
    """Data processing modes"""
    STRICT = "strict"          # Fail on any validation/security issues
    PERMISSIVE = "permissive"  # Process data with warnings
    SECURE = "secure"          # Focus on security, may sacrifice some data
    PERFORMANCE = "performance" # Optimize for speed over thoroughness


@dataclass
class PipelineConfig:
    """Configuration for the data processing pipeline"""
    mode: ProcessingMode = ProcessingMode.PERMISSIVE
    stages: List[PipelineStage] = None
    enable_logging: bool = True
    enable_metrics: bool = True
    batch_size: int = 1000
    timeout_seconds: int = 30
    
    def __post_init__(self):
        if self.stages is None:
            self.stages = [
                PipelineStage.VALIDATION,
                PipelineStage.FILTERING,
                PipelineStage.SANITIZATION,
                PipelineStage.TRANSFORMATION
            ]


@dataclass
class PipelineResult:
    """Result of data processing pipeline"""
    original_data: Any
    processed_data: Any
    validation_result: Optional[ValidationResult]
    filter_result: Optional[FilterResult]
    sanitization_result: Optional[SanitizedData]
    transformation_result: Optional[NormalizedData]
    success: bool
    errors: List[str]
    warnings: List[str]
    processing_time_ms: float
    stages_completed: List[PipelineStage]
    metadata: Dict[str, Any]
    timestamp: datetime


class DataProcessingPipeline:
    """Comprehensive data processing pipeline"""
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        self.logger = structlog.get_logger()
        
        # Initialize components
        self.validator = DataValidator()
        self.transformer = DataTransformer()
        self.sanitizer = DataSanitizer()
        self.filter = DataFilter()
        
        # Pipeline statistics
        self.stats = {
            'total_processed': 0,
            'successful_processed': 0,
            'failed_processed': 0,
            'average_processing_time_ms': 0.0,
            'stage_stats': {stage.value: 0 for stage in PipelineStage}
        }
        
        self.logger.info(
            "Data processing pipeline initialized",
            mode=self.config.mode.value,
            stages=len(self.config.stages),
            batch_size=self.config.batch_size
        )
    
    def process_data(self, data: Any, schema_name: Optional[str] = None, 
                    custom_rules: Optional[List[FilterRule]] = None) -> PipelineResult:
        """
        Process data through the complete pipeline
        
        Args:
            data: Input data to process
            schema_name: Optional schema name for validation
            custom_rules: Optional custom filtering rules
            
        Returns:
            PipelineResult with processed data and metadata
        """
        start_time = datetime.now(timezone.utc)
        original_data = data
        current_data = data
        
        # Initialize result containers
        validation_result = None
        filter_result = None
        sanitization_result = None
        transformation_result = None
        
        errors = []
        warnings = []
        stages_completed = []
        
        try:
            self.logger.info(
                "Starting data processing pipeline",
                data_type=type(data).__name__,
                schema_name=schema_name,
                mode=self.config.mode.value,
                stages=len(self.config.stages)
            )
            
            # Process through each configured stage
            for stage in self.config.stages:
                try:
                    if stage == PipelineStage.VALIDATION:
                        current_data, validation_result = self._process_validation_stage(
                            current_data, schema_name
                        )
                        stages_completed.append(stage)
                        
                        if not validation_result.is_valid and self.config.mode == ProcessingMode.STRICT:
                            errors.extend([f"Validation: {e.message}" for e in validation_result.errors])
                            break
                        
                        if validation_result.has_warnings:
                            warnings.extend([f"Validation: {w.message}" for w in validation_result.warnings])
                    
                    elif stage == PipelineStage.FILTERING:
                        current_data, filter_result = self._process_filtering_stage(
                            current_data, custom_rules
                        )
                        stages_completed.append(stage)
                        
                        if filter_result.items_excluded > 0 and self.config.mode == ProcessingMode.STRICT:
                            warnings.append(f"Filtering: {filter_result.items_excluded} items excluded")
                    
                    elif stage == PipelineStage.SANITIZATION:
                        current_data, sanitization_result = self._process_sanitization_stage(
                            current_data
                        )
                        stages_completed.append(stage)
                        
                        if not sanitization_result.is_safe:
                            if self.config.mode in [ProcessingMode.STRICT, ProcessingMode.SECURE]:
                                errors.append(f"Sanitization: Data contains security threats")
                                break
                            else:
                                warnings.append(f"Sanitization: {len(sanitization_result.threats_detected)} threats detected")
                    
                    elif stage == PipelineStage.TRANSFORMATION:
                        current_data, transformation_result = self._process_transformation_stage(
                            current_data
                        )
                        stages_completed.append(stage)
                    
                    # Update stage statistics
                    self.stats['stage_stats'][stage.value] += 1
                    
                except Exception as e:
                    error_msg = f"Stage {stage.value} failed: {str(e)}"
                    errors.append(error_msg)
                    self.logger.error(
                        "Pipeline stage failed",
                        stage=stage.value,
                        error=str(e),
                        data_type=type(current_data).__name__
                    )
                    
                    if self.config.mode == ProcessingMode.STRICT:
                        break
                    else:
                        warnings.append(error_msg)
            
            # Calculate processing time
            end_time = datetime.now(timezone.utc)
            processing_time_ms = (end_time - start_time).total_seconds() * 1000
            
            # Determine success
            success = len(errors) == 0
            
            # Update statistics
            self.stats['total_processed'] += 1
            if success:
                self.stats['successful_processed'] += 1
            else:
                self.stats['failed_processed'] += 1
            
            # Update average processing time
            total_time = self.stats['average_processing_time_ms'] * (self.stats['total_processed'] - 1)
            self.stats['average_processing_time_ms'] = (total_time + processing_time_ms) / self.stats['total_processed']
            
            # Create metadata
            metadata = {
                'pipeline_config': {
                    'mode': self.config.mode.value,
                    'stages_configured': len(self.config.stages),
                    'stages_completed': len(stages_completed)
                },
                'processing_stats': {
                    'processing_time_ms': processing_time_ms,
                    'data_size_bytes': self._estimate_data_size(original_data),
                    'data_complexity': self._calculate_data_complexity(original_data)
                },
                'stage_results': {
                    'validation_passed': validation_result.is_valid if validation_result else None,
                    'items_filtered': filter_result.items_excluded if filter_result else 0,
                    'threats_detected': len(sanitization_result.threats_detected) if sanitization_result else 0,
                    'transformations_applied': len(transformation_result.transformations_applied) if transformation_result else 0
                }
            }
            
            result = PipelineResult(
                original_data=original_data,
                processed_data=current_data,
                validation_result=validation_result,
                filter_result=filter_result,
                sanitization_result=sanitization_result,
                transformation_result=transformation_result,
                success=success,
                errors=errors,
                warnings=warnings,
                processing_time_ms=processing_time_ms,
                stages_completed=stages_completed,
                metadata=metadata,
                timestamp=end_time
            )
            
            self.logger.info(
                "Data processing pipeline completed",
                success=success,
                processing_time_ms=processing_time_ms,
                stages_completed=len(stages_completed),
                errors=len(errors),
                warnings=len(warnings)
            )
            
            return result
            
        except Exception as e:
            self.logger.error(
                "Data processing pipeline failed",
                error=str(e),
                data_type=type(data).__name__
            )
            
            processing_time_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            self.stats['total_processed'] += 1
            self.stats['failed_processed'] += 1
            
            return PipelineResult(
                original_data=original_data,
                processed_data=original_data,
                validation_result=validation_result,
                filter_result=filter_result,
                sanitization_result=sanitization_result,
                transformation_result=transformation_result,
                success=False,
                errors=[f"Pipeline failed: {str(e)}"],
                warnings=warnings,
                processing_time_ms=processing_time_ms,
                stages_completed=stages_completed,
                metadata={"error": str(e)},
                timestamp=datetime.now(timezone.utc)
            )
    
    def _process_validation_stage(self, data: Any, schema_name: Optional[str]) -> Tuple[Any, ValidationResult]:
        """Process validation stage"""
        validation_result = self.validator.validate_data(data, schema_name)
        
        # Use validated data if available, otherwise use original
        processed_data = validation_result.validated_data if validation_result.validated_data is not None else data
        
        return processed_data, validation_result
    
    def _process_filtering_stage(self, data: Any, custom_rules: Optional[List[FilterRule]]) -> Tuple[Any, FilterResult]:
        """Process filtering stage"""
        filter_result = self.filter.filter_data(data, custom_rules)
        return filter_result.filtered_data, filter_result
    
    def _process_sanitization_stage(self, data: Any) -> Tuple[Any, SanitizedData]:
        """Process sanitization stage"""
        strict_mode = self.config.mode in [ProcessingMode.STRICT, ProcessingMode.SECURE]
        sanitization_result = self.sanitizer.sanitize_data(data, strict_mode)
        return sanitization_result.data, sanitization_result
    
    def _process_transformation_stage(self, data: Any) -> Tuple[Any, NormalizedData]:
        """Process transformation stage"""
        transformation_result = self.transformer.normalize_data(data)
        return transformation_result.data, transformation_result
    
    def batch_process(self, data_list: List[Any], schema_name: Optional[str] = None,
                     custom_rules: Optional[List[FilterRule]] = None) -> List[PipelineResult]:
        """
        Process a batch of data items through the pipeline
        
        Args:
            data_list: List of data items to process
            schema_name: Optional schema name for validation
            custom_rules: Optional custom filtering rules
            
        Returns:
            List of PipelineResult objects
        """
        results = []
        batch_start_time = datetime.now(timezone.utc)
        
        self.logger.info(
            "Starting batch processing",
            batch_size=len(data_list),
            configured_batch_size=self.config.batch_size
        )
        
        # Process in chunks if batch is large
        chunk_size = min(self.config.batch_size, len(data_list))
        
        for i in range(0, len(data_list), chunk_size):
            chunk = data_list[i:i + chunk_size]
            chunk_results = []
            
            for j, item in enumerate(chunk):
                try:
                    result = self.process_data(item, schema_name, custom_rules)
                    chunk_results.append(result)
                except Exception as e:
                    self.logger.error(
                        "Batch item processing failed",
                        batch_index=i + j,
                        error=str(e)
                    )
                    # Create error result
                    chunk_results.append(PipelineResult(
                        original_data=item,
                        processed_data=item,
                        validation_result=None,
                        filter_result=None,
                        sanitization_result=None,
                        transformation_result=None,
                        success=False,
                        errors=[f"Batch processing failed: {str(e)}"],
                        warnings=[],
                        processing_time_ms=0.0,
                        stages_completed=[],
                        metadata={"batch_error": str(e), "batch_index": i + j},
                        timestamp=datetime.now(timezone.utc)
                    ))
            
            results.extend(chunk_results)
        
        batch_end_time = datetime.now(timezone.utc)
        batch_processing_time = (batch_end_time - batch_start_time).total_seconds() * 1000
        
        successful_count = len([r for r in results if r.success])
        failed_count = len(results) - successful_count
        
        self.logger.info(
            "Batch processing completed",
            total_items=len(data_list),
            successful_items=successful_count,
            failed_items=failed_count,
            batch_processing_time_ms=batch_processing_time
        )
        
        return results
    
    def _estimate_data_size(self, data: Any) -> int:
        """Estimate data size in bytes"""
        try:
            if isinstance(data, str):
                return len(data.encode('utf-8'))
            elif isinstance(data, (list, dict)):
                return len(str(data).encode('utf-8'))
            else:
                return len(str(data).encode('utf-8'))
        except:
            return 0
    
    def _calculate_data_complexity(self, data: Any) -> int:
        """Calculate data complexity score"""
        if isinstance(data, dict):
            return len(data) + sum(self._calculate_data_complexity(v) for v in data.values())
        elif isinstance(data, list):
            return len(data) + sum(self._calculate_data_complexity(item) for item in data)
        else:
            return 1
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get pipeline processing statistics"""
        return {
            'processing_stats': self.stats.copy(),
            'component_stats': {
                'validator': getattr(self.validator, 'stats', {}),
                'filter': self.filter.get_stats(),
                'sanitizer': getattr(self.sanitizer, 'stats', {}),
                'transformer': getattr(self.transformer, 'stats', {})
            },
            'configuration': {
                'mode': self.config.mode.value,
                'stages': [stage.value for stage in self.config.stages],
                'batch_size': self.config.batch_size,
                'timeout_seconds': self.config.timeout_seconds
            }
        }
    
    def reset_stats(self):
        """Reset pipeline statistics"""
        self.stats = {
            'total_processed': 0,
            'successful_processed': 0,
            'failed_processed': 0,
            'average_processing_time_ms': 0.0,
            'stage_stats': {stage.value: 0 for stage in PipelineStage}
        }
        self.logger.info("Pipeline statistics reset")
    
    def configure_for_telemetry(self):
        """Configure pipeline optimally for telemetry data processing"""
        self.config.mode = ProcessingMode.PERFORMANCE
        self.config.stages = [
            PipelineStage.VALIDATION,
            PipelineStage.FILTERING,
            PipelineStage.TRANSFORMATION
        ]
        # Register telemetry-specific validation schema
        # This would be done in practice
        self.logger.info("Pipeline configured for telemetry data processing")
    
    def configure_for_user_data(self):
        """Configure pipeline optimally for user data processing"""
        self.config.mode = ProcessingMode.SECURE
        self.config.stages = [
            PipelineStage.VALIDATION,
            PipelineStage.SANITIZATION,
            PipelineStage.FILTERING,
            PipelineStage.TRANSFORMATION
        ]
        self.logger.info("Pipeline configured for user data processing")
    
    def configure_for_performance_data(self):
        """Configure pipeline optimally for performance data processing"""
        self.config.mode = ProcessingMode.PERMISSIVE
        self.config.stages = [
            PipelineStage.VALIDATION,
            PipelineStage.TRANSFORMATION
        ]
        self.logger.info("Pipeline configured for performance data processing")