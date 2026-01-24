"""
Real-Time Correlation Engine

Implements millisecond-precision correlation across all four pillars of observability.
Provides real-time cross-pillar data correlation, pattern detection, and deep system
integration for comprehensive observability insights.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import structlog

from .base_processor import ProcessingResult, PillarType, ProcessingStatus

logger = structlog.get_logger(__name__)

class CorrelationStrength(Enum):
    """Correlation strength levels"""
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"

class CorrelationType(Enum):
    """Types of correlations detected"""
    TEMPORAL = "temporal"          # Time-based correlation
    CAUSAL = "causal"             # Cause-effect relationship
    CONTEXTUAL = "contextual"     # Same context (user, session, service)
    PERFORMANCE = "performance"   # Performance-related correlation
    ERROR = "error"               # Error propagation correlation
    SYSTEM = "system"             # System-level correlation
    SECURITY = "security"         # Security-related correlation

@dataclass
class CorrelationCandidate:
    """A candidate for correlation between data points"""
    id: str
    pillar_type: PillarType
    timestamp: float
    correlation_hints: List[str]
    data_summary: Dict[str, Any]
    processing_result: ProcessingResult

@dataclass
class CorrelationMatch:
    """A detected correlation between multiple data points"""
    correlation_id: str
    correlation_type: CorrelationType
    strength: CorrelationStrength
    candidates: List[CorrelationCandidate]
    confidence_score: float
    temporal_window_ms: float
    correlation_evidence: Dict[str, Any]
    deep_system_context: Optional[Dict[str, Any]] = None
    created_at: float = field(default_factory=time.time)

@dataclass
class CorrelationWindow:
    """Time window for correlation analysis"""
    start_time: float
    end_time: float
    candidates: List[CorrelationCandidate] = field(default_factory=list)
    
    @property
    def duration_ms(self) -> float:
        return (self.end_time - self.start_time) * 1000

class RealTimeCorrelationEngine:
    """
    Real-time correlation engine with millisecond precision.
    
    Correlates data across all four pillars of observability using temporal,
    contextual, and causal analysis with deep system integration.
    """
    
    def __init__(self, 
                 correlation_window_ms: float = 5000,  # 5 second correlation window
                 max_candidates_per_window: int = 1000,
                 correlation_threshold: float = 0.7):
        self.correlation_window_ms = correlation_window_ms
        self.max_candidates_per_window = max_candidates_per_window
        self.correlation_threshold = correlation_threshold
        
        # Correlation state
        self._correlation_windows = deque(maxlen=100)  # Keep last 100 windows
        self._active_correlations = {}  # correlation_id -> CorrelationMatch
        self._correlation_cache = {}    # hint -> List[CorrelationCandidate]
        self._correlation_patterns = defaultdict(int)  # pattern -> count
        
        # Performance tracking
        self._correlation_stats = {
            'total_candidates_processed': 0,
            'correlations_found': 0,
            'average_correlation_time_ms': 0.0,
            'correlation_success_rate': 0.0
        }
        
        # Background tasks
        self._correlation_task = None
        self._cleanup_task = None
        
    async def start(self):
        """Start the correlation engine background tasks"""
        self._correlation_task = asyncio.create_task(self._correlation_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Real-time correlation engine started")
    
    async def stop(self):
        """Stop the correlation engine background tasks"""
        if self._correlation_task:
            self._correlation_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()
        logger.info("Real-time correlation engine stopped")
    
    async def add_candidate(self, processing_result: ProcessingResult) -> List[CorrelationMatch]:
        """
        Add a new correlation candidate and return any immediate correlations found.
        
        Args:
            processing_result: Result from pillar processor
            
        Returns:
            List of correlation matches found
        """
        start_time = time.time()
        
        try:
            # Create correlation candidate
            candidate = CorrelationCandidate(
                id=f"{processing_result.metadata.pillar_type.value}_{processing_result.metadata.correlation_id}",
                pillar_type=processing_result.metadata.pillar_type,
                timestamp=processing_result.metadata.processing_start_time,
                correlation_hints=processing_result.correlation_candidates,
                data_summary=self._create_data_summary(processing_result),
                processing_result=processing_result
            )
            
            # Add to current correlation window
            await self._add_to_correlation_window(candidate)
            
            # Update correlation cache
            await self._update_correlation_cache(candidate)
            
            # Find immediate correlations
            correlations = await self._find_correlations(candidate)
            
            # Update statistics
            self._correlation_stats['total_candidates_processed'] += 1
            if correlations:
                self._correlation_stats['correlations_found'] += len(correlations)
            
            processing_time_ms = (time.time() - start_time) * 1000
            self._update_average_correlation_time(processing_time_ms)
            
            logger.debug("Correlation candidate processed",
                        candidate_id=candidate.id,
                        correlations_found=len(correlations),
                        processing_time_ms=processing_time_ms)
            
            return correlations
            
        except Exception as e:
            logger.error("Error processing correlation candidate",
                        error=str(e),
                        pillar_type=processing_result.metadata.pillar_type.value)
            return []
    
    def _create_data_summary(self, processing_result: ProcessingResult) -> Dict[str, Any]:
        """Create a summary of the processed data for correlation"""
        
        processed_data = processing_result.processed_data
        
        summary = {
            'pillar_type': processing_result.metadata.pillar_type.value,
            'timestamp': processing_result.metadata.processing_start_time,
            'correlation_id': processing_result.metadata.correlation_id,
            'processing_duration_ms': processing_result.processing_latency_ms
        }
        
        # Add pillar-specific summary data
        if processing_result.metadata.pillar_type == PillarType.METRICS:
            summary.update({
                'metric_name': processed_data.get('metric_name'),
                'metric_value': processed_data.get('metric_value'),
                'metric_type': processed_data.get('metric_type'),
                'labels': processed_data.get('labels', {})
            })
        
        elif processing_result.metadata.pillar_type == PillarType.EVENTS:
            summary.update({
                'event_type': processed_data.get('event_type'),
                'severity': processed_data.get('severity'),
                'category': processed_data.get('category'),
                'source': processed_data.get('source')
            })
        
        elif processing_result.metadata.pillar_type == PillarType.LOGS:
            summary.update({
                'log_level': processed_data.get('level'),
                'logger_name': processed_data.get('logger_name'),
                'message_length': len(processed_data.get('message', '')),
                'has_structured_data': bool(processed_data.get('structured_data'))
            })
        
        elif processing_result.metadata.pillar_type == PillarType.TRACES:
            summary.update({
                'trace_id': processed_data.get('trace_id'),
                'span_id': processed_data.get('span_id'),
                'operation_name': processed_data.get('operation_name'),
                'duration_ms': processed_data.get('duration_ms'),
                'status': processed_data.get('status')
            })
        
        return summary
    
    async def _add_to_correlation_window(self, candidate: CorrelationCandidate):
        """Add candidate to the appropriate correlation window"""
        
        current_time = time.time()
        window_start = current_time - (self.correlation_window_ms / 1000)
        
        # Find or create current window
        current_window = None
        if self._correlation_windows and self._correlation_windows[-1].end_time > window_start:
            current_window = self._correlation_windows[-1]
        else:
            current_window = CorrelationWindow(
                start_time=window_start,
                end_time=current_time
            )
            self._correlation_windows.append(current_window)
        
        # Add candidate to window
        current_window.candidates.append(candidate)
        
        # Limit candidates per window
        if len(current_window.candidates) > self.max_candidates_per_window:
            current_window.candidates.pop(0)  # Remove oldest
    
    async def _update_correlation_cache(self, candidate: CorrelationCandidate):
        """Update correlation cache with candidate hints"""
        
        for hint in candidate.correlation_hints:
            if hint not in self._correlation_cache:
                self._correlation_cache[hint] = deque(maxlen=100)  # Keep last 100 per hint
            
            self._correlation_cache[hint].append(candidate)
    
    async def _find_correlations(self, candidate: CorrelationCandidate) -> List[CorrelationMatch]:
        """Find correlations for the given candidate"""
        
        correlations = []
        
        # Find candidates with matching hints
        matching_candidates = []
        
        for hint in candidate.correlation_hints:
            if hint in self._correlation_cache:
                for cached_candidate in self._correlation_cache[hint]:
                    # Skip self and candidates outside time window
                    if (cached_candidate.id != candidate.id and
                        abs(cached_candidate.timestamp - candidate.timestamp) <= (self.correlation_window_ms / 1000)):
                        if cached_candidate not in matching_candidates:  # Avoid duplicates
                            matching_candidates.append(cached_candidate)
        
        # Group candidates by correlation type and analyze
        correlation_groups = await self._group_candidates_by_correlation_type(candidate, list(matching_candidates))
        
        # Create correlation matches for strong correlations
        for correlation_type, candidates in correlation_groups.items():
            if len(candidates) >= 2:  # Need at least 2 candidates for correlation
                correlation_match = await self._create_correlation_match(
                    correlation_type, [candidate] + candidates
                )
                
                if correlation_match and correlation_match.confidence_score >= self.correlation_threshold:
                    correlations.append(correlation_match)
                    self._active_correlations[correlation_match.correlation_id] = correlation_match
        
        return correlations
    
    async def _group_candidates_by_correlation_type(
        self, 
        primary_candidate: CorrelationCandidate, 
        matching_candidates: List[CorrelationCandidate]
    ) -> Dict[CorrelationType, List[CorrelationCandidate]]:
        """Group candidates by correlation type"""
        
        groups = defaultdict(list)
        
        for candidate in matching_candidates:
            correlation_types = await self._determine_correlation_types(primary_candidate, candidate)
            
            for correlation_type in correlation_types:
                groups[correlation_type].append(candidate)
        
        return groups
    
    async def _determine_correlation_types(
        self, 
        candidate1: CorrelationCandidate, 
        candidate2: CorrelationCandidate
    ) -> List[CorrelationType]:
        """Determine correlation types between two candidates"""
        
        correlation_types = []
        
        # Temporal correlation (close in time)
        time_diff_ms = abs(candidate1.timestamp - candidate2.timestamp) * 1000
        if time_diff_ms <= 1000:  # Within 1 second
            correlation_types.append(CorrelationType.TEMPORAL)
        
        # Contextual correlation (same user, session, service, etc.)
        common_hints = set(candidate1.correlation_hints) & set(candidate2.correlation_hints)
        contextual_hints = [hint for hint in common_hints 
                           if any(prefix in hint for prefix in ['user:', 'session:', 'service:', 'trace:'])]
        if contextual_hints:
            correlation_types.append(CorrelationType.CONTEXTUAL)
        
        # Error correlation
        error_hints = [hint for hint in common_hints 
                      if any(keyword in hint for keyword in ['error', 'failure', 'exception'])]
        if error_hints:
            correlation_types.append(CorrelationType.ERROR)
        
        # Performance correlation
        performance_hints = [hint for hint in common_hints 
                           if any(keyword in hint for keyword in ['performance', 'slow', 'latency', 'timeout'])]
        if performance_hints:
            correlation_types.append(CorrelationType.PERFORMANCE)
        
        # System correlation
        system_hints = [hint for hint in common_hints 
                       if any(keyword in hint for keyword in ['system', 'kernel', 'hardware'])]
        if system_hints:
            correlation_types.append(CorrelationType.SYSTEM)
        
        # Security correlation
        security_hints = [hint for hint in common_hints 
                         if any(keyword in hint for keyword in ['security', 'auth', 'breach', 'attack'])]
        if security_hints:
            correlation_types.append(CorrelationType.SECURITY)
        
        # Causal correlation (based on pillar types and timing)
        if await self._detect_causal_relationship(candidate1, candidate2):
            correlation_types.append(CorrelationType.CAUSAL)
        
        return correlation_types
    
    async def _detect_causal_relationship(
        self, 
        candidate1: CorrelationCandidate, 
        candidate2: CorrelationCandidate
    ) -> bool:
        """Detect potential causal relationships between candidates"""
        
        # Order candidates by timestamp
        earlier, later = (candidate1, candidate2) if candidate1.timestamp <= candidate2.timestamp else (candidate2, candidate1)
        
        # Check for known causal patterns
        
        # Metric -> Event causality (metric threshold triggers event)
        if (earlier.pillar_type == PillarType.METRICS and 
            later.pillar_type == PillarType.EVENTS):
            
            # Check if metric indicates problem and event is error-related
            metric_data = earlier.data_summary
            event_data = later.data_summary
            
            if (metric_data.get('metric_name', '').lower() in ['error_rate', 'latency', 'cpu_usage'] and
                event_data.get('severity') in ['error', 'critical']):
                return True
        
        # Event -> Log causality (event triggers logging)
        if (earlier.pillar_type == PillarType.EVENTS and 
            later.pillar_type == PillarType.LOGS):
            
            event_data = earlier.data_summary
            log_data = later.data_summary
            
            if (event_data.get('severity') in ['error', 'critical'] and
                log_data.get('log_level') in ['error', 'fatal']):
                return True
        
        # Trace -> Metric causality (trace span affects metrics)
        if (earlier.pillar_type == PillarType.TRACES and 
            later.pillar_type == PillarType.METRICS):
            
            trace_data = earlier.data_summary
            metric_data = later.data_summary
            
            if (trace_data.get('status') == 'error' and
                'error' in metric_data.get('metric_name', '').lower()):
                return True
        
        return False
    
    async def _create_correlation_match(
        self, 
        correlation_type: CorrelationType, 
        candidates: List[CorrelationCandidate]
    ) -> Optional[CorrelationMatch]:
        """Create a correlation match from candidates"""
        
        if len(candidates) < 2:
            return None
        
        # Calculate confidence score
        confidence_score = await self._calculate_confidence_score(correlation_type, candidates)
        
        if confidence_score < self.correlation_threshold:
            return None
        
        # Determine correlation strength
        strength = self._determine_correlation_strength(confidence_score)
        
        # Calculate temporal window
        timestamps = [c.timestamp for c in candidates]
        temporal_window_ms = (max(timestamps) - min(timestamps)) * 1000
        
        # Gather correlation evidence
        evidence = await self._gather_correlation_evidence(correlation_type, candidates)
        
        # Create correlation ID
        correlation_id = f"corr_{correlation_type.value}_{int(time.time() * 1000)}_{hash(str(sorted([c.id for c in candidates]))) % 10000}"
        
        # Create deep system context if applicable
        deep_system_context = await self._create_deep_system_context(candidates)
        
        correlation_match = CorrelationMatch(
            correlation_id=correlation_id,
            correlation_type=correlation_type,
            strength=strength,
            candidates=candidates,
            confidence_score=confidence_score,
            temporal_window_ms=temporal_window_ms,
            correlation_evidence=evidence,
            deep_system_context=deep_system_context
        )
        
        # Update correlation patterns
        pattern_key = f"{correlation_type.value}_{len(candidates)}_pillars"
        self._correlation_patterns[pattern_key] += 1
        
        logger.info("Correlation match created",
                   correlation_id=correlation_id,
                   correlation_type=correlation_type.value,
                   strength=strength.value,
                   confidence_score=confidence_score,
                   candidates_count=len(candidates))
        
        return correlation_match
    
    async def _calculate_confidence_score(
        self, 
        correlation_type: CorrelationType, 
        candidates: List[CorrelationCandidate]
    ) -> float:
        """Calculate confidence score for correlation"""
        
        base_score = 0.5  # Base confidence
        
        # Temporal proximity bonus
        timestamps = [c.timestamp for c in candidates]
        time_span_ms = (max(timestamps) - min(timestamps)) * 1000
        
        if time_span_ms <= 100:  # Within 100ms
            base_score += 0.3
        elif time_span_ms <= 1000:  # Within 1 second
            base_score += 0.2
        elif time_span_ms <= 5000:  # Within 5 seconds
            base_score += 0.1
        
        # Common hints bonus
        all_hints = [hint for c in candidates for hint in c.correlation_hints]
        unique_hints = set(all_hints)
        common_hints = [hint for hint in unique_hints if all_hints.count(hint) >= 2]
        
        hint_bonus = min(0.3, len(common_hints) * 0.05)
        base_score += hint_bonus
        
        # Pillar diversity bonus (more pillars = stronger correlation)
        pillar_types = set(c.pillar_type for c in candidates)
        diversity_bonus = min(0.2, (len(pillar_types) - 1) * 0.1)
        base_score += diversity_bonus
        
        # Correlation type specific adjustments
        if correlation_type == CorrelationType.CAUSAL:
            base_score += 0.1  # Causal relationships are strong indicators
        elif correlation_type == CorrelationType.ERROR:
            base_score += 0.15  # Error correlations are very important
        elif correlation_type == CorrelationType.SECURITY:
            base_score += 0.2  # Security correlations are critical
        
        return min(1.0, base_score)
    
    def _determine_correlation_strength(self, confidence_score: float) -> CorrelationStrength:
        """Determine correlation strength from confidence score"""
        
        if confidence_score >= 0.9:
            return CorrelationStrength.VERY_STRONG
        elif confidence_score >= 0.8:
            return CorrelationStrength.STRONG
        elif confidence_score >= 0.7:
            return CorrelationStrength.MODERATE
        else:
            return CorrelationStrength.WEAK
    
    async def _gather_correlation_evidence(
        self, 
        correlation_type: CorrelationType, 
        candidates: List[CorrelationCandidate]
    ) -> Dict[str, Any]:
        """Gather evidence supporting the correlation"""
        
        evidence = {
            'correlation_type': correlation_type.value,
            'candidate_count': len(candidates),
            'pillar_types': [c.pillar_type.value for c in candidates],
            'time_span_ms': (max(c.timestamp for c in candidates) - min(c.timestamp for c in candidates)) * 1000
        }
        
        # Common correlation hints
        all_hints = [hint for c in candidates for hint in c.correlation_hints]
        unique_hints = set(all_hints)
        common_hints = [hint for hint in unique_hints if all_hints.count(hint) >= 2]
        evidence['common_hints'] = common_hints
        
        # Pillar-specific evidence
        pillar_evidence = {}
        for candidate in candidates:
            pillar_type = candidate.pillar_type.value
            if pillar_type not in pillar_evidence:
                pillar_evidence[pillar_type] = []
            
            pillar_evidence[pillar_type].append({
                'candidate_id': candidate.id,
                'timestamp': candidate.timestamp,
                'summary': candidate.data_summary
            })
        
        evidence['pillar_evidence'] = pillar_evidence
        
        # Correlation type specific evidence
        if correlation_type == CorrelationType.ERROR:
            error_indicators = []
            for candidate in candidates:
                summary = candidate.data_summary
                if (summary.get('severity') in ['error', 'critical'] or
                    summary.get('log_level') in ['error', 'fatal'] or
                    summary.get('status') == 'error'):
                    error_indicators.append(candidate.id)
            evidence['error_indicators'] = error_indicators
        
        elif correlation_type == CorrelationType.PERFORMANCE:
            performance_indicators = []
            for candidate in candidates:
                summary = candidate.data_summary
                if (summary.get('duration_ms', 0) > 1000 or  # Slow operations
                    'slow' in str(summary.get('metric_name', '')).lower() or
                    'latency' in str(summary.get('metric_name', '')).lower()):
                    performance_indicators.append(candidate.id)
            evidence['performance_indicators'] = performance_indicators
        
        return evidence
    
    async def _create_deep_system_context(self, candidates: List[CorrelationCandidate]) -> Optional[Dict[str, Any]]:
        """Create deep system context for correlation"""
        
        # Check if any candidates have system-level context
        system_candidates = [c for c in candidates 
                           if any('system' in hint or 'kernel' in hint for hint in c.correlation_hints)]
        
        if not system_candidates:
            return None
        
        return {
            'has_system_correlation': True,
            'system_candidates_count': len(system_candidates),
            'kernel_subsystems': list(set(
                hint.split(':')[1] for c in system_candidates 
                for hint in c.correlation_hints 
                if hint.startswith('kernel_subsystem:')
            )),
            'system_resources': list(set(
                hint.split(':')[1] for c in system_candidates 
                for hint in c.correlation_hints 
                if hint.startswith('system_resource:')
            ))
        }
    
    async def _correlation_loop(self):
        """Background correlation processing loop"""
        while True:
            try:
                await asyncio.sleep(1)  # Run every second
                
                # Process correlation windows for delayed correlations
                await self._process_correlation_windows()
                
                # Update correlation statistics
                self._update_correlation_statistics()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in correlation loop", error=str(e))
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _cleanup_loop(self):
        """Background cleanup loop"""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                
                # Clean up old correlations
                await self._cleanup_old_correlations()
                
                # Clean up correlation cache
                await self._cleanup_correlation_cache()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in cleanup loop", error=str(e))
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _process_correlation_windows(self):
        """Process correlation windows for delayed correlations"""
        
        current_time = time.time()
        
        # Process windows that are complete (older than correlation window)
        for window in list(self._correlation_windows):
            if current_time - window.end_time > (self.correlation_window_ms / 1000):
                # Process any remaining correlations in this window
                await self._process_window_correlations(window)
    
    async def _process_window_correlations(self, window: CorrelationWindow):
        """Process correlations within a specific window"""
        
        # This could implement more sophisticated correlation analysis
        # for patterns that emerge over time within the window
        pass
    
    async def _cleanup_old_correlations(self):
        """Clean up old correlations"""
        
        current_time = time.time()
        cleanup_threshold = 3600  # 1 hour
        
        old_correlations = [
            corr_id for corr_id, correlation in self._active_correlations.items()
            if current_time - correlation.created_at > cleanup_threshold
        ]
        
        for corr_id in old_correlations:
            del self._active_correlations[corr_id]
        
        if old_correlations:
            logger.debug("Cleaned up old correlations", count=len(old_correlations))
    
    async def _cleanup_correlation_cache(self):
        """Clean up old entries from correlation cache"""
        
        current_time = time.time()
        cleanup_threshold = 300  # 5 minutes
        
        for hint, candidates in self._correlation_cache.items():
            # Remove old candidates
            while candidates and current_time - candidates[0].timestamp > cleanup_threshold:
                candidates.popleft()
    
    def _update_average_correlation_time(self, processing_time_ms: float):
        """Update average correlation processing time"""
        
        current_avg = self._correlation_stats['average_correlation_time_ms']
        total_processed = self._correlation_stats['total_candidates_processed']
        
        # Incremental average calculation
        new_avg = ((current_avg * (total_processed - 1)) + processing_time_ms) / total_processed
        self._correlation_stats['average_correlation_time_ms'] = new_avg
    
    def _update_correlation_statistics(self):
        """Update correlation statistics"""
        
        total_processed = self._correlation_stats['total_candidates_processed']
        correlations_found = self._correlation_stats['correlations_found']
        
        if total_processed > 0:
            self._correlation_stats['correlation_success_rate'] = correlations_found / total_processed
    
    async def get_correlation_statistics(self) -> Dict[str, Any]:
        """Get correlation engine statistics"""
        
        return {
            'correlation_stats': self._correlation_stats.copy(),
            'active_correlations_count': len(self._active_correlations),
            'correlation_cache_size': sum(len(candidates) for candidates in self._correlation_cache.values()),
            'correlation_windows_count': len(self._correlation_windows),
            'correlation_patterns': dict(self._correlation_patterns),
            'engine_config': {
                'correlation_window_ms': self.correlation_window_ms,
                'max_candidates_per_window': self.max_candidates_per_window,
                'correlation_threshold': self.correlation_threshold
            }
        }
    
    async def get_active_correlations(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get active correlations"""
        
        correlations = []
        
        # Sort by creation time (newest first)
        sorted_correlations = sorted(
            self._active_correlations.values(),
            key=lambda x: x.created_at,
            reverse=True
        )
        
        for correlation in sorted_correlations[:limit]:
            correlations.append({
                'correlation_id': correlation.correlation_id,
                'correlation_type': correlation.correlation_type.value,
                'strength': correlation.strength.value,
                'confidence_score': correlation.confidence_score,
                'candidates_count': len(correlation.candidates),
                'pillar_types': [c.pillar_type.value for c in correlation.candidates],
                'temporal_window_ms': correlation.temporal_window_ms,
                'created_at': correlation.created_at,
                'evidence_summary': {
                    'common_hints_count': len(correlation.correlation_evidence.get('common_hints', [])),
                    'has_deep_system_context': correlation.deep_system_context is not None
                }
            })
        
        return correlations