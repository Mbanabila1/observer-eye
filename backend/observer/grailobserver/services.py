"""
Specialized observability services and analysis tools.
Provides advanced monitoring capabilities and intelligent analysis.
"""

import logging
import statistics
from datetime import timedelta
from typing import Dict, List, Optional, Tuple, Any
from django.utils import timezone
from django.db.models import Q, Avg, Count, Max, Min
import json

from .models import (
    ObservabilityTarget, ServiceLevelIndicator, ServiceLevelObjective,
    ObservabilityTrace, ObservabilityAnomaly, ObservabilityInsight
)

logger = logging.getLogger('observer_eye.grailobserver.services')


class SLOCalculationService:
    """Service for calculating SLO performance and error budgets."""
    
    @staticmethod
    def calculate_slo_performance(slo: ServiceLevelObjective, time_window_hours: int = None) -> Dict[str, Any]:
        """
        Calculate current SLO performance and error budget.
        
        Args:
            slo: ServiceLevelObjective instance
            time_window_hours: Override time window in hours
            
        Returns:
            Dictionary with performance metrics
        """
        try:
            # Determine time window
            if time_window_hours:
                window_start = timezone.now() - timedelta(hours=time_window_hours)
            else:
                # Parse SLO time window
                time_window_map = {
                    '1h': 1, '1d': 24, '7d': 168, '30d': 720, '90d': 2160
                }
                hours = time_window_map.get(slo.time_window, 24)
                window_start = timezone.now() - timedelta(hours=hours)
            
            window_end = timezone.now()
            
            # This is a simplified calculation - in practice, you'd query actual metrics
            # For now, we'll simulate the calculation
            
            # Calculate good events vs total events based on SLI configuration
            sli = slo.sli
            
            # Simulate performance calculation (replace with actual metric queries)
            simulated_performance = SLOCalculationService._simulate_sli_performance(sli, window_start, window_end)
            
            # Calculate error budget
            target_percentage = slo.target_percentage
            current_performance = simulated_performance
            error_budget_consumed = max(0, target_percentage - current_performance)
            error_budget_remaining = max(0, 100 - target_percentage - error_budget_consumed)
            
            # Update SLO record
            slo.current_performance = current_performance
            slo.error_budget_remaining = error_budget_remaining
            slo.last_calculated = timezone.now()
            slo.save(update_fields=['current_performance', 'error_budget_remaining', 'last_calculated'])
            
            return {
                'slo_id': str(slo.id),
                'target_percentage': target_percentage,
                'current_performance': current_performance,
                'error_budget_remaining': error_budget_remaining,
                'error_budget_consumed': error_budget_consumed,
                'status': 'healthy' if current_performance >= target_percentage else 'at_risk',
                'time_window': {
                    'start': window_start.isoformat(),
                    'end': window_end.isoformat(),
                },
                'calculated_at': timezone.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error calculating SLO performance for {slo.id}: {e}")
            return {
                'error': str(e),
                'slo_id': str(slo.id),
            }
    
    @staticmethod
    def _simulate_sli_performance(sli: ServiceLevelIndicator, start_time, end_time) -> float:
        """
        Simulate SLI performance calculation.
        In production, this would query actual metrics from your monitoring system.
        """
        # Simulate different performance based on SLI type
        sli_type_performance = {
            'availability': 99.5,
            'latency': 98.2,
            'throughput': 97.8,
            'error_rate': 99.1,
            'saturation': 96.5,
            'correctness': 99.9,
            'freshness': 98.7,
            'custom': 98.0,
        }
        
        base_performance = sli_type_performance.get(sli.sli_type, 98.0)
        
        # Add some randomness to simulate real-world variation
        import random
        variation = random.uniform(-2.0, 1.0)
        
        return max(90.0, min(100.0, base_performance + variation))


class AnomalyDetectionService:
    """Service for detecting anomalies in observability data."""
    
    @staticmethod
    def detect_performance_anomalies(target: ObservabilityTarget, lookback_hours: int = 24) -> List[Dict[str, Any]]:
        """
        Detect performance anomalies for a target.
        
        Args:
            target: ObservabilityTarget to analyze
            lookback_hours: Hours to look back for analysis
            
        Returns:
            List of detected anomalies
        """
        try:
            anomalies = []
            
            # Get recent traces for the target
            since = timezone.now() - timedelta(hours=lookback_hours)
            traces = ObservabilityTrace.objects.filter(
                service_name=target.name,
                start_time__gte=since
            ).order_by('start_time')
            
            if traces.count() < 10:  # Need minimum data points
                return anomalies
            
            # Analyze latency anomalies
            latency_anomalies = AnomalyDetectionService._detect_latency_anomalies(traces, target)
            anomalies.extend(latency_anomalies)
            
            # Analyze error rate anomalies
            error_anomalies = AnomalyDetectionService._detect_error_rate_anomalies(traces, target)
            anomalies.extend(error_anomalies)
            
            # Analyze throughput anomalies
            throughput_anomalies = AnomalyDetectionService._detect_throughput_anomalies(traces, target)
            anomalies.extend(throughput_anomalies)
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error detecting anomalies for target {target.id}: {e}")
            return []
    
    @staticmethod
    def _detect_latency_anomalies(traces, target) -> List[Dict[str, Any]]:
        """Detect latency anomalies using statistical analysis."""
        anomalies = []
        
        try:
            # Get latency values
            latencies = [trace.duration_ms for trace in traces]
            
            if len(latencies) < 10:
                return anomalies
            
            # Calculate statistical measures
            mean_latency = statistics.mean(latencies)
            stdev_latency = statistics.stdev(latencies) if len(latencies) > 1 else 0
            
            # Define anomaly threshold (3 standard deviations)
            threshold = mean_latency + (3 * stdev_latency)
            
            # Find anomalous traces
            anomalous_traces = [trace for trace in traces if trace.duration_ms > threshold]
            
            if anomalous_traces:
                # Calculate anomaly metrics
                max_latency = max(trace.duration_ms for trace in anomalous_traces)
                deviation_percentage = ((max_latency - mean_latency) / mean_latency) * 100
                
                anomaly_data = {
                    'target': target,
                    'anomaly_type': 'performance',
                    'metric_name': 'latency',
                    'severity': AnomalyDetectionService._calculate_severity(deviation_percentage),
                    'confidence_score': min(1.0, len(anomalous_traces) / len(latencies)),
                    'anomaly_score': deviation_percentage,
                    'baseline_value': mean_latency,
                    'observed_value': max_latency,
                    'deviation_percentage': deviation_percentage,
                    'detection_method': 'statistical_outlier_3sigma',
                    'context_data': {
                        'total_traces': len(latencies),
                        'anomalous_traces': len(anomalous_traces),
                        'threshold_ms': threshold,
                        'mean_latency_ms': mean_latency,
                        'stdev_latency_ms': stdev_latency,
                    },
                    'time_window_start': min(trace.start_time for trace in traces),
                    'time_window_end': max(trace.start_time for trace in traces),
                }
                
                anomalies.append(anomaly_data)
                
        except Exception as e:
            logger.error(f"Error detecting latency anomalies: {e}")
        
        return anomalies
    
    @staticmethod
    def _detect_error_rate_anomalies(traces, target) -> List[Dict[str, Any]]:
        """Detect error rate anomalies."""
        anomalies = []
        
        try:
            total_traces = len(traces)
            error_traces = len([trace for trace in traces if trace.status == 'error'])
            
            if total_traces < 10:
                return anomalies
            
            current_error_rate = (error_traces / total_traces) * 100
            
            # Define baseline error rate (could be historical average)
            baseline_error_rate = 1.0  # 1% baseline
            
            # Detect if error rate is significantly higher
            if current_error_rate > baseline_error_rate * 3:  # 3x higher than baseline
                deviation_percentage = ((current_error_rate - baseline_error_rate) / baseline_error_rate) * 100
                
                anomaly_data = {
                    'target': target,
                    'anomaly_type': 'error_rate',
                    'metric_name': 'error_rate',
                    'severity': AnomalyDetectionService._calculate_severity(deviation_percentage),
                    'confidence_score': min(1.0, error_traces / 10),  # Higher confidence with more errors
                    'anomaly_score': deviation_percentage,
                    'baseline_value': baseline_error_rate,
                    'observed_value': current_error_rate,
                    'deviation_percentage': deviation_percentage,
                    'detection_method': 'error_rate_threshold',
                    'context_data': {
                        'total_traces': total_traces,
                        'error_traces': error_traces,
                        'baseline_error_rate': baseline_error_rate,
                    },
                    'time_window_start': min(trace.start_time for trace in traces),
                    'time_window_end': max(trace.start_time for trace in traces),
                }
                
                anomalies.append(anomaly_data)
                
        except Exception as e:
            logger.error(f"Error detecting error rate anomalies: {e}")
        
        return anomalies
    
    @staticmethod
    def _detect_throughput_anomalies(traces, target) -> List[Dict[str, Any]]:
        """Detect throughput anomalies."""
        anomalies = []
        
        try:
            if len(traces) < 10:
                return anomalies
            
            # Calculate requests per minute
            time_span = (max(trace.start_time for trace in traces) - 
                        min(trace.start_time for trace in traces))
            time_span_minutes = time_span.total_seconds() / 60
            
            if time_span_minutes < 1:
                return anomalies
            
            current_throughput = len(traces) / time_span_minutes
            
            # Define baseline throughput (could be historical average)
            baseline_throughput = 10.0  # 10 requests per minute baseline
            
            # Detect significant drops in throughput
            if current_throughput < baseline_throughput * 0.5:  # 50% drop
                deviation_percentage = ((baseline_throughput - current_throughput) / baseline_throughput) * 100
                
                anomaly_data = {
                    'target': target,
                    'anomaly_type': 'traffic',
                    'metric_name': 'throughput',
                    'severity': AnomalyDetectionService._calculate_severity(deviation_percentage),
                    'confidence_score': 0.8,  # High confidence for throughput drops
                    'anomaly_score': deviation_percentage,
                    'baseline_value': baseline_throughput,
                    'observed_value': current_throughput,
                    'deviation_percentage': deviation_percentage,
                    'detection_method': 'throughput_drop_threshold',
                    'context_data': {
                        'total_traces': len(traces),
                        'time_span_minutes': time_span_minutes,
                        'baseline_throughput_rpm': baseline_throughput,
                    },
                    'time_window_start': min(trace.start_time for trace in traces),
                    'time_window_end': max(trace.start_time for trace in traces),
                }
                
                anomalies.append(anomaly_data)
                
        except Exception as e:
            logger.error(f"Error detecting throughput anomalies: {e}")
        
        return anomalies
    
    @staticmethod
    def _calculate_severity(deviation_percentage: float) -> str:
        """Calculate severity based on deviation percentage."""
        if deviation_percentage >= 100:
            return 'critical'
        elif deviation_percentage >= 50:
            return 'high'
        elif deviation_percentage >= 20:
            return 'medium'
        else:
            return 'low'


class InsightGenerationService:
    """Service for generating AI-powered observability insights."""
    
    @staticmethod
    def generate_performance_insights(target: ObservabilityTarget) -> List[Dict[str, Any]]:
        """
        Generate performance optimization insights for a target.
        
        Args:
            target: ObservabilityTarget to analyze
            
        Returns:
            List of generated insights
        """
        insights = []
        
        try:
            # Analyze recent performance data
            since = timezone.now() - timedelta(days=7)
            traces = ObservabilityTrace.objects.filter(
                service_name=target.name,
                start_time__gte=since
            )
            
            if traces.count() < 50:  # Need sufficient data
                return insights
            
            # Generate latency optimization insights
            latency_insights = InsightGenerationService._generate_latency_insights(traces, target)
            insights.extend(latency_insights)
            
            # Generate error pattern insights
            error_insights = InsightGenerationService._generate_error_insights(traces, target)
            insights.extend(error_insights)
            
            # Generate capacity planning insights
            capacity_insights = InsightGenerationService._generate_capacity_insights(traces, target)
            insights.extend(capacity_insights)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating insights for target {target.id}: {e}")
            return []
    
    @staticmethod
    def _generate_latency_insights(traces, target) -> List[Dict[str, Any]]:
        """Generate latency-related insights."""
        insights = []
        
        try:
            latencies = [trace.duration_ms for trace in traces]
            
            if not latencies:
                return insights
            
            # Calculate percentiles
            p50 = statistics.median(latencies)
            p95 = sorted(latencies)[int(len(latencies) * 0.95)]
            p99 = sorted(latencies)[int(len(latencies) * 0.99)]
            
            # Check if P99 is significantly higher than P50
            if p99 > p50 * 5:  # P99 is 5x higher than median
                insight_data = {
                    'title': f'High Latency Tail for {target.name}',
                    'description': f'The 99th percentile latency ({p99}ms) is significantly higher than the median ({p50}ms), indicating potential performance bottlenecks affecting a small percentage of requests.',
                    'insight_type': 'performance_optimization',
                    'confidence_score': 0.85,
                    'impact_score': 0.7,
                    'evidence_data': {
                        'p50_latency_ms': p50,
                        'p95_latency_ms': p95,
                        'p99_latency_ms': p99,
                        'sample_size': len(latencies),
                        'tail_ratio': p99 / p50,
                    },
                    'recommendations': [
                        'Investigate slow database queries or external API calls',
                        'Consider implementing caching for frequently accessed data',
                        'Review resource allocation and scaling policies',
                        'Analyze trace data to identify specific bottlenecks',
                    ],
                    'estimated_impact': {
                        'performance_improvement': '20-40%',
                        'user_experience': 'Significant improvement for affected users',
                        'implementation_effort': 'Medium',
                    },
                    'generated_by': 'latency_tail_analyzer_v1.0',
                    'targets': [target],
                }
                
                insights.append(insight_data)
                
        except Exception as e:
            logger.error(f"Error generating latency insights: {e}")
        
        return insights
    
    @staticmethod
    def _generate_error_insights(traces, target) -> List[Dict[str, Any]]:
        """Generate error pattern insights."""
        insights = []
        
        try:
            error_traces = [trace for trace in traces if trace.status == 'error']
            total_traces = len(traces)
            
            if not error_traces or total_traces < 10:
                return insights
            
            error_rate = (len(error_traces) / total_traces) * 100
            
            # Analyze error patterns
            error_operations = {}
            for trace in error_traces:
                op = trace.operation_name
                error_operations[op] = error_operations.get(op, 0) + 1
            
            # Find most problematic operation
            if error_operations:
                most_errors_op = max(error_operations.items(), key=lambda x: x[1])
                
                if most_errors_op[1] > len(error_traces) * 0.3:  # >30% of errors from one operation
                    insight_data = {
                        'title': f'High Error Rate in {most_errors_op[0]} Operation',
                        'description': f'The {most_errors_op[0]} operation accounts for {most_errors_op[1]} out of {len(error_traces)} errors ({(most_errors_op[1]/len(error_traces)*100):.1f}%), indicating a specific reliability issue.',
                        'insight_type': 'reliability_improvement',
                        'confidence_score': 0.9,
                        'impact_score': 0.8,
                        'evidence_data': {
                            'total_errors': len(error_traces),
                            'operation_errors': most_errors_op[1],
                            'operation_name': most_errors_op[0],
                            'overall_error_rate': error_rate,
                            'error_distribution': error_operations,
                        },
                        'recommendations': [
                            f'Focus debugging efforts on the {most_errors_op[0]} operation',
                            'Implement additional error handling and retry logic',
                            'Add more detailed logging for this specific operation',
                            'Consider circuit breaker pattern for external dependencies',
                        ],
                        'estimated_impact': {
                            'reliability_improvement': '30-50%',
                            'error_reduction': f'Up to {most_errors_op[1]} fewer errors',
                            'implementation_effort': 'Low to Medium',
                        },
                        'generated_by': 'error_pattern_analyzer_v1.0',
                        'targets': [target],
                    }
                    
                    insights.append(insight_data)
                    
        except Exception as e:
            logger.error(f"Error generating error insights: {e}")
        
        return insights
    
    @staticmethod
    def _generate_capacity_insights(traces, target) -> List[Dict[str, Any]]:
        """Generate capacity planning insights."""
        insights = []
        
        try:
            # Analyze traffic patterns over time
            if len(traces) < 100:
                return insights
            
            # Group traces by hour to analyze patterns
            hourly_counts = {}
            for trace in traces:
                hour = trace.start_time.replace(minute=0, second=0, microsecond=0)
                hourly_counts[hour] = hourly_counts.get(hour, 0) + 1
            
            if len(hourly_counts) < 24:  # Need at least 24 hours of data
                return insights
            
            # Calculate traffic statistics
            counts = list(hourly_counts.values())
            avg_hourly = statistics.mean(counts)
            max_hourly = max(counts)
            
            # Check for significant traffic spikes
            if max_hourly > avg_hourly * 3:  # Peak is 3x average
                insight_data = {
                    'title': f'Traffic Spike Pattern Detected for {target.name}',
                    'description': f'Peak hourly traffic ({max_hourly} requests) is {max_hourly/avg_hourly:.1f}x higher than average ({avg_hourly:.0f} requests), indicating potential capacity planning needs.',
                    'insight_type': 'capacity_planning',
                    'confidence_score': 0.8,
                    'impact_score': 0.6,
                    'evidence_data': {
                        'average_hourly_requests': avg_hourly,
                        'peak_hourly_requests': max_hourly,
                        'spike_ratio': max_hourly / avg_hourly,
                        'analysis_period_hours': len(hourly_counts),
                    },
                    'recommendations': [
                        'Implement auto-scaling based on traffic patterns',
                        'Consider load balancing improvements',
                        'Pre-scale resources during expected peak hours',
                        'Monitor resource utilization during traffic spikes',
                    ],
                    'estimated_impact': {
                        'availability_improvement': '15-25%',
                        'cost_optimization': 'Better resource utilization',
                        'implementation_effort': 'Medium',
                    },
                    'generated_by': 'capacity_pattern_analyzer_v1.0',
                    'targets': [target],
                }
                
                insights.append(insight_data)
                
        except Exception as e:
            logger.error(f"Error generating capacity insights: {e}")
        
        return insights


class HealthCheckService:
    """Service for performing health checks on observability targets."""
    
    @staticmethod
    def perform_health_check(target: ObservabilityTarget) -> Dict[str, Any]:
        """
        Perform comprehensive health check on a target.
        
        Args:
            target: ObservabilityTarget to check
            
        Returns:
            Health check results
        """
        try:
            health_result = {
                'target_id': str(target.id),
                'target_name': target.name,
                'timestamp': timezone.now().isoformat(),
                'overall_status': 'unknown',
                'checks': {},
                'recommendations': [],
            }
            
            # Perform different types of health checks
            if target.endpoint_url:
                endpoint_check = HealthCheckService._check_endpoint_health(target)
                health_result['checks']['endpoint'] = endpoint_check
            
            # Check recent trace data
            trace_check = HealthCheckService._check_trace_health(target)
            health_result['checks']['traces'] = trace_check
            
            # Check for recent anomalies
            anomaly_check = HealthCheckService._check_anomaly_status(target)
            health_result['checks']['anomalies'] = anomaly_check
            
            # Check SLO compliance
            slo_check = HealthCheckService._check_slo_compliance(target)
            health_result['checks']['slos'] = slo_check
            
            # Determine overall status
            health_result['overall_status'] = HealthCheckService._calculate_overall_status(
                health_result['checks']
            )
            
            # Update target health status
            target.health_status = health_result['overall_status']
            target.last_health_check = timezone.now()
            target.save(update_fields=['health_status', 'last_health_check'])
            
            return health_result
            
        except Exception as e:
            logger.error(f"Error performing health check for target {target.id}: {e}")
            return {
                'target_id': str(target.id),
                'error': str(e),
                'overall_status': 'unknown',
            }
    
    @staticmethod
    def _check_endpoint_health(target: ObservabilityTarget) -> Dict[str, Any]:
        """Check endpoint health (simplified - would use actual HTTP requests in production)."""
        # In production, you would make actual HTTP requests to the endpoint
        # For now, we'll simulate the check
        
        import random
        
        # Simulate endpoint check
        is_healthy = random.choice([True, True, True, False])  # 75% healthy
        response_time = random.uniform(50, 500)  # Random response time
        
        return {
            'status': 'healthy' if is_healthy else 'unhealthy',
            'response_time_ms': response_time,
            'details': 'Endpoint responding normally' if is_healthy else 'Endpoint timeout or error',
        }
    
    @staticmethod
    def _check_trace_health(target: ObservabilityTarget) -> Dict[str, Any]:
        """Check trace data health."""
        try:
            # Check for recent traces
            since = timezone.now() - timedelta(hours=1)
            recent_traces = ObservabilityTrace.objects.filter(
                service_name=target.name,
                start_time__gte=since
            )
            
            trace_count = recent_traces.count()
            error_count = recent_traces.filter(status='error').count()
            
            if trace_count == 0:
                return {
                    'status': 'degraded',
                    'trace_count': 0,
                    'details': 'No recent traces found',
                }
            
            error_rate = (error_count / trace_count) * 100 if trace_count > 0 else 0
            
            if error_rate > 10:  # >10% error rate
                status = 'unhealthy'
            elif error_rate > 5:  # >5% error rate
                status = 'degraded'
            else:
                status = 'healthy'
            
            return {
                'status': status,
                'trace_count': trace_count,
                'error_count': error_count,
                'error_rate': error_rate,
                'details': f'{trace_count} traces in last hour, {error_rate:.1f}% error rate',
            }
            
        except Exception as e:
            return {
                'status': 'unknown',
                'error': str(e),
            }
    
    @staticmethod
    def _check_anomaly_status(target: ObservabilityTarget) -> Dict[str, Any]:
        """Check for recent anomalies."""
        try:
            # Check for recent unacknowledged anomalies
            since = timezone.now() - timedelta(hours=24)
            recent_anomalies = ObservabilityAnomaly.objects.filter(
                target=target,
                detected_at__gte=since,
                is_acknowledged=False
            )
            
            anomaly_count = recent_anomalies.count()
            critical_count = recent_anomalies.filter(severity='critical').count()
            high_count = recent_anomalies.filter(severity='high').count()
            
            if critical_count > 0:
                status = 'unhealthy'
                details = f'{critical_count} critical anomalies detected'
            elif high_count > 0:
                status = 'degraded'
                details = f'{high_count} high-severity anomalies detected'
            elif anomaly_count > 0:
                status = 'degraded'
                details = f'{anomaly_count} anomalies detected'
            else:
                status = 'healthy'
                details = 'No recent anomalies'
            
            return {
                'status': status,
                'anomaly_count': anomaly_count,
                'critical_count': critical_count,
                'high_count': high_count,
                'details': details,
            }
            
        except Exception as e:
            return {
                'status': 'unknown',
                'error': str(e),
            }
    
    @staticmethod
    def _check_slo_compliance(target: ObservabilityTarget) -> Dict[str, Any]:
        """Check SLO compliance."""
        try:
            # Get SLOs for this target
            slos = ServiceLevelObjective.objects.filter(
                sli__target=target,
                is_active=True
            )
            
            if not slos.exists():
                return {
                    'status': 'unknown',
                    'details': 'No SLOs configured',
                }
            
            compliant_slos = 0
            total_slos = slos.count()
            
            for slo in slos:
                if slo.current_performance and slo.current_performance >= slo.target_percentage:
                    compliant_slos += 1
            
            compliance_rate = (compliant_slos / total_slos) * 100 if total_slos > 0 else 0
            
            if compliance_rate >= 90:
                status = 'healthy'
            elif compliance_rate >= 70:
                status = 'degraded'
            else:
                status = 'unhealthy'
            
            return {
                'status': status,
                'total_slos': total_slos,
                'compliant_slos': compliant_slos,
                'compliance_rate': compliance_rate,
                'details': f'{compliant_slos}/{total_slos} SLOs meeting targets ({compliance_rate:.1f}%)',
            }
            
        except Exception as e:
            return {
                'status': 'unknown',
                'error': str(e),
            }
    
    @staticmethod
    def _calculate_overall_status(checks: Dict[str, Dict[str, Any]]) -> str:
        """Calculate overall health status from individual checks."""
        statuses = [check.get('status', 'unknown') for check in checks.values()]
        
        if 'unhealthy' in statuses:
            return 'unhealthy'
        elif 'degraded' in statuses:
            return 'degraded'
        elif all(status == 'healthy' for status in statuses):
            return 'healthy'
        else:
            return 'unknown'