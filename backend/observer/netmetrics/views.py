"""
Network Metrics views.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Sum
from django.utils import timezone
from datetime import timedelta
import structlog

from .models import NetworkInterface, NetworkMetricData, NetworkConnection, NetworkLatencyTest

logger = structlog.get_logger(__name__)


@require_http_methods(["GET"])
@login_required
def interfaces_list(request):
    """List network interfaces."""
    try:
        interfaces = NetworkInterface.objects.filter(is_active=True, is_monitored=True)
        
        interfaces_data = []
        for interface in interfaces:
            interfaces_data.append({
                'id': str(interface.id),
                'name': interface.name,
                'interface_type': interface.interface_type,
                'ip_address': interface.ip_address,
                'is_up': interface.is_up,
                'speed_mbps': interface.speed_mbps
            })
        
        return JsonResponse({'interfaces': interfaces_data})
        
    except Exception as e:
        logger.error("Failed to retrieve interfaces", error=str(e))
        return JsonResponse({'error': 'Failed to retrieve interfaces'}, status=500)


@require_http_methods(["GET"])
@login_required
def network_summary(request):
    """Get network metrics summary."""
    try:
        hours = int(request.GET.get('hours', 24))
        start_time = timezone.now() - timedelta(hours=hours)
        
        # Active connections by protocol
        connections_by_protocol = NetworkConnection.objects.filter(
            is_active=True
        ).values('protocol').annotate(
            count=Count('id')
        ).order_by('protocol')
        
        # Average latency by target
        avg_latency = NetworkLatencyTest.objects.filter(
            timestamp__gte=start_time,
            success=True,
            is_active=True
        ).values('target_host').annotate(
            avg_latency=Avg('latency_ms'),
            test_count=Count('id')
        ).order_by('target_host')
        
        return JsonResponse({
            'connections_by_protocol': list(connections_by_protocol),
            'average_latency': list(avg_latency)
        })
        
    except Exception as e:
        logger.error("Failed to retrieve network summary", error=str(e))
        return JsonResponse({'error': 'Failed to retrieve network summary'}, status=500)