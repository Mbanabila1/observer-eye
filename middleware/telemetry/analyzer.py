"""
Telemetry analysis engine for Observer Eye Platform.
Performs pattern detection, anomaly detection, and trend analysis.
"""

import asyncio
import statistics
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from collections import defaultdict, deque

import structlog

from .models import (
    TelemetryData, ProcessedTelemetry, AnalysisPattern, AnalysisResult,
    TelemetryType, SeverityLevel
)
from .exceptions import AnalysisError

logger = structlog.get_logger(__name__)


class TelemetryAnalyzer:
    """
    Telemetry analysis engine for pattern detection and anomaly analysis.
    """
    
    def __init__(
        self,
        max_analysis_window_seconds: int = 3600,
        min_data_points_for_analysis: int = 10,
        enable_anomaly_detection: bool = True,
        enable_trend_analysis: bool = True
    ):
        self.max_analysis_window_seconds = max_analysis_window_seconds
        self.min_data_points_for_analysis = min_data_points_for_analysis
        self.enable_anomaly_detection = enable_anomaly_detection
        self.enable_trend_analysis = enable_trend_analysis
        
        # Analysis patterns
        self._analysis_patterns: Dict[str, AnalysisPattern] = {}
        
        # Telemetry data for analysis
        self._analysis_buffer: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self._buffer_lock = asyncio.Lock()
        
        # Analysis results
        self._analysis_results: List[AnalysisResult] = []
        
        # Initialize default patterns
        self._initialize_default_patterns()
        
        logger.info(
            "Telemetry analyzer initialized",
            max_analysis_window_seconds=max_analysis_window_seconds,
            enable_anomaly_detection=enable_anomaly_detection,
            enable_trend_analysis=enable_trend_analysis
        )
    
    def add_analysis_pattern(self, pattern: AnalysisPattern) -> None:
        """Add an analysis pattern"""
        self._analysis_patterns[pattern.id] = pattern
        logger.info(
            "Analysis pattern added",
            pattern_id=pattern.id,
            pattern_name=pattern.name,
            pattern_type=pattern.pattern_type
        )
    
    def remove_analysis_pattern(self, pattern_id: str) -> bool:
        """Remove an analysis pattern"""
        if pattern_id in self._analysis_patterns:
            del self._analysis_patterns[pattern_id]
            logger.info("Analysis pattern removed", pattern_id=pattern_id)
            return True
        return False
    
    async def analyze_telemetry(
        self,
        processed_telemetry: ProcessedTelemetry
    ) -> List[AnalysisResult]:
        """
        Analyze new telemetry data for patterns and anomalies.
        
        Args:
            processed_telemetry: Processed telemetry to analyze
        
        Returns:
            List[AnalysisResult]: Analysis results
        """
        try:
            # Add to analysis buffer
            async with self._buffer_lock:
                buffer_key = self._get_buffer_key(processed_telemetry.original_data)
                self._analysis_buffer[buffer_key].append(processed_telemetry)
                
                # Clean old entries
                await self._cleanup_analysis_buffer()
            
            # Run analysis patterns
            analysis_results = []
            
            for pattern in self._analysis_patterns.values():
                if not pattern.is_active:
                    continue
                
                if processed_telemetry.original_data.type not in pattern.telemetry_types:
                    continue
                
                pattern_results = await self._apply_analysis_pattern(
                    pattern, processed_telemetry
                )
                analysis_results.extend(pattern_results)
            
            # Store analysis results
            self._analysis_results.extend(analysis_results)
            
            if analysis_results:
                logger.info(
                    "Analysis completed",
                    telemetry_id=processed_telemetry.original_data.id,
                    results_count=len(analysis_results)
                )
            
            return analysis_results
            
        except Exception as e:
            logger.error(
                "Failed to analyze telemetry",
                telemetry_id=processed_telemetry.original_data.id,
                error=str(e)
            )
            raise AnalysisError(
                message=f"Analysis failed: {str(e)}",
                telemetry_ids=[processed_telemetry.original_data.id]
            )
    
    async def _apply_analysis_pattern(
        self,
        pattern: AnalysisPattern,
        new_telemetry: ProcessedTelemetry
    ) -> List[AnalysisResult]:
        """Apply an analysis pattern"""
        results = []
        
        try:
            if pattern.pattern_type == "anomaly":
                result = await self._detect_anomaly(pattern, new_telemetry)
                if result:
                    results.append(result)
            
            elif pattern.pattern_type == "threshold":
                result = await self._check_threshold(pattern, new_telemetry)
                if result:
                    results.append(result)
            
            elif pattern.pattern_type == "trend":
                result = await self._analyze_trend(pattern, new_telemetry)
                if result:
                    results.append(result)
            
            elif pattern.pattern_type == "spike":
                result = await self._detect_spike(pattern, new_telemetry)
                if result:
                    results.append(result)
            
        except Exception as e:
            logger.error(
                "Failed to apply analysis pattern",
                pattern_id=pattern.id,
                pattern_type=pattern.pattern_type,
                error=str(e)
            )
        
        return results
    
    async def _detect_anomaly(
        self,
        pattern: AnalysisPattern,
        new_telemetry: ProcessedTelemetry
    ) -> Optional[AnalysisResult]:
        """Detect anomalies using statistical analysis"""
        buffer_key = self._get_buffer_key(new_telemetry.original_data)
        
        async with self._buffer_lock:
            buffer = self._analysis_buffer[buffer_key]
            
            if len(buffer) < pattern.min_data_points:
                return None
            
            # Get recent data points
            recent_data = list(buffer)[-pattern.min_data_points:]
            
            # Extract numeric values
            values = []
            for telemetry in recent_data:
                if isinstance(telemetry.original_data.value, (int, float)):
                    values.append(float(telemetry.original_data.value))
            
            if len(values) < pattern.min_data_points:
                return None
            
            # Calculate statistics
            mean_val = statistics.mean(values[:-1])  # Exclude current value
            std_dev = statistics.stdev(values[:-1]) if len(values) > 2 else 0
            current_value = values[-1]
            
            # Z-score anomaly detection
            if std_dev > 0:
                z_score = abs(current_value - mean_val) / std_dev
                threshold = pattern.parameters.get("z_score_threshold", 3.0)
                
                if z_score > threshold:
                    confidence = min(1.0, z_score / (threshold * 2))
                    
                    return AnalysisResult(
                        pattern_id=pattern.id,
                        telemetry_ids=[new_telemetry.original_data.id],
                        pattern_detected=True,
                        confidence_score=confidence,
                        severity=self._determine_severity(confidence),
                        finding_type="statistical_anomaly",
                        description=f"Statistical anomaly detected: value {current_value} deviates {z_score:.2f} standard deviations from mean {mean_val:.2f}",
                        time_range_start=recent_data[0].original_data.timestamp,
                        time_range_end=new_telemetry.original_data.timestamp,
                        statistics={
                            "mean": mean_val,
                            "std_dev": std_dev,
                            "z_score": z_score,
                            "current_value": current_value
                        },
                        data_points_analyzed=len(values),
                        recommendations=[
                            "Investigate the cause of the anomalous value",
                            "Check for system issues or configuration changes",
                            "Monitor for additional anomalies"
                        ]
                    )
        
        return None
    
    async def _check_threshold(
        self,
        pattern: AnalysisPattern,
        new_telemetry: ProcessedTelemetry
    ) -> Optional[AnalysisResult]:
        """Check threshold violations"""
        if not isinstance(new_telemetry.original_data.value, (int, float)):
            return None
        
        current_value = float(new_telemetry.original_data.value)
        
        # Check thresholds
        for threshold_name, threshold_value in pattern.thresholds.items():
            violated = False
            description = ""
            
            if threshold_name == "max" and current_value > threshold_value:
                violated = True
                description = f"Maximum threshold exceeded: {current_value} > {threshold_value}"
            elif threshold_name == "min" and current_value < threshold_value:
                violated = True
                description = f"Minimum threshold violated: {current_value} < {threshold_value}"
            
            if violated:
                # Calculate confidence based on how much threshold is exceeded
                if threshold_name == "max":
                    confidence = min(1.0, (current_value - threshold_value) / threshold_value)
                else:
                    confidence = min(1.0, (threshold_value - current_value) / threshold_value)
                
                confidence = max(0.1, confidence)  # Minimum confidence
                
                return AnalysisResult(
                    pattern_id=pattern.id,
                    telemetry_ids=[new_telemetry.original_data.id],
                    pattern_detected=True,
                    confidence_score=confidence,
                    severity=self._determine_severity(confidence),
                    finding_type="threshold_violation",
                    description=description,
                    time_range_start=new_telemetry.original_data.timestamp,
                    time_range_end=new_telemetry.original_data.timestamp,
                    statistics={
                        "current_value": current_value,
                        "threshold_value": threshold_value,
                        "threshold_type": threshold_name
                    },
                    data_points_analyzed=1,
                    recommendations=[
                        f"Investigate why {threshold_name} threshold was exceeded",
                        "Check system capacity and configuration",
                        "Consider adjusting thresholds if appropriate"
                    ]
                )
        
        return None
    
    async def _analyze_trend(
        self,
        pattern: AnalysisPattern,
        new_telemetry: ProcessedTelemetry
    ) -> Optional[AnalysisResult]:
        """Analyze trends in telemetry data"""
        buffer_key = self._get_buffer_key(new_telemetry.original_data)
        
        async with self._buffer_lock:
            buffer = self._analysis_buffer[buffer_key]
            
            if len(buffer) < pattern.min_data_points:
                return None
            
            # Get recent data points
            recent_data = list(buffer)[-pattern.min_data_points:]
            
            # Extract numeric values with timestamps
            data_points = []
            for telemetry in recent_data:
                if isinstance(telemetry.original_data.value, (int, float)):
                    data_points.append({
                        "timestamp": telemetry.original_data.timestamp,
                        "value": float(telemetry.original_data.value)
                    })
            
            if len(data_points) < pattern.min_data_points:
                return None
            
            # Calculate trend
            trend_result = self._calculate_trend(data_points)
            
            if trend_result["significant"]:
                return AnalysisResult(
                    pattern_id=pattern.id,
                    telemetry_ids=[t.original_data.id for t in recent_data],
                    pattern_detected=True,
                    confidence_score=trend_result["confidence"],
                    severity=self._determine_severity(trend_result["confidence"]),
                    finding_type="trend_analysis",
                    description=trend_result["description"],
                    time_range_start=data_points[0]["timestamp"],
                    time_range_end=data_points[-1]["timestamp"],
                    statistics=trend_result["statistics"],
                    data_points_analyzed=len(data_points),
                    recommendations=trend_result["recommendations"]
                )
        
        return None
    
    async def _detect_spike(
        self,
        pattern: AnalysisPattern,
        new_telemetry: ProcessedTelemetry
    ) -> Optional[AnalysisResult]:
        """Detect sudden spikes in telemetry data"""
        buffer_key = self._get_buffer_key(new_telemetry.original_data)
        
        async with self._buffer_lock:
            buffer = self._analysis_buffer[buffer_key]
            
            if len(buffer) < 3:  # Need at least 3 points for spike detection
                return None
            
            # Get last few data points
            recent_data = list(buffer)[-3:]
            
            # Extract numeric values
            values = []
            for telemetry in recent_data:
                if isinstance(telemetry.original_data.value, (int, float)):
                    values.append(float(telemetry.original_data.value))
            
            if len(values) < 3:
                return None
            
            # Check for spike (current value significantly higher than previous)
            current_value = values[-1]
            previous_value = values[-2]
            baseline = statistics.mean(values[:-1])
            
            spike_threshold = pattern.parameters.get("spike_multiplier", 2.0)
            
            if current_value > baseline * spike_threshold and current_value > previous_value * spike_threshold:
                confidence = min(1.0, current_value / (baseline * spike_threshold))
                
                return AnalysisResult(
                    pattern_id=pattern.id,
                    telemetry_ids=[new_telemetry.original_data.id],
                    pattern_detected=True,
                    confidence_score=confidence,
                    severity=self._determine_severity(confidence),
                    finding_type="spike_detection",
                    description=f"Spike detected: current value {current_value} is {current_value/baseline:.2f}x the baseline {baseline}",
                    time_range_start=recent_data[0].original_data.timestamp,
                    time_range_end=new_telemetry.original_data.timestamp,
                    statistics={
                        "current_value": current_value,
                        "previous_value": previous_value,
                        "baseline": baseline,
                        "spike_ratio": current_value / baseline
                    },
                    data_points_analyzed=len(values),
                    recommendations=[
                        "Investigate the cause of the sudden spike",
                        "Check for system load or configuration changes",
                        "Monitor for sustained high values"
                    ]
                )
        
        return None
    
    def _get_buffer_key(self, telemetry: TelemetryData) -> str:
        """Generate buffer key for telemetry data"""
        key_parts = [
            telemetry.type.value,
            telemetry.source.value,
            telemetry.name,
            telemetry.service_name or "unknown",
            telemetry.host or "unknown"
        ]
        return ":".join(key_parts)
    
    def _calculate_trend(self, data_points: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate trend in data points"""
        if len(data_points) < 2:
            return {"significant": False}
        
        # Simple linear regression
        n = len(data_points)
        x_values = list(range(n))
        y_values = [dp["value"] for dp in data_points]
        
        # Calculate slope
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(y_values)
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        if denominator == 0:
            return {"significant": False}
        
        slope = numerator / denominator
        
        # Determine if trend is significant
        threshold = 0.1  # Minimum slope for significance
        significant = abs(slope) > threshold
        
        if significant:
            trend_direction = "increasing" if slope > 0 else "decreasing"
            confidence = min(1.0, abs(slope) / threshold)
            
            return {
                "significant": True,
                "confidence": confidence,
                "description": f"{trend_direction.capitalize()} trend detected with slope {slope:.4f}",
                "statistics": {
                    "slope": slope,
                    "trend_direction": trend_direction,
                    "start_value": y_values[0],
                    "end_value": y_values[-1],
                    "change_percent": ((y_values[-1] - y_values[0]) / y_values[0] * 100) if y_values[0] != 0 else 0
                },
                "recommendations": [
                    f"Monitor the {trend_direction} trend",
                    "Investigate underlying causes",
                    "Consider capacity planning if trend continues"
                ]
            }
        
        return {"significant": False}
    
    def _determine_severity(self, confidence: float) -> SeverityLevel:
        """Determine severity based on confidence score"""
        if confidence >= 0.9:
            return SeverityLevel.CRITICAL
        elif confidence >= 0.7:
            return SeverityLevel.ERROR
        elif confidence >= 0.5:
            return SeverityLevel.WARNING
        else:
            return SeverityLevel.INFO
    
    async def _cleanup_analysis_buffer(self) -> None:
        """Clean up old telemetry from analysis buffer"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(
            seconds=self.max_analysis_window_seconds
        )
        
        for buffer_key in list(self._analysis_buffer.keys()):
            buffer = self._analysis_buffer[buffer_key]
            
            # Remove old entries
            while buffer and buffer[0].original_data.timestamp < cutoff_time:
                buffer.popleft()
            
            # Remove empty buffers
            if not buffer:
                del self._analysis_buffer[buffer_key]
    
    def _initialize_default_patterns(self) -> None:
        """Initialize default analysis patterns"""
        # Anomaly detection pattern
        anomaly_pattern = AnalysisPattern(
            name="Statistical Anomaly Detection",
            description="Detect statistical anomalies using z-score analysis",
            pattern_type="anomaly",
            telemetry_types=[TelemetryType.METRIC, TelemetryType.GAUGE, TelemetryType.COUNTER],
            analysis_window_seconds=1800,  # 30 minutes
            parameters={"z_score_threshold": 3.0},
            min_data_points=10
        )
        self.add_analysis_pattern(anomaly_pattern)
        
        # Threshold pattern
        threshold_pattern = AnalysisPattern(
            name="Threshold Monitoring",
            description="Monitor threshold violations",
            pattern_type="threshold",
            telemetry_types=[TelemetryType.METRIC, TelemetryType.GAUGE],
            analysis_window_seconds=300,  # 5 minutes
            thresholds={"max": 100.0, "min": 0.0},
            min_data_points=1
        )
        self.add_analysis_pattern(threshold_pattern)
        
        # Spike detection pattern
        spike_pattern = AnalysisPattern(
            name="Spike Detection",
            description="Detect sudden spikes in metrics",
            pattern_type="spike",
            telemetry_types=[TelemetryType.METRIC, TelemetryType.COUNTER],
            analysis_window_seconds=600,  # 10 minutes
            parameters={"spike_multiplier": 3.0},
            min_data_points=3
        )
        self.add_analysis_pattern(spike_pattern)
    
    def get_analysis_results(
        self,
        limit: int = 100,
        pattern_id: Optional[str] = None,
        severity: Optional[SeverityLevel] = None
    ) -> List[AnalysisResult]:
        """Get analysis results"""
        results = self._analysis_results
        
        if pattern_id:
            results = [r for r in results if r.pattern_id == pattern_id]
        
        if severity:
            results = [r for r in results if r.severity == severity]
        
        # Sort by analysis timestamp (most recent first)
        results = sorted(results, key=lambda x: x.analysis_timestamp, reverse=True)
        
        return results[:limit]
    
    def get_analysis_patterns(self) -> List[AnalysisPattern]:
        """Get all analysis patterns"""
        return list(self._analysis_patterns.values())