"""
Telemetry data processor for Observer Eye Platform.
Handles processing and enrichment of collected telemetry data.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

import structlog
from opentelemetry import trace

from .models import (
    TelemetryData, ProcessedTelemetry, TelemetryBatch, ProcessingStatus
)
from .exceptions import ProcessingError, EnrichmentError

logger = structlog.get_logger(__name__)
tracer = trace.get_tracer(__name__)


class TelemetryProcessor:
    """
    Telemetry data processor with enrichment and validation capabilities.
    """
    
    def __init__(
        self,
        processor_version: str = "1.0.0",
        enable_enrichment: bool = True,
        max_processing_time_seconds: float = 30.0
    ):
        self.processor_version = processor_version
        self.enable_enrichment = enable_enrichment
        self.max_processing_time_seconds = max_processing_time_seconds
        
        logger.info(
            "Telemetry processor initialized",
            processor_version=processor_version,
            enable_enrichment=enable_enrichment
        )
    
    async def process_single(
        self,
        telemetry: TelemetryData
    ) -> ProcessedTelemetry:
        """Process a single telemetry data point"""
        with tracer.start_as_current_span("process_single") as span:
            start_time = time.time()
            
            try:
                # Basic processing
                enriched_attributes = {}
                computed_metrics = {}
                derived_labels = {}
                errors = []
                warnings = []
                
                # Enrich data if enabled
                if self.enable_enrichment:
                    enrichment_result = await self._enrich_telemetry(telemetry)
                    enriched_attributes.update(enrichment_result.get("attributes", {}))
                    computed_metrics.update(enrichment_result.get("metrics", {}))
                    derived_labels.update(enrichment_result.get("labels", {}))
                    errors.extend(enrichment_result.get("errors", []))
                    warnings.extend(enrichment_result.get("warnings", []))
                
                processing_time = (time.time() - start_time) * 1000
                
                processed = ProcessedTelemetry(
                    original_data=telemetry,
                    processing_time_ms=processing_time,
                    status=ProcessingStatus.PROCESSED,
                    enriched_attributes=enriched_attributes,
                    computed_metrics=computed_metrics,
                    derived_labels=derived_labels,
                    processor_version=self.processor_version,
                    enrichment_sources=["basic_enricher"] if self.enable_enrichment else [],
                    processing_errors=errors,
                    warnings=warnings
                )
                
                span.set_attribute("telemetry.id", telemetry.id)
                span.set_attribute("processing.time_ms", processing_time)
                
                return processed
                
            except Exception as e:
                processing_time = (time.time() - start_time) * 1000
                span.record_exception(e)
                
                logger.error(
                    "Failed to process telemetry",
                    telemetry_id=telemetry.id,
                    error=str(e),
                    processing_time_ms=processing_time
                )
                
                # Return failed processing result
                return ProcessedTelemetry(
                    original_data=telemetry,
                    processing_time_ms=processing_time,
                    status=ProcessingStatus.FAILED,
                    processor_version=self.processor_version,
                    processing_errors=[str(e)]
                )
    
    async def _enrich_telemetry(self, telemetry: TelemetryData) -> Dict[str, Any]:
        """Enrich telemetry data with additional context"""
        result = {
            "attributes": {},
            "metrics": {},
            "labels": {},
            "errors": [],
            "warnings": []
        }
        
        try:
            # Add basic enrichment
            result["attributes"]["processing_timestamp"] = datetime.now(timezone.utc).isoformat()
            result["attributes"]["processor_version"] = self.processor_version
            
            # Derive additional labels
            if telemetry.service_name:
                result["labels"]["service"] = telemetry.service_name
            
            if telemetry.environment:
                result["labels"]["env"] = telemetry.environment
            
            # Compute basic metrics
            if isinstance(telemetry.value, (int, float)):
                result["metrics"]["numeric_value"] = float(telemetry.value)
            
        except Exception as e:
            result["errors"].append(f"Enrichment failed: {str(e)}")
        
        return result