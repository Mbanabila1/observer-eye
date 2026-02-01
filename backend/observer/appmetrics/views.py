"""
Application Metrics views.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Sum
from django.utils import timezone
from datetime import timedelta
import structlog

from .models import ApplicationInstance, ApplicationMetricData, ApplicationCounter, ApplicationGauge, ApplicationEvent

logger = structlog.get_logger(__name__)


@require_http_methods(["GET"])
@login_required
def instances_list(request):
    """List application instances."""
    try:
        instances = ApplicationInstance.objects.filter(is_active=True)
        
        instances_data = []
        for instance in instances:
            instances_data.append({
                'id': str(instance.id),
                'name': instance.name,
                'version': instance.version,
                'environment': instance.environment,
                'host': instance.host,
                'port': instance.port,
                'is_running': instance.is_running,
                'start_time': instance.start_time.isoformat(),
                'last_heartbeat': instance.last_heartbeat.isoformat()
            })
        
        return JsonResponse({'instances': instances_data})
        
    except Exception as e:
        logger.error("Failed to retrieve instances", error=str(e))
        return JsonResponse({'error': 'Failed to retrieve instances'}, status=500)


@require_http_methods(["GET"])
@login_required
def metrics_summary(request):
    """Get application metrics summary."""
    try:
        hours = int(request.GET.get('hours', 24))
        start_time = timezone.now() - timedelta(hours=hours)
        
        # Metrics by category
        metrics_by_category = ApplicationMetricData.objects.filter(
            timestamp__gte=start_time,
            is_active=True
        ).values('metric_category').annotate(
            count=Count('id'),
            avg_value=Avg('value')
        ).order_by('metric_category')
        
        # Active instances
        active_instances = ApplicationInstance.objects.filter(
            is_running=True,
            is_active=True
        ).count()
        
        # Recent events
        recent_events = ApplicationEvent.objects.filter(
            timestamp__gte=start_time,
            is_active=True
        ).values('event_type', 'severity').annotate(
            count=Count('id')
        ).order_by('event_type', 'severity')
        
        return JsonResponse({
            'active_instances': active_instances,
            'metrics_by_category': list(metrics_by_category),
            'recent_events': list(recent_events)
        })
        
    except Exception as e:
        logger.error("Failed to retrieve metrics summary", error=str(e))
        return JsonResponse({'error': 'Failed to retrieve metrics summary'}, status=500)