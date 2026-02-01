"""
Traffic Performance Monitoring views.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Avg, Count
from django.utils import timezone
from datetime import timedelta
import structlog

from .models import TrafficMetric, TrafficFlow

logger = structlog.get_logger(__name__)


@require_http_methods(["GET"])
@login_required
def traffic_metrics_summary(request):
    """Get traffic metrics summary."""
    try:
        hours = int(request.GET.get('hours', 24))
        start_time = timezone.now() - timedelta(hours=hours)
        
        metrics = TrafficMetric.objects.filter(
            timestamp__gte=start_time,
            is_active=True
        ).values('interface_name', 'metric_type').annotate(
            avg_value=Avg('value'),
            count=Count('id')
        ).order_by('interface_name', 'metric_type')
        
        summary = {}
        for metric in metrics:
            interface = metric['interface_name']
            if interface not in summary:
                summary[interface] = {}
            
            summary[interface][metric['metric_type']] = {
                'avg_value': round(metric['avg_value'], 2),
                'count': metric['count']
            }
        
        return JsonResponse({'traffic_metrics': summary})
        
    except Exception as e:
        logger.error("Failed to retrieve traffic metrics", error=str(e))
        return JsonResponse({'error': 'Failed to retrieve traffic metrics'}, status=500)


@require_http_methods(["GET"])
@login_required
def traffic_flows_summary(request):
    """Get traffic flows summary."""
    try:
        hours = int(request.GET.get('hours', 24))
        start_time = timezone.now() - timedelta(hours=hours)
        
        flows = TrafficFlow.objects.filter(
            start_time__gte=start_time,
            is_active=True
        ).values('protocol').annotate(
            total_flows=Count('id'),
            total_bytes_sent=Sum('bytes_sent'),
            total_bytes_received=Sum('bytes_received'),
            avg_duration=Avg('duration_seconds')
        ).order_by('-total_flows')
        
        return JsonResponse({'traffic_flows': list(flows)})
        
    except Exception as e:
        logger.error("Failed to retrieve traffic flows", error=str(e))
        return JsonResponse({'error': 'Failed to retrieve traffic flows'}, status=500)