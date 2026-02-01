"""
Analytics Engine for the Observer Eye Platform.
Provides business intelligence analysis capabilities and data processing.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from django.db.models import Q, Count, Sum, Avg, Min, Max, StdDev, F
from django.db.models.functions import TruncHour, TruncDay, TruncWeek, TruncMonth
from django.utils import timezone
import structlog

from .models import (
    DataSource, AnalyticsData, AnalyticsQuery, AnalyticsAggregation, AnalyticsInsight
)

logger = structlog.get_logger(__name__)


class QueryBuilder:
    """
    Builds complex analytics queries with filtering, aggregation, and grouping.
    """
    
    def __init__(self):
        self.base_query = AnalyticsData.objects.filter(is_active=True)
        self.filters = []
        self.aggregations = []
        self.groupings = []
    
    def filter_by_data_source(self, data_source_ids: List[str]) -> 'QueryBuilder':
        """Filter by data source IDs."""
        self.filters.append(Q(data_source_id__in=data_source_ids))
        return self
    
    def filter_by_metric_name(self, metric_names: List[str]) -> 'QueryBuilder':
        """Filter by metric names."""
        self.filters.append(Q(metric_name__in=metric_names))
        return self
    
    def filter_by_time_range(self, start_time: datetime, end_time: datetime) -> 'QueryBuilder':
        """Filter by time range."""
        self.filters.append(Q(timestamp__gte=start_time, timestamp__lte=end_time))
        return self
    
    def filter_by_dimensions(self, dimensions: Dict[str, Any]) -> 'QueryBuilder':
        """Filter by dimension values."""
        for key, value in dimensions.items():
            self.filters.append(Q(**{f'dimensions__{key}': value}))
        return self
    
    def filter_by_tags(self, tags: Dict[str, Any]) -> 'QueryBuilder':
        """Filter by tag values."""
        for key, value in tags.items():
            self.filters.append(Q(**{f'tags__{key}': value}))
        return self
    
    def group_by_time(self, time_bucket: str) -> 'QueryBuilder':
        """Group by time buckets."""
        time_functions = {
            '1h': TruncHour,
            '1d': TruncDay,
            '1w': TruncWeek,
            '1M': TruncMonth
        }
        
        if time_bucket in time_functions:
            self.groupings.append(('time_bucket', time_functions[time_bucket]('timestamp')))
        
        return self
    
    def group_by_dimension(self, dimension_key: str) -> 'QueryBuilder':
        """Group by dimension key."""
        self.groupings.append(('dimension', f'dimensions__{dimension_key}'))
        return self
    
    def group_by_metric_name(self) -> 'QueryBuilder':
        """Group by metric name."""
        self.groupings.append(('metric_name', 'metric_name'))
        return self
    
    def aggregate(self, aggregation_type: str, field: str = 'numeric_value') -> 'QueryBuilder':
        """Add aggregation."""
        agg_functions = {
            'sum': Sum,
            'avg': Avg,
            'min': Min,
            'max': Max,
            'count': Count,
            'stddev': StdDev
        }
        
        if aggregation_type in agg_functions:
            self.aggregations.append((aggregation_type, agg_functions[aggregation_type](field)))
        
        return self
    
    def build(self) -> Any:
        """Build and execute the query."""
        query = self.base_query
        
        # Apply filters
        for filter_q in self.filters:
            query = query.filter(filter_q)
        
        # Apply groupings
        if self.groupings:
            group_fields = {}
            for name, field in self.groupings:
                if isinstance(field, str):
                    query = query.values(field)
                    group_fields[name] = field
                else:
                    query = query.annotate(**{name: field}).values(name)
                    group_fields[name] = name
        
        # Apply aggregations
        if self.aggregations:
            agg_dict = {}
            for name, agg_func in self.aggregations:
                agg_dict[name] = agg_func
            query = query.annotate(**agg_dict)
        
        return query


class AnalyticsEngine:
    """
    Main analytics engine for processing and analyzing data.
    """
    
    def __init__(self):
        self.query_builder = QueryBuilder()
    
    def execute_query(self, analytics_query: AnalyticsQuery, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a stored analytics query with optional parameters.
        """
        try:
            query_def = analytics_query.query_definition
            params = parameters or {}
            
            # Build query based on definition
            builder = QueryBuilder()
            
            # Apply data source filters
            if 'data_sources' in query_def:
                data_source_ids = query_def['data_sources']
                builder.filter_by_data_source(data_source_ids)
            
            # Apply metric filters
            if 'metrics' in query_def:
                metric_names = query_def['metrics']
                builder.filter_by_metric_name(metric_names)
            
            # Apply time range
            if 'time_range' in query_def:
                time_range = query_def['time_range']
                start_time = datetime.fromisoformat(time_range['start'])
                end_time = datetime.fromisoformat(time_range['end'])
                builder.filter_by_time_range(start_time, end_time)
            
            # Apply parameter overrides
            if 'start_time' in params:
                start_time = datetime.fromisoformat(params['start_time'])
                if 'end_time' in params:
                    end_time = datetime.fromisoformat(params['end_time'])
                else:
                    end_time = timezone.now()
                builder.filter_by_time_range(start_time, end_time)
            
            # Apply grouping
            if 'group_by' in query_def:
                group_by = query_def['group_by']
                if group_by == 'time':
                    time_bucket = query_def.get('time_bucket', '1h')
                    builder.group_by_time(time_bucket)
                elif group_by == 'metric':
                    builder.group_by_metric_name()
                elif group_by.startswith('dimension:'):
                    dimension_key = group_by.split(':', 1)[1]
                    builder.group_by_dimension(dimension_key)
            
            # Apply aggregation
            if 'aggregation' in query_def:
                aggregation = query_def['aggregation']
                builder.aggregate(aggregation)
            
            # Execute query
            results = list(builder.build())
            
            return {
                'data': results,
                'count': len(results),
                'query_definition': query_def,
                'parameters': params
            }
            
        except Exception as e:
            logger.error("Failed to execute analytics query", query_id=str(analytics_query.id), error=str(e))
            raise
    
    def aggregate_data(self, query, aggregation_type: str, group_by: str = None, time_bucket: str = '1h') -> Dict[str, Any]:
        """
        Perform aggregation on analytics data.
        """
        try:
            builder = QueryBuilder()
            builder.base_query = query
            
            # Apply grouping
            if group_by == 'time':
                builder.group_by_time(time_bucket)
            elif group_by == 'metric':
                builder.group_by_metric_name()
            
            # Apply aggregation
            if aggregation_type == 'count':
                builder.aggregate('count', 'id')
            else:
                builder.aggregate(aggregation_type, 'numeric_value')
            
            results = list(builder.build())
            
            # Calculate summary statistics
            if results and aggregation_type != 'count':
                values = [item.get(aggregation_type, 0) for item in results if item.get(aggregation_type) is not None]
                summary = {
                    'total_records': len(results),
                    'min': min(values) if values else 0,
                    'max': max(values) if values else 0,
                    'avg': sum(values) / len(values) if values else 0
                }
            else:
                summary = {
                    'total_records': len(results),
                    'total_count': sum(item.get('count', 0) for item in results)
                }
            
            return {
                'data': results,
                'summary': summary
            }
            
        except Exception as e:
            logger.error("Failed to aggregate data", aggregation_type=aggregation_type, error=str(e))
            raise
    
    def calculate_trends(self, data_source: DataSource, metric_name: str, days: int = 30) -> Dict[str, Any]:
        """
        Calculate trends for a specific metric over time.
        """
        try:
            end_time = timezone.now()
            start_time = end_time - timedelta(days=days)
            
            # Get daily aggregated data
            daily_data = AnalyticsData.objects.filter(
                data_source=data_source,
                metric_name=metric_name,
                timestamp__gte=start_time,
                is_active=True,
                numeric_value__isnull=False
            ).annotate(
                day=TruncDay('timestamp')
            ).values('day').annotate(
                avg_value=Avg('numeric_value'),
                count=Count('id')
            ).order_by('day')
            
            if not daily_data:
                return {
                    'trend': 'no_data',
                    'direction': 'unknown',
                    'change_percentage': 0,
                    'data_points': 0
                }
            
            # Convert to pandas for analysis
            df = pd.DataFrame(list(daily_data))
            df['day'] = pd.to_datetime(df['day'])
            df = df.set_index('day')
            
            # Calculate trend
            if len(df) >= 2:
                # Linear regression for trend
                x = np.arange(len(df))
                y = df['avg_value'].values
                
                # Remove NaN values
                mask = ~np.isnan(y)
                if mask.sum() >= 2:
                    x_clean = x[mask]
                    y_clean = y[mask]
                    
                    slope, intercept = np.polyfit(x_clean, y_clean, 1)
                    
                    # Determine trend direction
                    if abs(slope) < 0.01:  # Threshold for "stable"
                        trend = 'stable'
                        direction = 'stable'
                    elif slope > 0:
                        trend = 'increasing'
                        direction = 'up'
                    else:
                        trend = 'decreasing'
                        direction = 'down'
                    
                    # Calculate percentage change
                    first_value = y_clean[0]
                    last_value = y_clean[-1]
                    if first_value != 0:
                        change_percentage = ((last_value - first_value) / first_value) * 100
                    else:
                        change_percentage = 0
                    
                    return {
                        'trend': trend,
                        'direction': direction,
                        'slope': slope,
                        'change_percentage': change_percentage,
                        'data_points': len(df),
                        'first_value': first_value,
                        'last_value': last_value,
                        'daily_data': df.reset_index().to_dict('records')
                    }
            
            return {
                'trend': 'insufficient_data',
                'direction': 'unknown',
                'change_percentage': 0,
                'data_points': len(df)
            }
            
        except Exception as e:
            logger.error("Failed to calculate trends", metric_name=metric_name, error=str(e))
            raise
    
    def detect_anomalies(self, data_source: DataSource, metric_name: str, sensitivity: float = 2.0) -> List[Dict[str, Any]]:
        """
        Detect anomalies in metric data using statistical methods.
        """
        try:
            # Get recent data (last 30 days)
            end_time = timezone.now()
            start_time = end_time - timedelta(days=30)
            
            data = AnalyticsData.objects.filter(
                data_source=data_source,
                metric_name=metric_name,
                timestamp__gte=start_time,
                is_active=True,
                numeric_value__isnull=False
            ).values('timestamp', 'numeric_value').order_by('timestamp')
            
            if len(data) < 10:  # Need minimum data points
                return []
            
            # Convert to pandas
            df = pd.DataFrame(list(data))
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('timestamp')
            
            # Calculate rolling statistics
            window_size = min(24, len(df) // 4)  # Adaptive window size
            df['rolling_mean'] = df['numeric_value'].rolling(window=window_size).mean()
            df['rolling_std'] = df['numeric_value'].rolling(window=window_size).std()
            
            # Detect anomalies using z-score
            df['z_score'] = (df['numeric_value'] - df['rolling_mean']) / df['rolling_std']
            anomalies = df[abs(df['z_score']) > sensitivity].copy()
            
            # Format anomalies
            anomaly_list = []
            for timestamp, row in anomalies.iterrows():
                anomaly_list.append({
                    'timestamp': timestamp.isoformat(),
                    'value': row['numeric_value'],
                    'expected_value': row['rolling_mean'],
                    'z_score': row['z_score'],
                    'severity': 'high' if abs(row['z_score']) > sensitivity * 1.5 else 'medium'
                })
            
            return anomaly_list
            
        except Exception as e:
            logger.error("Failed to detect anomalies", metric_name=metric_name, error=str(e))
            return []


class InsightGenerator:
    """
    Generates AI-powered insights from analytics data.
    """
    
    def __init__(self):
        self.analytics_engine = AnalyticsEngine()
    
    def generate_insights(self, data_source: DataSource, metric_names: List[str] = None, 
                         time_range: Dict[str, str] = None, insight_types: List[str] = None) -> List[Dict[str, Any]]:
        """
        Generate insights for specified metrics and time range.
        """
        insights = []
        
        try:
            # Default parameters
            if not metric_names:
                # Get top metrics by volume
                recent_metrics = AnalyticsData.objects.filter(
                    data_source=data_source,
                    is_active=True,
                    timestamp__gte=timezone.now() - timedelta(days=7)
                ).values('metric_name').annotate(
                    count=Count('id')
                ).order_by('-count')[:5]
                
                metric_names = [item['metric_name'] for item in recent_metrics]
            
            if not insight_types:
                insight_types = ['anomaly', 'trend']
            
            # Generate insights for each metric
            for metric_name in metric_names:
                if 'anomaly' in insight_types:
                    anomaly_insights = self._generate_anomaly_insights(data_source, metric_name)
                    insights.extend(anomaly_insights)
                
                if 'trend' in insight_types:
                    trend_insights = self._generate_trend_insights(data_source, metric_name)
                    insights.extend(trend_insights)
            
            # Sort by confidence score
            insights.sort(key=lambda x: x['confidence_score'], reverse=True)
            
            return insights[:10]  # Return top 10 insights
            
        except Exception as e:
            logger.error("Failed to generate insights", error=str(e))
            return []
    
    def _generate_anomaly_insights(self, data_source: DataSource, metric_name: str) -> List[Dict[str, Any]]:
        """Generate anomaly-based insights."""
        insights = []
        
        try:
            anomalies = self.analytics_engine.detect_anomalies(data_source, metric_name)
            
            if anomalies:
                # Group anomalies by severity
                high_severity = [a for a in anomalies if a['severity'] == 'high']
                medium_severity = [a for a in anomalies if a['severity'] == 'medium']
                
                if high_severity:
                    insights.append({
                        'title': f'High Severity Anomalies Detected in {metric_name}',
                        'description': f'Found {len(high_severity)} high severity anomalies in {metric_name} metric. '
                                     f'Values deviated significantly from expected patterns.',
                        'type': 'anomaly',
                        'metric_names': [metric_name],
                        'confidence_score': 0.9,
                        'impact_score': 0.8,
                        'time_range': {
                            'start': min(a['timestamp'] for a in high_severity),
                            'end': max(a['timestamp'] for a in high_severity)
                        },
                        'analysis_data': {
                            'anomaly_count': len(high_severity),
                            'max_z_score': max(abs(a['z_score']) for a in high_severity),
                            'anomalies': high_severity
                        },
                        'recommendations': [
                            'Investigate the root cause of anomalous values',
                            'Check for system issues during anomaly periods',
                            'Consider adjusting alert thresholds if anomalies are expected'
                        ]
                    })
                
                if medium_severity:
                    insights.append({
                        'title': f'Medium Severity Anomalies in {metric_name}',
                        'description': f'Detected {len(medium_severity)} medium severity anomalies in {metric_name}. '
                                     f'Monitor for potential issues.',
                        'type': 'anomaly',
                        'metric_names': [metric_name],
                        'confidence_score': 0.7,
                        'impact_score': 0.5,
                        'time_range': {
                            'start': min(a['timestamp'] for a in medium_severity),
                            'end': max(a['timestamp'] for a in medium_severity)
                        },
                        'analysis_data': {
                            'anomaly_count': len(medium_severity),
                            'anomalies': medium_severity
                        },
                        'recommendations': [
                            'Monitor the metric for recurring patterns',
                            'Consider seasonal adjustments if applicable'
                        ]
                    })
            
        except Exception as e:
            logger.error("Failed to generate anomaly insights", metric_name=metric_name, error=str(e))
        
        return insights
    
    def _generate_trend_insights(self, data_source: DataSource, metric_name: str) -> List[Dict[str, Any]]:
        """Generate trend-based insights."""
        insights = []
        
        try:
            trend_data = self.analytics_engine.calculate_trends(data_source, metric_name)
            
            if trend_data['trend'] in ['increasing', 'decreasing']:
                confidence = min(0.9, abs(trend_data['change_percentage']) / 100)
                impact = min(0.8, abs(trend_data['change_percentage']) / 50)
                
                direction_text = 'increasing' if trend_data['direction'] == 'up' else 'decreasing'
                change_pct = abs(trend_data['change_percentage'])
                
                insights.append({
                    'title': f'{metric_name} is {direction_text.title()}',
                    'description': f'The {metric_name} metric shows a {direction_text} trend with '
                                 f'{change_pct:.1f}% change over the analysis period.',
                    'type': 'trend',
                    'metric_names': [metric_name],
                    'confidence_score': confidence,
                    'impact_score': impact,
                    'time_range': {
                        'start': (timezone.now() - timedelta(days=30)).isoformat(),
                        'end': timezone.now().isoformat()
                    },
                    'analysis_data': {
                        'trend_direction': trend_data['direction'],
                        'change_percentage': trend_data['change_percentage'],
                        'slope': trend_data.get('slope', 0),
                        'data_points': trend_data['data_points']
                    },
                    'recommendations': [
                        f'Monitor the {direction_text} trend in {metric_name}',
                        'Investigate factors contributing to the trend',
                        'Consider capacity planning if trend continues'
                    ] if direction_text == 'increasing' else [
                        f'Investigate the cause of {direction_text} {metric_name}',
                        'Check for system issues or reduced usage',
                        'Verify if the decrease is expected'
                    ]
                })
            
        except Exception as e:
            logger.error("Failed to generate trend insights", metric_name=metric_name, error=str(e))
        
        return insights