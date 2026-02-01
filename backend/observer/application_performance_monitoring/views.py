"""
Application Performance Monitoring views.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Avg, Count
from django.utils import timezone
from datetime import timedelta
import structlog

from .models import ApplicationService, ApplicationMetric, ApplicationHealthCheck, ApplicationError

logger = structlog.get_logger(__name__)


@require_http_methods(["GET"])
@login_required
def services_list(request):
    """List monitored application services."""
    try:
        services = ApplicationService.objects.filter(is_active=True, is_monitored=True)
        
        services_data = []
        for service in services:
            # Get latest health check
            latest_health = service.health_checks.first()
            
            services_data.append({
                'id': str(service.id),
                'name': service.name,
                'service_type': service.service_type,
                'environment': service.environment,
                'version': service.version,
                'health_status': latest_health.status if latest_health else 'unknown',
                'last_health_check': latest_health.timestamp.isoformat() if latest_health else None
            })
        
        return JsonResponse({'services': services_data})
        
    except Exception as e:
        logger.error("Failed to retrieve services", error=str(e))
        return JsonResponse({'error': 'Failed to retrieve services'}, status=500)


@require_http_methods(["GET"])
@login_required
def service_metrics(request, service_id):
    """Get metrics for a specific service."""
    try:
        service = ApplicationService.objects.get(id=service_id, is_active=True)
        
        hours = int(request.GET.get('hours', 24))
        start_time = timezone.now() - timedelta(hours=hours)
        
        metrics = ApplicationMetric.objects.filter(
            service=service,
            timestamp__gte=start_time,
            is_active=True
        ).order_by('-timestamp')
        
        # Group by metric type
        metrics_by_type = {}
        for metric in metrics:
            if metric.metric_type not in metrics_by_type:
                metrics_by_type[metric.metric_type] = []
            
            metrics_by_type[metric.metric_type].append({
                'value': metric.value,
                'unit': metric.unit,
                'timestamp': metric.timestamp.isoformat()
            })
        
        return JsonResponse({
            'service': service.name,
            'metrics': metrics_by_type
        })
        
    except ApplicationService.DoesNotExist:
        return JsonResponse({'error': 'Service not found'}, status=404)
    except Exception as e:
        logger.error("Failed to retrieve service metrics", service_id=service_id, error=str(e))
        return JsonResponse({'error': 'Failed to retrieve service metrics'}, status=500)


@require_http_methods(["GET"])
@login_required
def health_status(request):
    """Get overall health status of all services."""
    try:
        services = ApplicationService.objects.filter(is_active=True, is_monitored=True)
        
        health_summary = {
            'healthy': 0,
            'degraded': 0,
            'unhealthy': 0,
            'unknown': 0
        }
        
        service_health = []
        for service in services:
            latest_health = service.health_checks.first()
            status = latest_health.status if latest_health else 'unknown'
            
            health_summary[status] += 1
            
            service_health.append({
                'service_name': service.name,
                'status': status,
                'last_check': latest_health.timestamp.isoformat() if latest_health else None,
                'response_time_ms': latest_health.response_time_ms if latest_health else None
            })
        
        return JsonResponse({
            'summary': health_summary,
            'services': service_health
        })
        
    except Exception as e:
        logger.error("Failed to retrieve health status", error=str(e))
        return JsonResponse({'error': 'Failed to retrieve health status'}, status=500)