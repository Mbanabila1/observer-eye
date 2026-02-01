"""
Analytics views for the Observer Eye Platform.
Provides BI analysis capabilities and data visualization endpoints.
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg, Min, Max, StdDev
from django.db.models.functions import TruncHour, TruncDay, TruncWeek, TruncMonth
import structlog

from .models import (
    DataSource, AnalyticsData, AnalyticsQuery, AnalyticsReport,
    AnalyticsDashboard, AnalyticsAlert, AnalyticsAggregation, AnalyticsInsight
)
from .analytics_engine import AnalyticsEngine, QueryBuilder, InsightGenerator
from core.utils import DataValidator, AuditLogger

logger = structlog.get_logger(__name__)


@require_http_methods(["GET"])
@login_required
def data_sources_list(request):
    """List available data sources."""
    try:
        sources = DataSource.objects.filter(is_active=True).order_by('name')
        
        # Apply filters
        source_type = request.GET.get('type')
        if source_type:
            sources = sources.filter(source_type=source_type)
        
        # Pagination
        page_number = request.GET.get('page', 1)
        page_size = min(int(request.GET.get('page_size', 20)), 100)
        
        paginator = Paginator(sources, page_size)
        page_obj = paginator.get_page(page_number)
        
        sources_data = []
        for source in page_obj:
            sources_data.append({
                'id': str(source.id),
                'name': source.name,
                'description': source.description,
                'source_type': source.source_type,
                'is_enabled': source.is_enabled,
                'last_sync': source.last_sync.isoformat() if source.last_sync else None,
                'sync_frequency': source.sync_frequency,
                'created_at': source.created_at.isoformat()
            })
        
        return JsonResponse({
            'data_sources': sources_data,
            'pagination': {
                'page': page_obj.number,
                'pages': paginator.num_pages,
                'per_page': page_size,
                'total': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            }
        })
        
    except Exception as e:
        logger.error("Failed to retrieve data sources", error=str(e))
        return JsonResponse({'error': 'Failed to retrieve data sources'}, status=500)


@require_http_methods(["GET"])
@login_required
def analytics_data_query(request):
    """Query analytics data with flexible filtering and aggregation."""
    try:
        # Parse query parameters
        data_source_id = request.GET.get('data_source')
        metric_name = request.GET.get('metric_name')
        start_time = request.GET.get('start_time')
        end_time = request.GET.get('end_time')
        aggregation = request.GET.get('aggregation', 'raw')  # raw, sum, avg, min, max, count
        group_by = request.GET.get('group_by')  # time, dimension
        time_bucket = request.GET.get('time_bucket', '1h')  # 1m, 5m, 15m, 1h, 1d
        
        # Build base query
        query = AnalyticsData.objects.filter(is_active=True)
        
        if data_source_id:
            query = query.filter(data_source_id=data_source_id)
        
        if metric_name:
            query = query.filter(metric_name=metric_name)
        
        # Time range filtering
        if start_time:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            query = query.filter(timestamp__gte=start_dt)
        
        if end_time:
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            query = query.filter(timestamp__lte=end_dt)
        
        # Apply aggregation
        if aggregation == 'raw':
            # Return raw data with pagination
            page_number = request.GET.get('page', 1)
            page_size = min(int(request.GET.get('page_size', 100)), 1000)
            
            paginator = Paginator(query.order_by('-timestamp'), page_size)
            page_obj = paginator.get_page(page_number)
            
            data = []
            for item in page_obj:
                data.append({
                    'id': str(item.id),
                    'metric_name': item.metric_name,
                    'metric_type': item.metric_type,
                    'metric_value': item.metric_value,
                    'dimensions': item.dimensions,
                    'tags': item.tags,
                    'timestamp': item.timestamp.isoformat(),
                    'numeric_value': item.numeric_value,
                    'string_value': item.string_value
                })
            
            return JsonResponse({
                'data': data,
                'aggregation': 'raw',
                'pagination': {
                    'page': page_obj.number,
                    'pages': paginator.num_pages,
                    'per_page': page_size,
                    'total': paginator.count
                }
            })
        
        else:
            # Apply aggregation using simplified logic for now
            # In a real implementation, this would use the AnalyticsEngine
            if aggregation == 'count':
                result = query.count()
                return JsonResponse({
                    'data': [{'value': result, 'aggregation': 'count'}],
                    'aggregation': aggregation
                })
            elif aggregation in ['sum', 'avg', 'min', 'max'] and query.exists():
                # Simple aggregation on numeric_value
                agg_func = {
                    'sum': Sum('numeric_value'),
                    'avg': Avg('numeric_value'),
                    'min': Min('numeric_value'),
                    'max': Max('numeric_value')
                }
                result = query.aggregate(value=agg_func[aggregation])
                return JsonResponse({
                    'data': [{'value': result['value'] or 0, 'aggregation': aggregation}],
                    'aggregation': aggregation
                })
            else:
                return JsonResponse({
                    'data': [],
                    'aggregation': aggregation,
                    'message': 'No data available for aggregation'
                })
        
    except Exception as e:
        logger.error("Failed to query analytics data", error=str(e))
        return JsonResponse({'error': 'Failed to query analytics data'}, status=500)


@require_http_methods(["GET"])
@login_required
def analytics_summary(request):
    """Get analytics summary and key metrics."""
    try:
        # Time range for summary
        end_time = timezone.now()
        start_time = end_time - timedelta(days=7)  # Last 7 days
        
        # Get summary statistics
        total_data_points = AnalyticsData.objects.filter(
            timestamp__gte=start_time,
            is_active=True
        ).count()
        
        active_data_sources = DataSource.objects.filter(
            is_active=True,
            is_enabled=True
        ).count()
        
        recent_insights = AnalyticsInsight.objects.filter(
            created_at__gte=start_time,
            is_active=True
        ).count()
        
        unacknowledged_insights = AnalyticsInsight.objects.filter(
            is_acknowledged=False,
            is_active=True
        ).count()
        
        # Top metrics by volume
        top_metrics = AnalyticsData.objects.filter(
            timestamp__gte=start_time,
            is_active=True
        ).values('metric_name').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Data sources activity
        source_activity = AnalyticsData.objects.filter(
            timestamp__gte=start_time,
            is_active=True
        ).values(
            'data_source__name'
        ).annotate(
            count=Count('id'),
            last_data=Max('timestamp')
        ).order_by('-count')[:10]
        
        return JsonResponse({
            'summary': {
                'total_data_points': total_data_points,
                'active_data_sources': active_data_sources,
                'recent_insights': recent_insights,
                'unacknowledged_insights': unacknowledged_insights,
                'time_range': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat()
                }
            },
            'top_metrics': [
                {
                    'metric_name': item['metric_name'],
                    'count': item['count']
                }
                for item in top_metrics
            ],
            'source_activity': [
                {
                    'data_source': item['data_source__name'],
                    'count': item['count'],
                    'last_data': item['last_data'].isoformat() if item['last_data'] else None
                }
                for item in source_activity
            ]
        })
        
    except Exception as e:
        logger.error("Failed to retrieve analytics summary", error=str(e))
        return JsonResponse({'error': 'Failed to retrieve analytics summary'}, status=500)


@require_http_methods(["GET"])
@login_required
def metric_statistics(request):
    """Get statistical analysis for specific metrics."""
    try:
        metric_name = request.GET.get('metric_name')
        data_source_id = request.GET.get('data_source_id')
        days = int(request.GET.get('days', 7))
        
        if not metric_name:
            return JsonResponse({'error': 'metric_name is required'}, status=400)
        
        # Time range
        end_time = timezone.now()
        start_time = end_time - timedelta(days=days)
        
        # Build query
        query = AnalyticsData.objects.filter(
            metric_name=metric_name,
            timestamp__gte=start_time,
            is_active=True,
            numeric_value__isnull=False
        )
        
        if data_source_id:
            query = query.filter(data_source_id=data_source_id)
        
        # Calculate statistics
        stats = query.aggregate(
            count=Count('id'),
            sum=Sum('numeric_value'),
            avg=Avg('numeric_value'),
            min=Min('numeric_value'),
            max=Max('numeric_value'),
            stddev=StdDev('numeric_value')
        )
        
        # Time series data (daily aggregation)
        daily_data = query.annotate(
            day=TruncDay('timestamp')
        ).values('day').annotate(
            count=Count('id'),
            avg_value=Avg('numeric_value'),
            sum_value=Sum('numeric_value')
        ).order_by('day')
        
        return JsonResponse({
            'metric_name': metric_name,
            'time_range': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat(),
                'days': days
            },
            'statistics': {
                'count': stats['count'] or 0,
                'sum': stats['sum'] or 0,
                'average': stats['avg'] or 0,
                'minimum': stats['min'] or 0,
                'maximum': stats['max'] or 0,
                'standard_deviation': stats['stddev'] or 0
            },
            'daily_data': [
                {
                    'date': item['day'].isoformat(),
                    'count': item['count'],
                    'average': item['avg_value'] or 0,
                    'sum': item['sum_value'] or 0
                }
                for item in daily_data
            ]
        })
        
    except Exception as e:
        logger.error("Failed to retrieve metric statistics", error=str(e))
        return JsonResponse({'error': 'Failed to retrieve metric statistics'}, status=500)
