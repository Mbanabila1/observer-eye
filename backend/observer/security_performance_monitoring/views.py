"""
Security Performance Monitoring views.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg
from django.utils import timezone
from datetime import timedelta
import structlog

from .models import SecurityMetric, SecurityIncident

logger = structlog.get_logger(__name__)


@require_http_methods(["GET"])
@login_required
def security_metrics_summary(request):
    """Get security metrics summary."""
    try:
        hours = int(request.GET.get('hours', 24))
        start_time = timezone.now() - timedelta(hours=hours)
        
        metrics = SecurityMetric.objects.filter(
            timestamp__gte=start_time,
            is_active=True
        ).values('metric_type', 'severity').annotate(
            count=Count('id'),
            avg_value=Avg('value')
        ).order_by('metric_type', 'severity')
        
        summary = {}
        for metric in metrics:
            metric_type = metric['metric_type']
            if metric_type not in summary:
                summary[metric_type] = {}
            
            summary[metric_type][metric['severity']] = {
                'count': metric['count'],
                'avg_value': round(metric['avg_value'], 2)
            }
        
        return JsonResponse({'security_metrics': summary})
        
    except Exception as e:
        logger.error("Failed to retrieve security metrics", error=str(e))
        return JsonResponse({'error': 'Failed to retrieve security metrics'}, status=500)


@require_http_methods(["GET"])
@login_required
def security_incidents(request):
    """Get security incidents."""
    try:
        hours = int(request.GET.get('hours', 24))
        start_time = timezone.now() - timedelta(hours=hours)
        
        incidents = SecurityIncident.objects.filter(
            timestamp__gte=start_time,
            is_active=True
        ).values('incident_type', 'severity', 'is_resolved').annotate(
            count=Count('id'),
            avg_detection_time=Avg('detection_time_ms'),
            avg_response_time=Avg('response_time_ms')
        ).order_by('incident_type', 'severity')
        
        return JsonResponse({'security_incidents': list(incidents)})
        
    except Exception as e:
        logger.error("Failed to retrieve security incidents", error=str(e))
        return JsonResponse({'error': 'Failed to retrieve security incidents'}, status=500)