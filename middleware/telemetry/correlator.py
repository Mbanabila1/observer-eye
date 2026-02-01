"""
Telemetry correlation engine for Observer Eye Platform.
Correlates related telemetry events across different sources and time windows.
"""

import asyncio
from typing import Any, Dict, List, Optional, Set
from datetime import datetime, timezone, timedelta
from collections import defaultdict

import structlog

from .models import (
    TelemetryData, ProcessedTelemetry, CorrelationRule, CorrelationResult,
    TelemetryType
)
from .exceptions import CorrelationError

logger = structlog.get_logger(__name__)


class TelemetryCorrelator:
    """
    Telemetry correlation engine that finds relationships between telemetry events.
    """
    
    def __init__(
        self,
        max_correlation_window_seconds: int = 3600,
        max_correlations_per_rule: int = 1000,
        enable_automatic_rules: bool = True
    ):
        self.max_correlation_window_seconds = max_correlation_window_seconds
        self.max_correlations_per_rule = max_correlations_per_rule
        self.enable_automatic_rules = enable_automatic_rules
        
        # Correlation rules
        self._correlation_rules: Dict[str, CorrelationRule] = {}
        
        # Telemetry data buffer for correlation
        self._telemetry_buffer: List[ProcessedTelemetry] = []
        self._buffer_lock = asyncio.Lock()
        
        # Correlation results cache
        self._correlation_results: List[CorrelationResult] = []
        
        # Initialize default rules
        if enable_automatic_rules:
            self._initialize_default_rules()
        
        logger.info(
            "Telemetry correlator initialized",
            max_correlation_window_seconds=max_correlation_window_seconds,
            enable_automatic_rules=enable_automatic_rules
        )
    
    def add_correlation_rule(self, rule: CorrelationRule) -> None:
        """Add a correlation rule"""
        self._correlation_rules[rule.id] = rule
        logger.info(
            "Correlation rule added",
            rule_id=rule.id,
            rule_name=rule.name
        )
    
    def remove_correlation_rule(self, rule_id: str) -> bool:
        """Remove a correlation rule"""
        if rule_id in self._correlation_rules:
            del self._correlation_rules[rule_id]
            logger.info("Correlation rule removed", rule_id=rule_id)
            return True
        return False
    
    async def correlate_telemetry(
        self,
        processed_telemetry: ProcessedTelemetry
    ) -> List[CorrelationResult]:
        """
        Correlate new telemetry with existing data.
        
        Args:
            processed_telemetry: New processed telemetry to correlate
        
        Returns:
            List[CorrelationResult]: Found correlations
        """
        try:
            # Add to buffer
            async with self._buffer_lock:
                self._telemetry_buffer.append(processed_telemetry)
                
                # Clean old entries
                await self._cleanup_buffer()
            
            # Find correlations
            correlations = []
            
            for rule in self._correlation_rules.values():
                if not rule.is_active:
                    continue
                
                rule_correlations = await self._apply_correlation_rule(
                    rule, processed_telemetry
                )
                correlations.extend(rule_correlations)
            
            # Store correlation results
            self._correlation_results.extend(correlations)
            
            if correlations:
                logger.info(
                    "Correlations found",
                    telemetry_id=processed_telemetry.original_data.id,
                    correlation_count=len(correlations)
                )
            
            return correlations
            
        except Exception as e:
            logger.error(
                "Failed to correlate telemetry",
                telemetry_id=processed_telemetry.original_data.id,
                error=str(e)
            )
            raise CorrelationError(
                message=f"Correlation failed: {str(e)}",
                telemetry_ids=[processed_telemetry.original_data.id]
            )
    
    async def _apply_correlation_rule(
        self,
        rule: CorrelationRule,
        new_telemetry: ProcessedTelemetry
    ) -> List[CorrelationResult]:
        """Apply a correlation rule to find matches"""
        correlations = []
        
        try:
            # Check if new telemetry matches rule source types
            if new_telemetry.original_data.type not in rule.source_types:
                return correlations
            
            # Find potential correlations in buffer
            async with self._buffer_lock:
                candidates = self._find_correlation_candidates(rule, new_telemetry)
            
            # Evaluate each candidate
            for candidate in candidates:
                correlation_score = self._calculate_correlation_score(
                    rule, new_telemetry, candidate
                )
                
                if correlation_score >= rule.similarity_threshold:
                    correlation = CorrelationResult(
                        rule_id=rule.id,
                        primary_telemetry_id=new_telemetry.original_data.id,
                        correlated_telemetry_ids=[candidate.original_data.id],
                        correlation_score=correlation_score,
                        correlation_type=self._determine_correlation_type(rule, new_telemetry, candidate),
                        correlation_reason=self._generate_correlation_reason(rule, new_telemetry, candidate),
                        time_span_seconds=abs(
                            (new_telemetry.original_data.timestamp - 
                             candidate.original_data.timestamp).total_seconds()
                        )
                    )
                    
                    correlations.append(correlation)
            
            # Limit correlations per rule
            if len(correlations) > rule.max_correlations:
                correlations = sorted(
                    correlations,
                    key=lambda x: x.correlation_score,
                    reverse=True
                )[:rule.max_correlations]
            
        except Exception as e:
            logger.error(
                "Failed to apply correlation rule",
                rule_id=rule.id,
                telemetry_id=new_telemetry.original_data.id,
                error=str(e)
            )
        
        return correlations
    
    def _find_correlation_candidates(
        self,
        rule: CorrelationRule,
        new_telemetry: ProcessedTelemetry
    ) -> List[ProcessedTelemetry]:
        """Find potential correlation candidates"""
        candidates = []
        
        # Time window for correlation
        time_window = timedelta(seconds=rule.time_window_seconds)
        cutoff_time = new_telemetry.original_data.timestamp - time_window
        
        for telemetry in self._telemetry_buffer:
            # Skip self
            if telemetry.original_data.id == new_telemetry.original_data.id:
                continue
            
            # Check time window
            if telemetry.original_data.timestamp < cutoff_time:
                continue
            
            # Check target types
            if telemetry.original_data.type not in rule.target_types:
                continue
            
            candidates.append(telemetry)
        
        return candidates
    
    def _calculate_correlation_score(
        self,
        rule: CorrelationRule,
        telemetry1: ProcessedTelemetry,
        telemetry2: ProcessedTelemetry
    ) -> float:
        """Calculate correlation score between two telemetry items"""
        score = 0.0
        total_weight = 0.0
        
        # Check matching fields
        for field in rule.match_fields:
            weight = 1.0
            
            value1 = self._get_field_value(telemetry1.original_data, field)
            value2 = self._get_field_value(telemetry2.original_data, field)
            
            if value1 is not None and value2 is not None:
                if value1 == value2:
                    score += weight
                elif isinstance(value1, str) and isinstance(value2, str):
                    # String similarity
                    similarity = self._calculate_string_similarity(value1, value2)
                    score += similarity * weight
            
            total_weight += weight
        
        # Normalize score
        if total_weight > 0:
            score = score / total_weight
        
        return min(1.0, score)
    
    def _get_field_value(self, telemetry: TelemetryData, field: str) -> Any:
        """Get field value from telemetry data"""
        if hasattr(telemetry, field):
            return getattr(telemetry, field)
        
        if field in telemetry.labels:
            return telemetry.labels[field]
        
        if field in telemetry.attributes:
            return telemetry.attributes[field]
        
        return None
    
    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity (simple implementation)"""
        if str1 == str2:
            return 1.0
        
        # Simple Jaccard similarity
        set1 = set(str1.lower().split())
        set2 = set(str2.lower().split())
        
        if not set1 and not set2:
            return 1.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def _determine_correlation_type(
        self,
        rule: CorrelationRule,
        telemetry1: ProcessedTelemetry,
        telemetry2: ProcessedTelemetry
    ) -> str:
        """Determine the type of correlation"""
        if telemetry1.original_data.trace_id and telemetry2.original_data.trace_id:
            if telemetry1.original_data.trace_id == telemetry2.original_data.trace_id:
                return "trace_correlation"
        
        if telemetry1.original_data.service_name == telemetry2.original_data.service_name:
            return "service_correlation"
        
        if telemetry1.original_data.host == telemetry2.original_data.host:
            return "host_correlation"
        
        return "pattern_correlation"
    
    def _generate_correlation_reason(
        self,
        rule: CorrelationRule,
        telemetry1: ProcessedTelemetry,
        telemetry2: ProcessedTelemetry
    ) -> str:
        """Generate human-readable correlation reason"""
        reasons = []
        
        for field in rule.match_fields:
            value1 = self._get_field_value(telemetry1.original_data, field)
            value2 = self._get_field_value(telemetry2.original_data, field)
            
            if value1 == value2 and value1 is not None:
                reasons.append(f"matching {field}: {value1}")
        
        if not reasons:
            reasons.append("pattern match")
        
        return ", ".join(reasons)
    
    async def _cleanup_buffer(self) -> None:
        """Clean up old telemetry from buffer"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(
            seconds=self.max_correlation_window_seconds
        )
        
        self._telemetry_buffer = [
            t for t in self._telemetry_buffer
            if t.original_data.timestamp >= cutoff_time
        ]
    
    def _initialize_default_rules(self) -> None:
        """Initialize default correlation rules"""
        # Error correlation rule
        error_rule = CorrelationRule(
            name="Error Correlation",
            description="Correlate error events across services",
            source_types=[TelemetryType.LOG, TelemetryType.EVENT],
            target_types=[TelemetryType.LOG, TelemetryType.EVENT, TelemetryType.METRIC],
            time_window_seconds=300,  # 5 minutes
            match_fields=["service_name", "trace_id", "user_id"],
            similarity_threshold=0.7
        )
        self.add_correlation_rule(error_rule)
        
        # Performance correlation rule
        perf_rule = CorrelationRule(
            name="Performance Correlation",
            description="Correlate performance metrics with events",
            source_types=[TelemetryType.METRIC, TelemetryType.GAUGE],
            target_types=[TelemetryType.EVENT, TelemetryType.LOG],
            time_window_seconds=600,  # 10 minutes
            match_fields=["service_name", "host"],
            similarity_threshold=0.8
        )
        self.add_correlation_rule(perf_rule)
    
    def get_correlation_results(
        self,
        limit: int = 100,
        rule_id: Optional[str] = None
    ) -> List[CorrelationResult]:
        """Get correlation results"""
        results = self._correlation_results
        
        if rule_id:
            results = [r for r in results if r.rule_id == rule_id]
        
        # Sort by creation time (most recent first)
        results = sorted(results, key=lambda x: x.created_at, reverse=True)
        
        return results[:limit]
    
    def get_correlation_rules(self) -> List[CorrelationRule]:
        """Get all correlation rules"""
        return list(self._correlation_rules.values())