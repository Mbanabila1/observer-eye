"""
Telemetry data enricher for Observer Eye Platform.
Adds contextual information and metadata to telemetry data.
"""

import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

import structlog
import httpx

from .models import TelemetryData, ProcessedTelemetry
from .exceptions import EnrichmentError

logger = structlog.get_logger(__name__)


class TelemetryEnricher:
    """
    Telemetry data enricher that adds contextual information.
    """
    
    def __init__(
        self,
        django_base_url: str = "http://localhost:8000",
        enable_service_lookup: bool = True,
        enable_geo_lookup: bool = False,
        cache_ttl_seconds: int = 300
    ):
        self.django_base_url = django_base_url.rstrip('/')
        self.enable_service_lookup = enable_service_lookup
        self.enable_geo_lookup = enable_geo_lookup
        self.cache_ttl_seconds = cache_ttl_seconds
        
        # HTTP client for external lookups
        self.http_client = httpx.AsyncClient(timeout=httpx.Timeout(10.0))
        
        # Simple in-memory cache
        self._cache: Dict[str, Dict[str, Any]] = {}
        
        logger.info(
            "Telemetry enricher initialized",
            django_base_url=django_base_url,
            enable_service_lookup=enable_service_lookup,
            enable_geo_lookup=enable_geo_lookup
        )
    
    async def enrich(
        self,
        processed_telemetry: ProcessedTelemetry
    ) -> ProcessedTelemetry:
        """
        Enrich processed telemetry with additional context.
        
        Args:
            processed_telemetry: Processed telemetry to enrich
        
        Returns:
            ProcessedTelemetry: Enriched telemetry data
        """
        try:
            telemetry = processed_telemetry.original_data
            
            # Service information enrichment
            if self.enable_service_lookup and telemetry.service_name:
                service_info = await self._get_service_info(telemetry.service_name)
                if service_info:
                    processed_telemetry.enriched_attributes.update({
                        "service_info": service_info
                    })
                    processed_telemetry.enrichment_sources.append("service_lookup")
            
            # Geographic enrichment (if IP available)
            if self.enable_geo_lookup and telemetry.attributes.get("source_ip"):
                geo_info = await self._get_geo_info(telemetry.attributes["source_ip"])
                if geo_info:
                    processed_telemetry.enriched_attributes.update({
                        "geo_info": geo_info
                    })
                    processed_telemetry.enrichment_sources.append("geo_lookup")
            
            # Add timestamp-based enrichment
            time_info = self._get_time_context(telemetry.timestamp)
            processed_telemetry.enriched_attributes.update({
                "time_context": time_info
            })
            processed_telemetry.enrichment_sources.append("time_context")
            
            # Update status
            processed_telemetry.status = "enriched"
            
            return processed_telemetry
            
        except Exception as e:
            logger.error(
                "Failed to enrich telemetry",
                telemetry_id=processed_telemetry.original_data.id,
                error=str(e)
            )
            
            processed_telemetry.processing_errors.append(f"Enrichment failed: {str(e)}")
            return processed_telemetry
    
    async def _get_service_info(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get service information from Django backend"""
        cache_key = f"service:{service_name}"
        
        # Check cache first
        if cache_key in self._cache:
            cached_data = self._cache[cache_key]
            if (datetime.now(timezone.utc) - cached_data["cached_at"]).total_seconds() < self.cache_ttl_seconds:
                return cached_data["data"]
        
        try:
            # Query Django backend for service info
            url = f"{self.django_base_url}/api/services/{service_name}/"
            response = await self.http_client.get(url)
            
            if response.status_code == 200:
                service_data = response.json()
                
                # Cache the result
                self._cache[cache_key] = {
                    "data": service_data,
                    "cached_at": datetime.now(timezone.utc)
                }
                
                return service_data
            
        except Exception as e:
            logger.warning(
                "Failed to lookup service info",
                service_name=service_name,
                error=str(e)
            )
        
        return None
    
    async def _get_geo_info(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Get geographic information for IP address"""
        cache_key = f"geo:{ip_address}"
        
        # Check cache first
        if cache_key in self._cache:
            cached_data = self._cache[cache_key]
            if (datetime.now(timezone.utc) - cached_data["cached_at"]).total_seconds() < self.cache_ttl_seconds:
                return cached_data["data"]
        
        try:
            # This would typically use a geo IP service
            # For now, return basic info
            geo_data = {
                "ip": ip_address,
                "country": "Unknown",
                "city": "Unknown",
                "timezone": "UTC"
            }
            
            # Cache the result
            self._cache[cache_key] = {
                "data": geo_data,
                "cached_at": datetime.now(timezone.utc)
            }
            
            return geo_data
            
        except Exception as e:
            logger.warning(
                "Failed to lookup geo info",
                ip_address=ip_address,
                error=str(e)
            )
        
        return None
    
    def _get_time_context(self, timestamp: datetime) -> Dict[str, Any]:
        """Get time-based context information"""
        return {
            "hour_of_day": timestamp.hour,
            "day_of_week": timestamp.weekday(),
            "is_weekend": timestamp.weekday() >= 5,
            "is_business_hours": 9 <= timestamp.hour <= 17,
            "quarter": (timestamp.month - 1) // 3 + 1,
            "timezone": str(timestamp.tzinfo) if timestamp.tzinfo else "UTC"
        }
    
    async def close(self) -> None:
        """Close HTTP client"""
        await self.http_client.aclose()