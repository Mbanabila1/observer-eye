"""
Identity Performance Monitoring views.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count
from django.utils import timezone
from datetime import timedelta
import structlog

from .models import IdentityProviderMetric, AuthenticationEvent

logger = structlog.get_logger(__name__)


@require_http_methods(["GET"])
@login_required
def provider_metrics(request):
    """Get identity provider performance metrics."""
    try:
        hours = int(request.GET.get('hours', 24))
        start_time = timezone.now() - timedelta(hours=hours)
        
        metrics = IdentityProviderMetric.objects.filter(
            timestamp__gte=start_time,
            is_active=True
        ).values('provider_name', 'metric_type').annotate(
            avg_value=Avg('value'),
            count=Count('id')
        ).order_by('provider_name', 'metric_type')
        
        provider_data = {}
        for metric in metrics:
            provider = metric['provider_name']
            if provider not in provider_data:
                provider_data[provider] = {}
            
            provider_data[provider][metric['metric_type']] = {
                'avg_value': round(metric['avg_value'], 2),
                'count': metric['count']
            }
        
        return JsonResponse({'provider_metrics': provider_data})
        
    except Exception as e:
        logger.error("Failed to retrieve provider metrics", error=str(e))
        return JsonResponse({'error': 'Failed to retrieve provider metrics'}, status=500)


@require_http_methods(["GET"])
@login_required
def auth_events_summary(request):
    """Get authentication events summary."""
    try:
        hours = int(request.GET.get('hours', 24))
        start_time = timezone.now() - timedelta(hours=hours)
        
        events = AuthenticationEvent.objects.filter(
            timestamp__gte=start_time,
            is_active=True
        ).values('provider_name', 'event_type').annotate(
            count=Count('id'),
            avg_response_time=Avg('response_time_ms')
        ).order_by('provider_name', 'event_type')
        
        summary = {}
        for event in events:
            provider = event['provider_name']
            if provider not in summary:
                summary[provider] = {}
            
            summary[provider][event['event_type']] = {
                'count': event['count'],
                'avg_response_time_ms': round(event['avg_response_time'] or 0, 2)
            }
        
        return JsonResponse({'auth_events': summary})
        
    except Exception as e:
        logger.error("Failed to retrieve auth events", error=str(e))
        return JsonResponse({'error': 'Failed to retrieve auth events'}, status=500)