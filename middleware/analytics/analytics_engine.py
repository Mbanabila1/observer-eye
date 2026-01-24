"""
BI Analytics Engine

Core business intelligence and analytics engine providing advanced statistical analysis,
data processing, and insights generation for the Observer-Eye platform.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import structlog

from .models import (
    AnalyticsRequest, AnalyticsResult, TimeRange, DataFilter, 
    AggregationConfig, AnalyticsMetric, DataQualityMetrics
)
from .data_warehouse import DataWarehouseManager
from .kpi_calculator import KPICalculator
from .trend_analyzer import TrendAnalyzer
from .ml_pipeline import MachineLearningPipeline

logger = structlog.get_logger(__name__)

class BIAnalyticsEngine:
    """
    Advanced Business Intelligence Analytics Engine
    
    Provides comprehensive analytics capabilities including:
    - Statistical analysis and data processing
    - Real-time analytics and aggregations
    - Data quality assessment
    - Advanced correlation analysis
    - Predictive analytics integration
    """
    
    def __init__(self, 
                 data_warehouse_manager: Optional[DataWarehouseManager] = None,
                 enable_ml_pipeline: bool = True,
                 cache_results: bool = True):
        self.data_warehouse = data_warehouse_manager or DataWarehouseManager()
        self.kpi_calculator = KPICalculator(self.data_warehouse)
        self.trend_analyzer = TrendAnalyzer(self.data_warehouse)
        self.ml_pipeline = MachineLearningPipeline() if enable_ml_pipeline else None
        
        self.cache_results = cache_results
        self._results_cache = {}
        self._cache_ttl = 300  # 5 minutes
        
        # Analytics configuration
        self.max_data_points = 1000000  # Maximum data points to process
        self.default_sample_size = 10000  # Default sample size for large datasets
        
        # Performance tracking
        self._analytics_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_processing_time_ms': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        logger.info("BI Analytics Engine initialized",
                   ml_enabled=enable_ml_pipeline,
                   cache_enabled=cache_results)
    
    async def process_analytics_request(self, request: AnalyticsRequest) -> AnalyticsResult:
        """
        Process an analytics request and return comprehensive results
        
        Args:
            request: Analytics request with query parameters
            
        Returns:
            AnalyticsResult with processed data and metadata
        """
        start_time = time.time()
        self._analytics_stats['total_requests'] += 1
        
        try:
            logger.info("Processing analytics request",
                       request_id=request.request_id,
                       data_sources=request.data_sources,
                       time_range_hours=request.time_range.duration_hours)
            
            # Check cache first
            cache_key = self._generate_cache_key(request)
            if self.cache_results and cache_key in self._results_cache:
                cached_result = self._results_cache[cache_key]
                if time.time() - cached_result['timestamp'] < self._cache_ttl:
                    self._analytics_stats['cache_hits'] += 1
                    logger.debug("Returning cached analytics result", request_id=request.request_id)
                    return cached_result['result']
            
            self._analytics_stats['cache_misses'] += 1
            
            # Retrieve data from warehouse
            raw_data = await self._retrieve_data(request)
            
            if raw_data.empty:
                return AnalyticsResult(
                    request_id=request.request_id,
                    status="success",
                    data={},
                    metadata={'message': 'No data found for the specified criteria'},
                    processing_time_ms=(time.time() - start_time) * 1000,
                    row_count=0
                )
            
            # Assess data quality
            data_quality = await self._assess_data_quality(raw_data)
            
            # Apply filters
            filtered_data = await self._apply_filters(raw_data, request.filters)
            
            # Perform aggregations
            aggregated_data = await self._perform_aggregations(filtered_data, request.aggregations)
            
            # Calculate metrics
            metrics_results = await self._calculate_metrics(filtered_data, request.metrics)
            
            # Perform statistical analysis
            statistical_analysis = await self._perform_statistical_analysis(filtered_data)
            
            # Generate insights
            insights = await self._generate_insights(filtered_data, aggregated_data, metrics_results)
            
            # Prepare result data
            result_data = {
                'raw_data_sample': filtered_data.head(100).to_dict('records') if not filtered_data.empty else [],
                'aggregations': aggregated_data,
                'metrics': metrics_results,
                'statistical_analysis': statistical_analysis,
                'insights': insights,
                'data_quality': data_quality.__dict__
            }
            
            # Prepare metadata
            metadata = {
                'query_execution_time_ms': (time.time() - start_time) * 1000,
                'data_sources_queried': request.data_sources,
                'time_range': {
                    'start': request.time_range.start_time.isoformat(),
                    'end': request.time_range.end_time.isoformat(),
                    'duration_hours': request.time_range.duration_hours
                },
                'filters_applied': len(request.filters),
                'aggregations_performed': len(request.aggregations),
                'metrics_calculated': len(request.metrics),
                'original_row_count': len(raw_data),
                'filtered_row_count': len(filtered_data),
                'data_quality_score': data_quality.overall_score
            }
            
            processing_time_ms = (time.time() - start_time) * 1000
            
            result = AnalyticsResult(
                request_id=request.request_id,
                status="success",
                data=result_data,
                metadata=metadata,
                processing_time_ms=processing_time_ms,
                row_count=len(filtered_data)
            )
            
            # Cache result
            if self.cache_results:
                self._results_cache[cache_key] = {
                    'result': result,
                    'timestamp': time.time()
                }
            
            # Update statistics
            self._analytics_stats['successful_requests'] += 1
            self._update_average_processing_time(processing_time_ms)
            
            logger.info("Analytics request processed successfully",
                       request_id=request.request_id,
                       processing_time_ms=processing_time_ms,
                       row_count=len(filtered_data))
            
            return result
            
        except Exception as e:
            self._analytics_stats['failed_requests'] += 1
            processing_time_ms = (time.time() - start_time) * 1000
            
            logger.error("Analytics request processing failed",
                        request_id=request.request_id,
                        error=str(e),
                        processing_time_ms=processing_time_ms)
            
            return AnalyticsResult(
                request_id=request.request_id,
                status="error",
                data={},
                metadata={'error_details': str(e)},
                processing_time_ms=processing_time_ms,
                row_count=0,
                error_message=str(e)
            )
    
    async def _retrieve_data(self, request: AnalyticsRequest) -> pd.DataFrame:
        """Retrieve data from the data warehouse based on request parameters"""
        
        # Build query based on request parameters
        query_params = {
            'data_sources': request.data_sources,
            'start_time': request.time_range.start_time,
            'end_time': request.time_range.end_time,
            'limit': request.limit or self.max_data_points
        }
        
        # Retrieve data from warehouse
        data = await self.data_warehouse.query_observability_data(**query_params)
        
        return data
    
    async def _apply_filters(self, data: pd.DataFrame, filters: List[DataFilter]) -> pd.DataFrame:
        """Apply filters to the dataset"""
        
        if not filters or data.empty:
            return data
        
        filtered_data = data.copy()
        
        for filter_config in filters:
            try:
                field = filter_config.field
                operator = filter_config.operator
                value = filter_config.value
                
                if field not in filtered_data.columns:
                    logger.warning("Filter field not found in data", field=field)
                    continue
                
                # Apply filter based on operator
                if operator == 'eq':
                    filtered_data = filtered_data[filtered_data[field] == value]
                elif operator == 'ne':
                    filtered_data = filtered_data[filtered_data[field] != value]
                elif operator == 'gt':
                    filtered_data = filtered_data[filtered_data[field] > value]
                elif operator == 'lt':
                    filtered_data = filtered_data[filtered_data[field] < value]
                elif operator == 'gte':
                    filtered_data = filtered_data[filtered_data[field] >= value]
                elif operator == 'lte':
                    filtered_data = filtered_data[filtered_data[field] <= value]
                elif operator == 'in':
                    filtered_data = filtered_data[filtered_data[field].isin(value)]
                elif operator == 'not_in':
                    filtered_data = filtered_data[~filtered_data[field].isin(value)]
                elif operator == 'contains':
                    if filter_config.case_sensitive:
                        filtered_data = filtered_data[filtered_data[field].str.contains(value, na=False)]
                    else:
                        filtered_data = filtered_data[filtered_data[field].str.contains(value, case=False, na=False)]
                elif operator == 'regex':
                    filtered_data = filtered_data[filtered_data[field].str.match(value, na=False)]
                
            except Exception as e:
                logger.warning("Error applying filter", 
                              field=filter_config.field,
                              operator=filter_config.operator,
                              error=str(e))
                continue
        
        return filtered_data
    
    async def _perform_aggregations(self, data: pd.DataFrame, aggregations: List[AggregationConfig]) -> Dict[str, Any]:
        """Perform data aggregations"""
        
        if not aggregations or data.empty:
            return {}
        
        aggregation_results = {}
        
        for agg_config in aggregations:
            try:
                field = agg_config.field
                function = agg_config.function
                group_by = agg_config.group_by
                
                if field not in data.columns:
                    logger.warning("Aggregation field not found", field=field)
                    continue
                
                # Perform aggregation
                if group_by:
                    # Group by aggregation
                    valid_group_fields = [f for f in group_by if f in data.columns]
                    if valid_group_fields:
                        grouped_data = data.groupby(valid_group_fields)
                        
                        if function == AnalyticsMetric.MEAN:
                            result = grouped_data[field].mean()
                        elif function == AnalyticsMetric.MEDIAN:
                            result = grouped_data[field].median()
                        elif function == AnalyticsMetric.SUM:
                            result = grouped_data[field].sum()
                        elif function == AnalyticsMetric.COUNT:
                            result = grouped_data[field].count()
                        elif function == AnalyticsMetric.MIN:
                            result = grouped_data[field].min()
                        elif function == AnalyticsMetric.MAX:
                            result = grouped_data[field].max()
                        elif function == AnalyticsMetric.STANDARD_DEVIATION:
                            result = grouped_data[field].std()
                        elif function == AnalyticsMetric.VARIANCE:
                            result = grouped_data[field].var()
                        else:
                            result = grouped_data[field].mean()  # Default to mean
                        
                        aggregation_results[f"{field}_{function.value}_by_{'_'.join(valid_group_fields)}"] = result.to_dict()
                else:
                    # Simple aggregation
                    if function == AnalyticsMetric.MEAN:
                        result = data[field].mean()
                    elif function == AnalyticsMetric.MEDIAN:
                        result = data[field].median()
                    elif function == AnalyticsMetric.SUM:
                        result = data[field].sum()
                    elif function == AnalyticsMetric.COUNT:
                        result = data[field].count()
                    elif function == AnalyticsMetric.MIN:
                        result = data[field].min()
                    elif function == AnalyticsMetric.MAX:
                        result = data[field].max()
                    elif function == AnalyticsMetric.STANDARD_DEVIATION:
                        result = data[field].std()
                    elif function == AnalyticsMetric.VARIANCE:
                        result = data[field].var()
                    elif function == AnalyticsMetric.PERCENTILE_95:
                        result = data[field].quantile(0.95)
                    elif function == AnalyticsMetric.PERCENTILE_99:
                        result = data[field].quantile(0.99)
                    else:
                        result = data[field].mean()  # Default to mean
                    
                    aggregation_results[f"{field}_{function.value}"] = float(result) if pd.notna(result) else None
                
            except Exception as e:
                logger.warning("Error performing aggregation",
                              field=agg_config.field,
                              function=agg_config.function.value,
                              error=str(e))
                continue
        
        return aggregation_results
    
    async def _calculate_metrics(self, data: pd.DataFrame, metrics: List[AnalyticsMetric]) -> Dict[str, Any]:
        """Calculate specified metrics on the dataset"""
        
        if not metrics or data.empty:
            return {}
        
        metrics_results = {}
        
        # Get numeric columns for calculations
        numeric_columns = data.select_dtypes(include=[np.number]).columns.tolist()
        
        if not numeric_columns:
            return {'warning': 'No numeric columns found for metric calculations'}
        
        for metric in metrics:
            try:
                if metric == AnalyticsMetric.CORRELATION:
                    # Calculate correlation matrix for numeric columns
                    if len(numeric_columns) > 1:
                        correlation_matrix = data[numeric_columns].corr()
                        metrics_results['correlation_matrix'] = correlation_matrix.to_dict()
                
                elif metric == AnalyticsMetric.REGRESSION:
                    # Perform simple linear regression analysis
                    if len(numeric_columns) >= 2:
                        regression_results = {}
                        for i, col1 in enumerate(numeric_columns):
                            for col2 in numeric_columns[i+1:]:
                                try:
                                    x = data[col1].dropna()
                                    y = data[col2].dropna()
                                    
                                    if len(x) > 1 and len(y) > 1:
                                        # Align the data
                                        common_idx = x.index.intersection(y.index)
                                        if len(common_idx) > 1:
                                            x_aligned = x.loc[common_idx]
                                            y_aligned = y.loc[common_idx]
                                            
                                            slope, intercept, r_value, p_value, std_err = stats.linregress(x_aligned, y_aligned)
                                            
                                            regression_results[f"{col1}_vs_{col2}"] = {
                                                'slope': slope,
                                                'intercept': intercept,
                                                'r_squared': r_value ** 2,
                                                'p_value': p_value,
                                                'standard_error': std_err
                                            }
                                except Exception as e:
                                    logger.debug("Regression calculation failed", 
                                               col1=col1, col2=col2, error=str(e))
                                    continue
                        
                        metrics_results['regression_analysis'] = regression_results
                
                else:
                    # Calculate metric for each numeric column
                    column_metrics = {}
                    for col in numeric_columns:
                        try:
                            col_data = data[col].dropna()
                            
                            if len(col_data) == 0:
                                continue
                            
                            if metric == AnalyticsMetric.MEAN:
                                column_metrics[col] = float(col_data.mean())
                            elif metric == AnalyticsMetric.MEDIAN:
                                column_metrics[col] = float(col_data.median())
                            elif metric == AnalyticsMetric.MODE:
                                mode_result = col_data.mode()
                                column_metrics[col] = float(mode_result.iloc[0]) if len(mode_result) > 0 else None
                            elif metric == AnalyticsMetric.STANDARD_DEVIATION:
                                column_metrics[col] = float(col_data.std())
                            elif metric == AnalyticsMetric.VARIANCE:
                                column_metrics[col] = float(col_data.var())
                            elif metric == AnalyticsMetric.MIN:
                                column_metrics[col] = float(col_data.min())
                            elif metric == AnalyticsMetric.MAX:
                                column_metrics[col] = float(col_data.max())
                            elif metric == AnalyticsMetric.COUNT:
                                column_metrics[col] = int(len(col_data))
                            elif metric == AnalyticsMetric.SUM:
                                column_metrics[col] = float(col_data.sum())
                            elif metric == AnalyticsMetric.PERCENTILE_95:
                                column_metrics[col] = float(col_data.quantile(0.95))
                            elif metric == AnalyticsMetric.PERCENTILE_99:
                                column_metrics[col] = float(col_data.quantile(0.99))
                        
                        except Exception as e:
                            logger.debug("Metric calculation failed",
                                        column=col, metric=metric.value, error=str(e))
                            continue
                    
                    if column_metrics:
                        metrics_results[metric.value] = column_metrics
            
            except Exception as e:
                logger.warning("Error calculating metric",
                              metric=metric.value, error=str(e))
                continue
        
        return metrics_results
    
    async def _perform_statistical_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Perform comprehensive statistical analysis"""
        
        if data.empty:
            return {}
        
        analysis_results = {}
        
        try:
            # Basic statistics
            numeric_data = data.select_dtypes(include=[np.number])
            if not numeric_data.empty:
                analysis_results['descriptive_statistics'] = numeric_data.describe().to_dict()
                
                # Normality tests
                normality_tests = {}
                for col in numeric_data.columns:
                    col_data = numeric_data[col].dropna()
                    if len(col_data) > 3:  # Minimum sample size for normality test
                        try:
                            statistic, p_value = stats.shapiro(col_data.sample(min(5000, len(col_data))))
                            normality_tests[col] = {
                                'shapiro_wilk_statistic': statistic,
                                'p_value': p_value,
                                'is_normal': p_value > 0.05
                            }
                        except Exception:
                            pass
                
                analysis_results['normality_tests'] = normality_tests
                
                # Outlier detection using IQR method
                outliers = {}
                for col in numeric_data.columns:
                    col_data = numeric_data[col].dropna()
                    if len(col_data) > 0:
                        Q1 = col_data.quantile(0.25)
                        Q3 = col_data.quantile(0.75)
                        IQR = Q3 - Q1
                        lower_bound = Q1 - 1.5 * IQR
                        upper_bound = Q3 + 1.5 * IQR
                        
                        outlier_count = len(col_data[(col_data < lower_bound) | (col_data > upper_bound)])
                        outliers[col] = {
                            'count': outlier_count,
                            'percentage': (outlier_count / len(col_data)) * 100,
                            'lower_bound': lower_bound,
                            'upper_bound': upper_bound
                        }
                
                analysis_results['outlier_analysis'] = outliers
            
            # Categorical analysis
            categorical_data = data.select_dtypes(include=['object', 'category'])
            if not categorical_data.empty:
                categorical_analysis = {}
                for col in categorical_data.columns:
                    value_counts = categorical_data[col].value_counts()
                    categorical_analysis[col] = {
                        'unique_values': len(value_counts),
                        'most_frequent': value_counts.index[0] if len(value_counts) > 0 else None,
                        'most_frequent_count': int(value_counts.iloc[0]) if len(value_counts) > 0 else 0,
                        'distribution': value_counts.head(10).to_dict()
                    }
                
                analysis_results['categorical_analysis'] = categorical_analysis
            
            # Data completeness
            completeness = {}
            for col in data.columns:
                total_count = len(data)
                non_null_count = data[col].count()
                completeness[col] = {
                    'completeness_percentage': (non_null_count / total_count) * 100 if total_count > 0 else 0,
                    'null_count': total_count - non_null_count,
                    'non_null_count': non_null_count
                }
            
            analysis_results['data_completeness'] = completeness
            
        except Exception as e:
            logger.error("Error performing statistical analysis", error=str(e))
            analysis_results['error'] = str(e)
        
        return analysis_results
    
    async def _generate_insights(self, data: pd.DataFrame, aggregations: Dict[str, Any], 
                                metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate actionable insights from the analysis"""
        
        insights = {
            'data_insights': [],
            'performance_insights': [],
            'anomaly_insights': [],
            'trend_insights': [],
            'recommendations': []
        }
        
        try:
            # Data volume insights
            row_count = len(data)
            if row_count > 100000:
                insights['data_insights'].append({
                    'type': 'high_volume',
                    'message': f'Large dataset detected with {row_count:,} records',
                    'recommendation': 'Consider data sampling or partitioning for better performance'
                })
            
            # Performance insights from metrics
            if 'mean' in metrics:
                for col, mean_val in metrics['mean'].items():
                    if 'latency' in col.lower() or 'response_time' in col.lower():
                        if mean_val > 1000:  # Assuming milliseconds
                            insights['performance_insights'].append({
                                'type': 'high_latency',
                                'metric': col,
                                'value': mean_val,
                                'message': f'High average latency detected: {mean_val:.2f}ms',
                                'recommendation': 'Investigate performance bottlenecks'
                            })
            
            # Anomaly insights from outlier analysis
            if 'outlier_analysis' in metrics.get('statistical_analysis', {}):
                for col, outlier_info in metrics['statistical_analysis']['outlier_analysis'].items():
                    if outlier_info['percentage'] > 5:  # More than 5% outliers
                        insights['anomaly_insights'].append({
                            'type': 'high_outlier_rate',
                            'metric': col,
                            'percentage': outlier_info['percentage'],
                            'message': f'High outlier rate in {col}: {outlier_info["percentage"]:.1f}%',
                            'recommendation': 'Investigate data quality or system anomalies'
                        })
            
            # Correlation insights
            if 'correlation_matrix' in metrics:
                correlation_matrix = metrics['correlation_matrix']
                high_correlations = []
                
                for col1 in correlation_matrix:
                    for col2 in correlation_matrix[col1]:
                        if col1 != col2:
                            corr_value = correlation_matrix[col1][col2]
                            if abs(corr_value) > 0.8:  # Strong correlation
                                high_correlations.append({
                                    'metric1': col1,
                                    'metric2': col2,
                                    'correlation': corr_value
                                })
                
                if high_correlations:
                    insights['trend_insights'].append({
                        'type': 'strong_correlations',
                        'correlations': high_correlations,
                        'message': f'Found {len(high_correlations)} strong correlations between metrics',
                        'recommendation': 'Leverage these correlations for predictive modeling'
                    })
            
            # General recommendations
            if row_count < 100:
                insights['recommendations'].append({
                    'type': 'data_volume',
                    'message': 'Small dataset may limit statistical significance',
                    'action': 'Consider expanding time range or data sources'
                })
            
            if len(data.columns) > 50:
                insights['recommendations'].append({
                    'type': 'dimensionality',
                    'message': 'High-dimensional dataset detected',
                    'action': 'Consider feature selection or dimensionality reduction'
                })
        
        except Exception as e:
            logger.error("Error generating insights", error=str(e))
            insights['error'] = str(e)
        
        return insights
    
    async def _assess_data_quality(self, data: pd.DataFrame) -> DataQualityMetrics:
        """Assess data quality metrics"""
        
        if data.empty:
            return DataQualityMetrics(
                completeness=0.0, accuracy=0.0, consistency=0.0,
                timeliness=0.0, validity=0.0, uniqueness=0.0, overall_score=0.0
            )
        
        try:
            # Completeness: percentage of non-null values
            total_cells = data.size
            non_null_cells = data.count().sum()
            completeness = non_null_cells / total_cells if total_cells > 0 else 0.0
            
            # Uniqueness: percentage of unique rows
            total_rows = len(data)
            unique_rows = len(data.drop_duplicates())
            uniqueness = unique_rows / total_rows if total_rows > 0 else 0.0
            
            # Validity: percentage of valid data types (simplified check)
            validity_score = 1.0  # Assume valid unless proven otherwise
            
            # Consistency: check for consistent formats (simplified)
            consistency_score = 1.0  # Assume consistent unless proven otherwise
            
            # Timeliness: check if timestamp data is recent (if available)
            timeliness_score = 1.0
            timestamp_columns = [col for col in data.columns if 'timestamp' in col.lower() or 'time' in col.lower()]
            if timestamp_columns:
                try:
                    latest_timestamp = pd.to_datetime(data[timestamp_columns[0]]).max()
                    time_diff = datetime.now() - latest_timestamp
                    if time_diff.days > 7:  # Data older than 7 days
                        timeliness_score = max(0.0, 1.0 - (time_diff.days / 30))  # Decay over 30 days
                except Exception:
                    pass
            
            # Accuracy: simplified check based on data ranges and patterns
            accuracy_score = 1.0  # Assume accurate unless proven otherwise
            
            # Overall score
            overall_score = (completeness + accuracy_score + consistency_score + 
                           timeliness_score + validity_score + uniqueness) / 6
            
            return DataQualityMetrics(
                completeness=completeness,
                accuracy=accuracy_score,
                consistency=consistency_score,
                timeliness=timeliness_score,
                validity=validity_score,
                uniqueness=uniqueness,
                overall_score=overall_score
            )
        
        except Exception as e:
            logger.error("Error assessing data quality", error=str(e))
            return DataQualityMetrics(
                completeness=0.0, accuracy=0.0, consistency=0.0,
                timeliness=0.0, validity=0.0, uniqueness=0.0, overall_score=0.0,
                issues_detected=[f"Quality assessment failed: {str(e)}"]
            )
    
    def _generate_cache_key(self, request: AnalyticsRequest) -> str:
        """Generate cache key for analytics request"""
        key_components = [
            request.time_range.start_time.isoformat(),
            request.time_range.end_time.isoformat(),
            '_'.join(sorted(request.data_sources)),
            str(len(request.filters)),
            str(len(request.aggregations)),
            '_'.join(sorted([m.value for m in request.metrics]))
        ]
        return hash('_'.join(key_components))
    
    def _update_average_processing_time(self, processing_time_ms: float):
        """Update average processing time statistics"""
        current_avg = self._analytics_stats['average_processing_time_ms']
        successful_requests = self._analytics_stats['successful_requests']
        
        if successful_requests > 1:
            new_avg = ((current_avg * (successful_requests - 1)) + processing_time_ms) / successful_requests
            self._analytics_stats['average_processing_time_ms'] = new_avg
        else:
            self._analytics_stats['average_processing_time_ms'] = processing_time_ms
    
    async def get_analytics_statistics(self) -> Dict[str, Any]:
        """Get analytics engine statistics"""
        return {
            'analytics_stats': self._analytics_stats.copy(),
            'cache_stats': {
                'cache_size': len(self._results_cache),
                'cache_hit_rate': (
                    self._analytics_stats['cache_hits'] / 
                    (self._analytics_stats['cache_hits'] + self._analytics_stats['cache_misses'])
                    if (self._analytics_stats['cache_hits'] + self._analytics_stats['cache_misses']) > 0 else 0.0
                )
            },
            'configuration': {
                'max_data_points': self.max_data_points,
                'default_sample_size': self.default_sample_size,
                'cache_ttl_seconds': self._cache_ttl,
                'ml_pipeline_enabled': self.ml_pipeline is not None
            }
        }
    
    async def clear_cache(self):
        """Clear the analytics results cache"""
        self._results_cache.clear()
        logger.info("Analytics cache cleared")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check for the analytics engine"""
        try:
            # Test basic functionality
            test_data = pd.DataFrame({
                'test_metric': [1, 2, 3, 4, 5],
                'timestamp': pd.date_range('2024-01-01', periods=5, freq='H')
            })
            
            # Test statistical analysis
            stats_result = await self._perform_statistical_analysis(test_data)
            
            health_status = "healthy" if stats_result else "degraded"
            
            return {
                'status': health_status,
                'statistics': await self.get_analytics_statistics(),
                'components': {
                    'data_warehouse': await self.data_warehouse.health_check() if self.data_warehouse else None,
                    'kpi_calculator': self.kpi_calculator is not None,
                    'trend_analyzer': self.trend_analyzer is not None,
                    'ml_pipeline': self.ml_pipeline is not None
                },
                'last_check': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'last_check': datetime.utcnow().isoformat()
            }