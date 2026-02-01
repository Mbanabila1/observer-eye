"""
Grail Observer views for specialized observability features.
Provides REST API endpoints for advanced monitoring and analysis.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg, Max, Min
from django.utils import timezone
from datetime import timedelta
import json
import logging

from .models import (
    ObservabilityTarget, ObservabilityPattern, ServiceLevelIndicator,
    ServiceLevelObjective, ObservabilityTrace, ObservabilityAnomaly,
    ObservabilityPlaybook, ObservabilityExperiment, ObservabilityInsight
)

logger = logging.getLogger('observer_eye.grailobserver')


class ObservabilityTargetView(View):
    """API endpoints for observability targets management."""
    
    def get(self, request, target_id=None):
        """Get observability targets or specific target."""
        try:
            if target_id:
                target = ObservabilityTarget.objects.get(id=target_id, is_active=True)
                return JsonResponse({
                    'id': str(target.id),
                    'name': target.name,
                    'description': target.description,
                    'target_type': target.target_type,
                    'endpoint_url': target.endpoint_url,
                    'health_status': target.health_status,
                    'is_critical': target.is_critical,
                    'is_monitored': target.is_monitored,
                    'last_health_check': target.last_health_check.isoformat() if target.last_health_check else None,
                    'tags': target.tags,
                    'created_at': target.created_at.isoformat(),
                })
            else:
                # List targets with filtering
                targets = ObservabilityTarget.objects.filter(is_active=True)
                
                # Apply filters
                target_type = request.GET.get('type')
                if target_type:
                    targets = targets.filter(target_type=target_type)
                
                health_status = request.GET.get('health_status')
                if health_status:
                    targets = targets.filter(health_status=health_status)
                
                is_critical = request.GET.get('is_critical')
                if is_critical:
                    targets = targets.filter(is_critical=is_critical.lower() == 'true')
                
                # Pagination
                page = int(request.GET.get('page', 1))
                page_size = int(request.GET.get('page_size', 20))
                paginator = Paginator(targets, page_size)
                page_obj = paginator.get_page(page)
                
                return JsonResponse({
                    'targets': [
                        {
                            'id': str(target.id),
                            'name': target.name,
                            'target_type': target.target_type,
                            'health_status': target.health_status,
                            'is_critical': target.is_critical,
                            'is_monitored': target.is_monitored,
                            'last_health_check': target.last_health_check.isoformat() if target.last_health_check else None,
                        }
                        for target in page_obj
                    ],
                    'pagination': {
                        'page': page,
                        'page_size': page_size,
                        'total_pages': paginator.num_pages,
                        'total_count': paginator.count,
                    }
                })
        except ObservabilityTarget.DoesNotExist:
            return JsonResponse({'error': 'Target not found'}, status=404)
        except Exception as e:
            logger.error(f"Error retrieving observability targets: {e}")
            return JsonResponse({'error': 'Internal server error'}, status=500)
    
    @method_decorator(csrf_exempt)
    def post(self, request):
        """Create new observability target."""
        try:
            data = json.loads(request.body)
            
            target = ObservabilityTarget.objects.create(
                name=data['name'],
                description=data.get('description', ''),
                target_type=data['target_type'],
                endpoint_url=data.get('endpoint_url', ''),
                health_check_config=data.get('health_check_config', {}),
                monitoring_config=data.get('monitoring_config', {}),
                sla_config=data.get('sla_config', {}),
                tags=data.get('tags', {}),
                is_critical=data.get('is_critical', False),
                is_monitored=data.get('is_monitored', True),
            )
            
            logger.info(f"Created observability target: {target.name}")
            
            return JsonResponse({
                'id': str(target.id),
                'name': target.name,
                'message': 'Target created successfully'
            }, status=201)
            
        except KeyError as e:
            return JsonResponse({'error': f'Missing required field: {e}'}, status=400)
        except Exception as e:
            logger.error(f"Error creating observability target: {e}")
            return JsonResponse({'error': 'Internal server error'}, status=500)


class SLIView(View):
    """API endpoints for Service Level Indicators."""
    
    def get(self, request, sli_id=None):
        """Get SLIs or specific SLI."""
        try:
            if sli_id:
                sli = ServiceLevelIndicator.objects.get(id=sli_id, is_active=True)
                return JsonResponse({
                    'id': str(sli.id),
                    'name': sli.name,
                    'description': sli.description,
                    'target': {
                        'id': str(sli.target.id),
                        'name': sli.target.name,
                    },
                    'sli_type': sli.sli_type,
                    'measurement_config': sli.measurement_config,
                    'unit': sli.unit,
                    'good_threshold': sli.good_threshold,
                    'total_threshold': sli.total_threshold,
                    'calculation_window': sli.calculation_window,
                    'is_active': sli.is_active,
                })
            else:
                # List SLIs with filtering
                slis = ServiceLevelIndicator.objects.filter(is_active=True).select_related('target')
                
                target_id = request.GET.get('target_id')
                if target_id:
                    slis = slis.filter(target_id=target_id)
                
                sli_type = request.GET.get('sli_type')
                if sli_type:
                    slis = slis.filter(sli_type=sli_type)
                
                return JsonResponse({
                    'slis': [
                        {
                            'id': str(sli.id),
                            'name': sli.name,
                            'target_name': sli.target.name,
                            'sli_type': sli.sli_type,
                            'unit': sli.unit,
                            'calculation_window': sli.calculation_window,
                        }
                        for sli in slis
                    ]
                })
        except ServiceLevelIndicator.DoesNotExist:
            return JsonResponse({'error': 'SLI not found'}, status=404)
        except Exception as e:
            logger.error(f"Error retrieving SLIs: {e}")
            return JsonResponse({'error': 'Internal server error'}, status=500)


class SLOView(View):
    """API endpoints for Service Level Objectives."""
    
    def get(self, request, slo_id=None):
        """Get SLOs or specific SLO."""
        try:
            if slo_id:
                slo = ServiceLevelObjective.objects.get(id=slo_id, is_active=True)
                return JsonResponse({
                    'id': str(slo.id),
                    'name': slo.name,
                    'description': slo.description,
                    'sli': {
                        'id': str(slo.sli.id),
                        'name': slo.sli.name,
                        'target_name': slo.sli.target.name,
                    },
                    'target_percentage': slo.target_percentage,
                    'time_window': slo.time_window,
                    'current_performance': slo.current_performance,
                    'error_budget_remaining': slo.error_budget_remaining,
                    'last_calculated': slo.last_calculated.isoformat() if slo.last_calculated else None,
                })
            else:
                # List SLOs with performance data
                slos = ServiceLevelObjective.objects.filter(is_active=True).select_related('sli__target')
                
                return JsonResponse({
                    'slos': [
                        {
                            'id': str(slo.id),
                            'name': slo.name,
                            'target_name': slo.sli.target.name,
                            'target_percentage': slo.target_percentage,
                            'current_performance': slo.current_performance,
                            'error_budget_remaining': slo.error_budget_remaining,
                            'status': 'healthy' if slo.current_performance and slo.current_performance >= slo.target_percentage else 'at_risk',
                        }
                        for slo in slos
                    ]
                })
        except ServiceLevelObjective.DoesNotExist:
            return JsonResponse({'error': 'SLO not found'}, status=404)
        except Exception as e:
            logger.error(f"Error retrieving SLOs: {e}")
            return JsonResponse({'error': 'Internal server error'}, status=500)


class TraceView(View):
    """API endpoints for distributed tracing data."""
    
    def get(self, request, trace_id=None):
        """Get traces or specific trace."""
        try:
            if trace_id:
                # Get all spans for a trace
                spans = ObservabilityTrace.objects.filter(trace_id=trace_id).order_by('start_time')
                
                if not spans.exists():
                    return JsonResponse({'error': 'Trace not found'}, status=404)
                
                return JsonResponse({
                    'trace_id': trace_id,
                    'spans': [
                        {
                            'span_id': span.span_id,
                            'parent_span_id': span.parent_span_id,
                            'operation_name': span.operation_name,
                            'service_name': span.service_name,
                            'start_time': span.start_time.isoformat(),
                            'end_time': span.end_time.isoformat(),
                            'duration_ms': span.duration_ms,
                            'status': span.status,
                            'tags': span.tags,
                        }
                        for span in spans
                    ],
                    'total_duration_ms': max(span.end_time for span in spans) - min(span.start_time for span in spans),
                })
            else:
                # List recent traces with filtering
                traces = ObservabilityTrace.objects.all()
                
                service_name = request.GET.get('service_name')
                if service_name:
                    traces = traces.filter(service_name=service_name)
                
                status = request.GET.get('status')
                if status:
                    traces = traces.filter(status=status)
                
                # Get unique traces (group by trace_id)
                trace_ids = traces.values('trace_id').distinct()[:100]
                
                trace_summaries = []
                for trace_data in trace_ids:
                    trace_spans = traces.filter(trace_id=trace_data['trace_id'])
                    root_span = trace_spans.filter(parent_span_id='').first()
                    
                    if root_span:
                        trace_summaries.append({
                            'trace_id': trace_data['trace_id'],
                            'root_operation': root_span.operation_name,
                            'root_service': root_span.service_name,
                            'start_time': root_span.start_time.isoformat(),
                            'duration_ms': root_span.duration_ms,
                            'status': root_span.status,
                            'span_count': trace_spans.count(),
                        })
                
                return JsonResponse({'traces': trace_summaries})
                
        except Exception as e:
            logger.error(f"Error retrieving traces: {e}")
            return JsonResponse({'error': 'Internal server error'}, status=500)


class AnomalyView(View):
    """API endpoints for observability anomalies."""
    
    def get(self, request, anomaly_id=None):
        """Get anomalies or specific anomaly."""
        try:
            if anomaly_id:
                anomaly = ObservabilityAnomaly.objects.get(id=anomaly_id)
                return JsonResponse({
                    'id': str(anomaly.id),
                    'target': {
                        'id': str(anomaly.target.id),
                        'name': anomaly.target.name,
                    },
                    'anomaly_type': anomaly.anomaly_type,
                    'metric_name': anomaly.metric_name,
                    'detected_at': anomaly.detected_at.isoformat(),
                    'severity': anomaly.severity,
                    'confidence_score': anomaly.confidence_score,
                    'anomaly_score': anomaly.anomaly_score,
                    'baseline_value': anomaly.baseline_value,
                    'observed_value': anomaly.observed_value,
                    'deviation_percentage': anomaly.deviation_percentage,
                    'detection_method': anomaly.detection_method,
                    'context_data': anomaly.context_data,
                    'is_acknowledged': anomaly.is_acknowledged,
                })
            else:
                # List recent anomalies
                anomalies = ObservabilityAnomaly.objects.select_related('target')
                
                # Apply filters
                target_id = request.GET.get('target_id')
                if target_id:
                    anomalies = anomalies.filter(target_id=target_id)
                
                severity = request.GET.get('severity')
                if severity:
                    anomalies = anomalies.filter(severity=severity)
                
                is_acknowledged = request.GET.get('is_acknowledged')
                if is_acknowledged:
                    anomalies = anomalies.filter(is_acknowledged=is_acknowledged.lower() == 'true')
                
                # Recent anomalies (last 7 days)
                week_ago = timezone.now() - timedelta(days=7)
                anomalies = anomalies.filter(detected_at__gte=week_ago)[:50]
                
                return JsonResponse({
                    'anomalies': [
                        {
                            'id': str(anomaly.id),
                            'target_name': anomaly.target.name,
                            'anomaly_type': anomaly.anomaly_type,
                            'metric_name': anomaly.metric_name,
                            'detected_at': anomaly.detected_at.isoformat(),
                            'severity': anomaly.severity,
                            'confidence_score': anomaly.confidence_score,
                            'deviation_percentage': anomaly.deviation_percentage,
                            'is_acknowledged': anomaly.is_acknowledged,
                        }
                        for anomaly in anomalies
                    ]
                })
        except ObservabilityAnomaly.DoesNotExist:
            return JsonResponse({'error': 'Anomaly not found'}, status=404)
        except Exception as e:
            logger.error(f"Error retrieving anomalies: {e}")
            return JsonResponse({'error': 'Internal server error'}, status=500)


class InsightView(View):
    """API endpoints for observability insights."""
    
    def get(self, request, insight_id=None):
        """Get insights or specific insight."""
        try:
            if insight_id:
                insight = ObservabilityInsight.objects.get(id=insight_id)
                return JsonResponse({
                    'id': str(insight.id),
                    'title': insight.title,
                    'description': insight.description,
                    'insight_type': insight.insight_type,
                    'confidence_score': insight.confidence_score,
                    'impact_score': insight.impact_score,
                    'evidence_data': insight.evidence_data,
                    'recommendations': insight.recommendations,
                    'estimated_impact': insight.estimated_impact,
                    'generated_by': insight.generated_by,
                    'is_actionable': insight.is_actionable,
                    'is_acknowledged': insight.is_acknowledged,
                    'created_at': insight.created_at.isoformat(),
                })
            else:
                # List insights with filtering
                insights = ObservabilityInsight.objects.all()
                
                insight_type = request.GET.get('insight_type')
                if insight_type:
                    insights = insights.filter(insight_type=insight_type)
                
                is_actionable = request.GET.get('is_actionable')
                if is_actionable:
                    insights = insights.filter(is_actionable=is_actionable.lower() == 'true')
                
                is_acknowledged = request.GET.get('is_acknowledged')
                if is_acknowledged:
                    insights = insights.filter(is_acknowledged=is_acknowledged.lower() == 'true')
                
                # Recent insights (last 30 days)
                month_ago = timezone.now() - timedelta(days=30)
                insights = insights.filter(created_at__gte=month_ago)[:50]
                
                return JsonResponse({
                    'insights': [
                        {
                            'id': str(insight.id),
                            'title': insight.title,
                            'insight_type': insight.insight_type,
                            'confidence_score': insight.confidence_score,
                            'impact_score': insight.impact_score,
                            'is_actionable': insight.is_actionable,
                            'is_acknowledged': insight.is_acknowledged,
                            'created_at': insight.created_at.isoformat(),
                        }
                        for insight in insights
                    ]
                })
        except ObservabilityInsight.DoesNotExist:
            return JsonResponse({'error': 'Insight not found'}, status=404)
        except Exception as e:
            logger.error(f"Error retrieving insights: {e}")
            return JsonResponse({'error': 'Internal server error'}, status=500)


@require_http_methods(["GET"])
def health_check(request):
    """Health check endpoint for grailobserver app."""
    try:
        # Basic health checks
        target_count = ObservabilityTarget.objects.filter(is_active=True).count()
        recent_traces = ObservabilityTrace.objects.filter(
            start_time__gte=timezone.now() - timedelta(hours=1)
        ).count()
        
        return JsonResponse({
            'app': 'grailobserver',
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'stats': {
                'active_targets': target_count,
                'recent_traces_1h': recent_traces,
            }
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JsonResponse({
            'app': 'grailobserver',
            'status': 'unhealthy',
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def dashboard_summary(request):
    """Summary data for observability dashboard."""
    try:
        # Get summary statistics
        targets = ObservabilityTarget.objects.filter(is_active=True)
        total_targets = targets.count()
        healthy_targets = targets.filter(health_status='healthy').count()
        critical_targets = targets.filter(is_critical=True).count()
        
        # Recent anomalies
        week_ago = timezone.now() - timedelta(days=7)
        recent_anomalies = ObservabilityAnomaly.objects.filter(
            detected_at__gte=week_ago
        ).count()
        
        # Active SLOs
        active_slos = ServiceLevelObjective.objects.filter(is_active=True).count()
        
        # Recent insights
        recent_insights = ObservabilityInsight.objects.filter(
            created_at__gte=week_ago,
            is_actionable=True
        ).count()
        
        return JsonResponse({
            'summary': {
                'targets': {
                    'total': total_targets,
                    'healthy': healthy_targets,
                    'critical': critical_targets,
                    'health_percentage': (healthy_targets / total_targets * 100) if total_targets > 0 else 0,
                },
                'anomalies': {
                    'recent_7d': recent_anomalies,
                },
                'slos': {
                    'active': active_slos,
                },
                'insights': {
                    'actionable_7d': recent_insights,
                }
            },
            'timestamp': timezone.now().isoformat(),
        })
    except Exception as e:
        logger.error(f"Dashboard summary failed: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)
