"""
Analytics Performance Monitoring views for the Observer Eye Platform.
Provides endpoints for monitoring analytics performance metrics.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Avg, Max, Min, Count, Q
from django.utils import timezone
from datetime import timedelta
import structlog

from .models import (
    AnalyticsPerformanceMetric, AnalyticsQueryPerformance,
    AnalyticsResourceUsage, AnalyticsPerformanceAlert
)

logger = structlog.get_logger(__name__)


@require_http_methods(["GET"])
@login_required
def performance_metrics_list(request):
    """List analytics performance metrics."""
    try:
        metrics = AnalyticsPerformanceMetric.objects.filter(is_active=True)
        
        # Apply filters
        operation_type = request.GET.get('operation_type')
        if operation_type:
            metrics = metrics.filter(operation_type=operation_type)
        
        success_filter = request.GET.get('success')
        if success_filter is not None:
            metrics = metrics.filter(success=success_filter.lower() == 'true')
        
        # Time range filter
        hours = request.GET.get('hours', 24)
        start_time = timezone.now() - timedelta(hours=int(hours))
        metrics = metrics.filter(timestamp__gte=start_time)
        
        # Pagination
        page_number = request.GET.get('page', 1)
        page_size = min(int(request.GET.get('page_size', 50)), 100)
        
        paginator = Paginator(metrics.order_by('-timestamp'), page_size)
        page_obj = paginator.get_page(page_number)
        
        metrics_data = []
        for metric in page_obj:
            metrics_data.append({
                'id': str(metric.id),
                'operation_type': metric.operation_type,
                'operation_name': metric.operation_name,
                'execution_time_ms': metric.execution_time_ms,
                'memory_usage_mb': metric.memory_usage_mb,
                'cpu_usage_percent': metric.cpu_usage_percent,
                'data_volume_mb': metric.data_volume_mb,
                'record_count': metric.record_count,
                'success': metric.success,
                'error_message': metric.error_message,
                'timestamp': metric.timestamp.isoformat()
            })
        
        return JsonResponse({
            'metrics': metrics_data,
            'pagination': {
                'page': page_obj.number,
                'pages': paginator.num_pages,
                'per_page': page_size,
                'total': paginator.count
            }
        })
        
    except Exception as e:
        logger.error("Failed to retrieve performance metrics", error=str(e))
        return JsonResponse({'error': 'Failed to retrieve performance metrics'}, status=500)


@require_http_methods(["GET"])
@login_required
def performance_summary(request):
    """Get performance summary statistics."""
    try:
        hours = int(request.GET.get('hours', 24))
        start_time = timezone.now() - timedelta(hours=hours)
        
        # Overall metrics
        total_operations = AnalyticsPerformanceMetric.objects.filter(
            timestamp__gte=start_time,
            is_active=True
        ).count()
        
        successful_operations = AnalyticsPerformanceMetric.objects.filter(
            timestamp__gte=start_time,
            success=True,
            is_active=True
        ).count()
        
        success_rate = (successful_operations / total_operations * 100) if total_operations > 0 else 0
        
        # Performance statistics
        perf_stats = AnalyticsPerformanceMetric.objects.filter(
            timestamp__gte=start_time,
            success=True,
            is_active=True
        ).aggregate(
            avg_execution_time=Avg('execution_time_ms'),
            max_execution_time=Max('execution_time_ms'),
            min_execution_time=Min('execution_time_ms'),
            avg_memory_usage=Avg('memory_usage_mb'),
            avg_cpu_usage=Avg('cpu_usage_percent')
        )
        
        # Operation type breakdown
        operation_breakdown = AnalyticsPerformanceMetric.objects.filter(
            timestamp__gte=start_time,
            is_active=True
        ).values('operation_type').annotate(
            count=Count('id'),
            avg_time=Avg('execution_time_ms'),
            success_count=Count('id', filter=Q(success=True))
        ).order_by('-count')
        
        # Active alerts
        active_alerts = AnalyticsPerformanceAlert.objects.filter(
            is_resolved=False,
            is_active=True
        ).count()
        
        return JsonResponse({
            'summary': {
                'total_operations': total_operations,
                'successful_operations': successful_operations,
                'success_rate': round(success_rate, 2),
                'active_alerts': active_alerts,
                'time_range_hours': hours
            },
            'performance_stats': {
                'avg_execution_time_ms': round(perf_stats['avg_execution_time'] or 0, 2),
                'max_execution_time_ms': perf_stats['max_execution_time'] or 0,
                'min_execution_time_ms': perf_stats['min_execution_time'] or 0,
                'avg_memory_usage_mb': round(perf_stats['avg_memory_usage'] or 0, 2),
                'avg_cpu_usage_percent': round(perf_stats['avg_cpu_usage'] or 0, 2)
            },
            'operation_breakdown': [
                {
                    'operation_type': item['operation_type'],
                    'count': item['count'],
                    'avg_time_ms': round(item['avg_time'] or 0, 2),
                    'success_rate': round((item['success_count'] / item['count'] * 100) if item['count'] > 0 else 0, 2)
                }
                for item in operation_breakdown
            ]
        })
        
    except Exception as e:
        logger.error("Failed to retrieve performance summary", error=str(e))
        return JsonResponse({'error': 'Failed to retrieve performance summary'}, status=500)


@require_http_methods(["GET"])
@login_required
def query_performance_list(request):
    """List query performance metrics."""
    try:
        queries = AnalyticsQueryPerformance.objects.filter(is_active=True)
        
        # Apply filters
        query_type = request.GET.get('query_type')
        if query_type:
            queries = queries.filter(query_type=query_type)
        
        # Time range filter
        hours = request.GET.get('hours', 24)
        start_time = timezone.now() - timedelta(hours=int(hours))
        queries = queries.filter(timestamp__gte=start_time)
        
        # Pagination
        page_number = request.GET.get('page', 1)
        page_size = min(int(request.GET.get('page_size', 50)), 100)
        
        paginator = Paginator(queries.order_by('-timestamp'), page_size)
        page_obj = paginator.get_page(page_number)
        
        queries_data = []
        for query in page_obj:
            queries_data.append({
                'id': str(query.id),
                'query_id': query.query_id,
                'query_type': query.query_type,
                'user': query.user.email if query.user else None,
                'execution_time_ms': query.execution_time_ms,
                'planning_time_ms': query.planning_time_ms,
                'data_scan_mb': query.data_scan_mb,
                'result_size_mb': query.result_size_mb,
                'cache_hit': query.cache_hit,
                'performance_score': query.performance_score,
                'timestamp': query.timestamp.isoformat()
            })
        
        return JsonResponse({
            'queries': queries_data,
            'pagination': {
                'page': page_obj.number,
                'pages': paginator.num_pages,
                'per_page': page_size,
                'total': paginator.count
            }
        })
        
    except Exception as e:
        logger.error("Failed to retrieve query performance", error=str(e))
        return JsonResponse({'error': 'Failed to retrieve query performance'}, status=500)


@require_http_methods(["GET"])
@login_required
def resource_usage_current(request):
    """Get current resource usage metrics."""
    try:
        # Get latest resource usage for each type
        latest_usage = {}
        resource_types = ['cpu', 'memory', 'disk_io', 'network_io', 'database_connections']
        
        for resource_type in resource_types:
            latest = AnalyticsResourceUsage.objects.filter(
                resource_type=resource_type,
                is_active=True
            ).order_by('-timestamp').first()
            
            if latest:
                latest_usage[resource_type] = {
                    'current_usage': latest.current_usage,
                    'peak_usage': latest.peak_usage,
                    'average_usage': latest.average_usage,
                    'usage_unit': latest.usage_unit,
                    'threshold_warning': latest.threshold_warning,
                    'threshold_critical': latest.threshold_critical,
                    'alert_triggered': latest.alert_triggered,
                    'timestamp': latest.timestamp.isoformat()
                }
        
        return JsonResponse({
            'resource_usage': latest_usage,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error("Failed to retrieve resource usage", error=str(e))
        return JsonResponse({'error': 'Failed to retrieve resource usage'}, status=500)


@require_http_methods(["GET"])
@login_required
def performance_alerts_list(request):
    """List performance alerts."""
    try:
        alerts = AnalyticsPerformanceAlert.objects.filter(is_active=True)
        
        # Apply filters
        severity = request.GET.get('severity')
        if severity:
            alerts = alerts.filter(severity=severity)
        
        resolved = request.GET.get('resolved')
        if resolved is not None:
            alerts = alerts.filter(is_resolved=resolved.lower() == 'true')
        
        # Pagination
        page_number = request.GET.get('page', 1)
        page_size = min(int(request.GET.get('page_size', 20)), 100)
        
        paginator = Paginator(alerts.order_by('-timestamp'), page_size)
        page_obj = paginator.get_page(page_number)
        
        alerts_data = []
        for alert in page_obj:
            alerts_data.append({
                'id': str(alert.id),
                'alert_type': alert.alert_type,
                'severity': alert.severity,
                'title': alert.title,
                'description': alert.description,
                'metric_name': alert.metric_name,
                'threshold_value': alert.threshold_value,
                'actual_value': alert.actual_value,
                'is_resolved': alert.is_resolved,
                'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None,
                'resolved_by': alert.resolved_by.email if alert.resolved_by else None,
                'timestamp': alert.timestamp.isoformat()
            })
        
        return JsonResponse({
            'alerts': alerts_data,
            'pagination': {
                'page': page_obj.number,
                'pages': paginator.num_pages,
                'per_page': page_size,
                'total': paginator.count
            }
        })
        
    except Exception as e:
        logger.error("Failed to retrieve performance alerts", error=str(e))
        return JsonResponse({'error': 'Failed to retrieve performance alerts'}, status=500)