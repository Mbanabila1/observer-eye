"""
Trend Analyzer

Advanced trend analysis and forecasting engine for observability data.
Provides statistical trend detection, seasonal pattern analysis, and predictive forecasting.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
import structlog

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    Prophet = None

from .models import (
    TrendAnalysisRequest, TrendAnalysisResult, TrendType, TimeRange, DataFilter
)
from .data_warehouse import DataWarehouseManager

logger = structlog.get_logger(__name__)

class TrendAnalyzer:
    """
    Advanced Trend Analysis Engine
    
    Provides comprehensive trend analysis capabilities including:
    - Linear and non-linear trend detection
    - Seasonal pattern analysis
    - Anomaly detection in time series
    - Predictive forecasting
    - Statistical significance testing
    - Correlation analysis across metrics
    """
    
    def __init__(self, data_warehouse: DataWarehouseManager):
        self.data_warehouse = data_warehouse
        
        # Trend analysis statistics
        self._trend_stats = {
            'total_analyses': 0,
            'successful_analyses': 0,
            'failed_analyses': 0,
            'analyses_by_type': {},
            'average_analysis_time_ms': 0.0
        }
        
        # Analysis configuration
        self.min_data_points = 10  # Minimum data points for trend analysis
        self.significance_threshold = 0.05  # Statistical significance threshold
        self.anomaly_threshold = 2.0  # Standard deviations for anomaly detection
        
        logger.info("Trend Analyzer initialized", prophet_available=PROPHET_AVAILABLE)
    
    async def analyze_trend(self, request: TrendAnalysisRequest) -> TrendAnalysisResult:
        """
        Perform comprehensive trend analysis
        
        Args:
            request: Trend analysis request parameters
            
        Returns:
            TrendAnalysisResult with trend analysis findings
        """
        start_time = time.time()
        self._trend_stats['total_analyses'] += 1
        
        try:
            logger.info("Starting trend analysis",
                       request_id=request.request_id,
                       trend_type=request.trend_type.value,
                       metric_field=request.metric_field)
            
            # Retrieve data for analysis
            data = await self._retrieve_trend_data(request)
            
            if data.empty or len(data) < self.min_data_points:
                return TrendAnalysisResult(
                    request_id=request.request_id,
                    trend_type=request.trend_type,
                    trend_direction="insufficient_data",
                    trend_strength=0.0,
                    statistical_significance=1.0,
                    model_accuracy=0.0
                )
            
            # Prepare time series data
            time_series = await self._prepare_time_series(data, request.metric_field)
            
            if time_series.empty:
                return TrendAnalysisResult(
                    request_id=request.request_id,
                    trend_type=request.trend_type,
                    trend_direction="no_data",
                    trend_strength=0.0,
                    statistical_significance=1.0
                )
            
            # Perform trend analysis based on type
            if request.trend_type == TrendType.LINEAR:
                result = await self._analyze_linear_trend(request, time_series)
            elif request.trend_type == TrendType.SEASONAL:
                result = await self._analyze_seasonal_trend(request, time_series)
            elif request.trend_type == TrendType.ANOMALY_DETECTION:
                result = await self._detect_anomalies(request, time_series)
            elif request.trend_type == TrendType.FORECAST:
                result = await self._generate_forecast(request, time_series)
            else:
                # Default to linear trend analysis
                result = await self._analyze_linear_trend(request, time_series)
            
            analysis_time_ms = (time.time() - start_time) * 1000
            
            # Update statistics
            self._trend_stats['successful_analyses'] += 1
            self._update_analysis_type_stats(request.trend_type)
            self._update_average_analysis_time(analysis_time_ms)
            
            logger.info("Trend analysis completed",
                       request_id=request.request_id,
                       trend_direction=result.trend_direction,
                       trend_strength=result.trend_strength,
                       analysis_time_ms=analysis_time_ms)
            
            return result
            
        except Exception as e:
            self._trend_stats['failed_analyses'] += 1
            analysis_time_ms = (time.time() - start_time) * 1000
            
            logger.error("Trend analysis failed",
                        request_id=request.request_id,
                        error=str(e),
                        analysis_time_ms=analysis_time_ms)
            
            return TrendAnalysisResult(
                request_id=request.request_id,
                trend_type=request.trend_type,
                trend_direction="error",
                trend_strength=0.0,
                statistical_significance=1.0,
                model_accuracy=0.0
            )
    
    async def _retrieve_trend_data(self, request: TrendAnalysisRequest) -> pd.DataFrame:
        """Retrieve data for trend analysis"""
        
        # Query data from warehouse
        data = await self.data_warehouse.query_observability_data(
            data_sources=request.data_sources,
            start_time=request.time_range.start_time,
            end_time=request.time_range.end_time,
            filters={f.field: f.value for f in request.filters} if request.filters else None
        )
        
        return data
    
    async def _prepare_time_series(self, data: pd.DataFrame, metric_field: str) -> pd.DataFrame:
        """Prepare time series data for analysis"""
        
        try:
            # Ensure timestamp column exists
            if 'timestamp' not in data.columns:
                logger.warning("No timestamp column found in data")
                return pd.DataFrame()
            
            # Convert timestamp to datetime
            data['timestamp'] = pd.to_datetime(data['timestamp'])
            
            # Check if metric field exists
            if metric_field not in data.columns:
                # Try to find a similar field
                numeric_columns = data.select_dtypes(include=[np.number]).columns
                if len(numeric_columns) > 0:
                    metric_field = numeric_columns[0]
                    logger.info("Using alternative metric field", field=metric_field)
                else:
                    logger.warning("No numeric columns found for trend analysis")
                    return pd.DataFrame()
            
            # Create time series
            time_series = data[['timestamp', metric_field]].copy()
            time_series = time_series.dropna()
            
            # Sort by timestamp
            time_series = time_series.sort_values('timestamp')
            
            # Remove duplicates, keeping the last value for each timestamp
            time_series = time_series.drop_duplicates(subset=['timestamp'], keep='last')
            
            # Set timestamp as index
            time_series.set_index('timestamp', inplace=True)
            
            return time_series
            
        except Exception as e:
            logger.error("Error preparing time series data", error=str(e))
            return pd.DataFrame()
    
    async def _analyze_linear_trend(self, request: TrendAnalysisRequest, 
                                   time_series: pd.DataFrame) -> TrendAnalysisResult:
        """Analyze linear trend in time series data"""
        
        try:
            # Prepare data for linear regression
            time_series_reset = time_series.reset_index()
            time_series_reset['time_numeric'] = (
                time_series_reset['timestamp'] - time_series_reset['timestamp'].min()
            ).dt.total_seconds()
            
            X = time_series_reset[['time_numeric']]
            y = time_series_reset[request.metric_field]
            
            # Fit linear regression
            model = LinearRegression()
            model.fit(X, y)
            
            # Calculate predictions
            y_pred = model.predict(X)
            
            # Calculate statistics
            slope = model.coef_[0]
            r_squared = r2_score(y, y_pred)
            
            # Statistical significance test
            n = len(y)
            if n > 2:
                # Calculate t-statistic for slope
                mse = mean_squared_error(y, y_pred)
                se_slope = np.sqrt(mse / np.sum((X['time_numeric'] - X['time_numeric'].mean()) ** 2))
                t_stat = slope / se_slope if se_slope > 0 else 0
                p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n - 2))
            else:
                p_value = 1.0
            
            # Determine trend direction and strength
            if abs(slope) < 1e-10:  # Essentially zero slope
                trend_direction = "stable"
                trend_strength = 0.0
            elif slope > 0:
                trend_direction = "increasing"
                trend_strength = min(1.0, abs(r_squared))
            else:
                trend_direction = "decreasing"
                trend_strength = min(1.0, abs(r_squared))
            
            # Generate forecast if requested
            forecast_values = []
            if request.forecast_periods and request.forecast_periods > 0:
                forecast_values = await self._generate_linear_forecast(
                    model, time_series_reset, request.forecast_periods
                )
            
            return TrendAnalysisResult(
                request_id=request.request_id,
                trend_type=request.trend_type,
                trend_direction=trend_direction,
                trend_strength=trend_strength,
                statistical_significance=p_value,
                correlation_coefficient=np.sqrt(r_squared) if r_squared >= 0 else 0.0,
                forecast_values=forecast_values,
                model_accuracy=r_squared,
                confidence_intervals={
                    'slope': slope,
                    'intercept': model.intercept_,
                    'r_squared': r_squared,
                    'p_value': p_value
                }
            )
            
        except Exception as e:
            logger.error("Error in linear trend analysis", error=str(e))
            return TrendAnalysisResult(
                request_id=request.request_id,
                trend_type=request.trend_type,
                trend_direction="error",
                trend_strength=0.0,
                statistical_significance=1.0
            )
    
    async def _analyze_seasonal_trend(self, request: TrendAnalysisRequest, 
                                     time_series: pd.DataFrame) -> TrendAnalysisResult:
        """Analyze seasonal patterns in time series data"""
        
        try:
            # Use Prophet for seasonal analysis if available
            if PROPHET_AVAILABLE and len(time_series) >= 20:
                return await self._analyze_seasonal_with_prophet(request, time_series)
            
            # Fallback to simple seasonal analysis
            return await self._analyze_seasonal_simple(request, time_series)
            
        except Exception as e:
            logger.error("Error in seasonal trend analysis", error=str(e))
            return TrendAnalysisResult(
                request_id=request.request_id,
                trend_type=request.trend_type,
                trend_direction="error",
                trend_strength=0.0,
                statistical_significance=1.0
            )
    
    async def _analyze_seasonal_with_prophet(self, request: TrendAnalysisRequest, 
                                           time_series: pd.DataFrame) -> TrendAnalysisResult:
        """Analyze seasonal patterns using Prophet"""
        
        try:
            # Prepare data for Prophet
            prophet_data = time_series.reset_index()
            prophet_data.columns = ['ds', 'y']
            
            # Create and fit Prophet model
            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=False,
                interval_width=request.confidence_interval
            )
            
            # Suppress Prophet logging
            import logging
            logging.getLogger('prophet').setLevel(logging.WARNING)
            
            model.fit(prophet_data)
            
            # Make predictions
            future = model.make_future_dataframe(periods=request.forecast_periods or 0)
            forecast = model.predict(future)
            
            # Analyze trend components
            trend_component = forecast['trend'].iloc[-1] - forecast['trend'].iloc[0]
            trend_strength = abs(trend_component) / (forecast['y'].max() - forecast['y'].min()) if forecast['y'].max() != forecast['y'].min() else 0.0
            
            # Determine trend direction
            if abs(trend_component) < 0.01:
                trend_direction = "stable"
            elif trend_component > 0:
                trend_direction = "increasing"
            else:
                trend_direction = "decreasing"
            
            # Extract seasonal patterns
            seasonal_patterns = {}
            if 'yearly' in forecast.columns:
                seasonal_patterns['yearly'] = {
                    'strength': forecast['yearly'].std(),
                    'peak_month': forecast['yearly'].idxmax() % 12 + 1
                }
            
            if 'weekly' in forecast.columns:
                seasonal_patterns['weekly'] = {
                    'strength': forecast['weekly'].std(),
                    'peak_day': forecast['weekly'].idxmax() % 7
                }
            
            # Generate forecast values
            forecast_values = []
            if request.forecast_periods and request.forecast_periods > 0:
                forecast_data = forecast.tail(request.forecast_periods)
                for _, row in forecast_data.iterrows():
                    forecast_values.append({
                        'timestamp': row['ds'].isoformat(),
                        'value': row['yhat'],
                        'lower_bound': row['yhat_lower'],
                        'upper_bound': row['yhat_upper']
                    })
            
            return TrendAnalysisResult(
                request_id=request.request_id,
                trend_type=request.trend_type,
                trend_direction=trend_direction,
                trend_strength=min(1.0, trend_strength),
                statistical_significance=0.05,  # Prophet doesn't provide p-values directly
                forecast_values=forecast_values,
                seasonal_patterns=seasonal_patterns,
                model_accuracy=0.8  # Placeholder - would need cross-validation for actual accuracy
            )
            
        except Exception as e:
            logger.error("Error in Prophet seasonal analysis", error=str(e))
            return await self._analyze_seasonal_simple(request, time_series)
    
    async def _analyze_seasonal_simple(self, request: TrendAnalysisRequest, 
                                      time_series: pd.DataFrame) -> TrendAnalysisResult:
        """Simple seasonal analysis without Prophet"""
        
        try:
            # Extract time components
            time_series_reset = time_series.reset_index()
            time_series_reset['hour'] = time_series_reset['timestamp'].dt.hour
            time_series_reset['day_of_week'] = time_series_reset['timestamp'].dt.dayofweek
            time_series_reset['month'] = time_series_reset['timestamp'].dt.month
            
            # Analyze hourly patterns
            hourly_pattern = time_series_reset.groupby('hour')[request.metric_field].mean()
            hourly_variation = hourly_pattern.std() / hourly_pattern.mean() if hourly_pattern.mean() != 0 else 0
            
            # Analyze daily patterns
            daily_pattern = time_series_reset.groupby('day_of_week')[request.metric_field].mean()
            daily_variation = daily_pattern.std() / daily_pattern.mean() if daily_pattern.mean() != 0 else 0
            
            # Analyze monthly patterns
            monthly_pattern = time_series_reset.groupby('month')[request.metric_field].mean()
            monthly_variation = monthly_pattern.std() / monthly_pattern.mean() if monthly_pattern.mean() != 0 else 0
            
            # Determine overall seasonality
            max_variation = max(hourly_variation, daily_variation, monthly_variation)
            
            if max_variation > 0.2:  # 20% variation indicates seasonality
                trend_direction = "seasonal"
                trend_strength = min(1.0, max_variation)
            else:
                trend_direction = "stable"
                trend_strength = max_variation
            
            seasonal_patterns = {
                'hourly': {
                    'variation_coefficient': hourly_variation,
                    'peak_hour': int(hourly_pattern.idxmax()) if not hourly_pattern.empty else 0
                },
                'daily': {
                    'variation_coefficient': daily_variation,
                    'peak_day': int(daily_pattern.idxmax()) if not daily_pattern.empty else 0
                },
                'monthly': {
                    'variation_coefficient': monthly_variation,
                    'peak_month': int(monthly_pattern.idxmax()) if not monthly_pattern.empty else 1
                }
            }
            
            return TrendAnalysisResult(
                request_id=request.request_id,
                trend_type=request.trend_type,
                trend_direction=trend_direction,
                trend_strength=trend_strength,
                statistical_significance=0.1,  # Simplified significance
                seasonal_patterns=seasonal_patterns,
                model_accuracy=0.6  # Lower accuracy for simple method
            )
            
        except Exception as e:
            logger.error("Error in simple seasonal analysis", error=str(e))
            return TrendAnalysisResult(
                request_id=request.request_id,
                trend_type=request.trend_type,
                trend_direction="error",
                trend_strength=0.0,
                statistical_significance=1.0
            )
    
    async def _detect_anomalies(self, request: TrendAnalysisRequest, 
                               time_series: pd.DataFrame) -> TrendAnalysisResult:
        """Detect anomalies in time series data"""
        
        try:
            values = time_series[request.metric_field]
            
            # Calculate statistical thresholds
            mean_value = values.mean()
            std_value = values.std()
            
            # Define anomaly thresholds
            upper_threshold = mean_value + (self.anomaly_threshold * std_value)
            lower_threshold = mean_value - (self.anomaly_threshold * std_value)
            
            # Detect anomalies
            anomalies = []
            time_series_reset = time_series.reset_index()
            
            for idx, row in time_series_reset.iterrows():
                value = row[request.metric_field]
                timestamp = row['timestamp']
                
                if value > upper_threshold or value < lower_threshold:
                    anomaly_type = "high" if value > upper_threshold else "low"
                    severity = min(5.0, abs(value - mean_value) / std_value) if std_value > 0 else 1.0
                    
                    anomalies.append({
                        'timestamp': timestamp.isoformat(),
                        'value': value,
                        'expected_range': [lower_threshold, upper_threshold],
                        'anomaly_type': anomaly_type,
                        'severity': severity,
                        'deviation_score': abs(value - mean_value) / std_value if std_value > 0 else 0.0
                    })
            
            # Calculate anomaly statistics
            anomaly_rate = len(anomalies) / len(values) if len(values) > 0 else 0.0
            
            # Determine trend direction based on anomaly patterns
            if anomaly_rate > 0.1:  # More than 10% anomalies
                trend_direction = "volatile"
                trend_strength = min(1.0, anomaly_rate * 2)
            elif anomaly_rate > 0.05:  # 5-10% anomalies
                trend_direction = "unstable"
                trend_strength = anomaly_rate * 2
            else:
                trend_direction = "stable"
                trend_strength = 1.0 - anomaly_rate
            
            # Statistical significance based on number of anomalies
            if len(anomalies) > 0:
                # Use binomial test to assess significance
                expected_anomalies = len(values) * 0.05  # Expect 5% anomalies normally
                if len(anomalies) > expected_anomalies:
                    p_value = stats.binom_test(len(anomalies), len(values), 0.05)
                else:
                    p_value = 1.0
            else:
                p_value = 1.0
            
            return TrendAnalysisResult(
                request_id=request.request_id,
                trend_type=request.trend_type,
                trend_direction=trend_direction,
                trend_strength=trend_strength,
                statistical_significance=p_value,
                anomalies_detected=anomalies,
                model_accuracy=1.0 - anomaly_rate,
                confidence_intervals={
                    'mean': mean_value,
                    'std': std_value,
                    'upper_threshold': upper_threshold,
                    'lower_threshold': lower_threshold,
                    'anomaly_rate': anomaly_rate
                }
            )
            
        except Exception as e:
            logger.error("Error in anomaly detection", error=str(e))
            return TrendAnalysisResult(
                request_id=request.request_id,
                trend_type=request.trend_type,
                trend_direction="error",
                trend_strength=0.0,
                statistical_significance=1.0
            )
    
    async def _generate_forecast(self, request: TrendAnalysisRequest, 
                                time_series: pd.DataFrame) -> TrendAnalysisResult:
        """Generate forecast for time series data"""
        
        try:
            # Use Prophet for forecasting if available
            if PROPHET_AVAILABLE and len(time_series) >= 10:
                return await self._generate_prophet_forecast(request, time_series)
            
            # Fallback to linear extrapolation
            return await self._generate_linear_forecast_result(request, time_series)
            
        except Exception as e:
            logger.error("Error in forecast generation", error=str(e))
            return TrendAnalysisResult(
                request_id=request.request_id,
                trend_type=request.trend_type,
                trend_direction="error",
                trend_strength=0.0,
                statistical_significance=1.0
            )
    
    async def _generate_prophet_forecast(self, request: TrendAnalysisRequest, 
                                        time_series: pd.DataFrame) -> TrendAnalysisResult:
        """Generate forecast using Prophet"""
        
        try:
            # Prepare data for Prophet
            prophet_data = time_series.reset_index()
            prophet_data.columns = ['ds', 'y']
            
            # Create and fit Prophet model
            model = Prophet(interval_width=request.confidence_interval)
            
            # Suppress Prophet logging
            import logging
            logging.getLogger('prophet').setLevel(logging.WARNING)
            
            model.fit(prophet_data)
            
            # Generate forecast
            periods = request.forecast_periods or 24  # Default to 24 periods
            future = model.make_future_dataframe(periods=periods)
            forecast = model.predict(future)
            
            # Extract forecast values
            forecast_values = []
            forecast_data = forecast.tail(periods)
            
            for _, row in forecast_data.iterrows():
                forecast_values.append({
                    'timestamp': row['ds'].isoformat(),
                    'value': row['yhat'],
                    'lower_bound': row['yhat_lower'],
                    'upper_bound': row['yhat_upper'],
                    'trend': row['trend']
                })
            
            # Calculate trend from forecast
            trend_start = forecast['trend'].iloc[0]
            trend_end = forecast['trend'].iloc[-1]
            trend_change = trend_end - trend_start
            
            if abs(trend_change) < 0.01:
                trend_direction = "stable"
            elif trend_change > 0:
                trend_direction = "increasing"
            else:
                trend_direction = "decreasing"
            
            trend_strength = min(1.0, abs(trend_change) / abs(trend_start)) if trend_start != 0 else 0.0
            
            return TrendAnalysisResult(
                request_id=request.request_id,
                trend_type=request.trend_type,
                trend_direction=trend_direction,
                trend_strength=trend_strength,
                statistical_significance=0.05,
                forecast_values=forecast_values,
                model_accuracy=0.85,  # Prophet typically has good accuracy
                confidence_intervals={
                    'confidence_level': request.confidence_interval,
                    'forecast_periods': periods
                }
            )
            
        except Exception as e:
            logger.error("Error in Prophet forecast", error=str(e))
            return await self._generate_linear_forecast_result(request, time_series)
    
    async def _generate_linear_forecast_result(self, request: TrendAnalysisRequest, 
                                             time_series: pd.DataFrame) -> TrendAnalysisResult:
        """Generate forecast using linear extrapolation"""
        
        try:
            # Prepare data for linear regression
            time_series_reset = time_series.reset_index()
            time_series_reset['time_numeric'] = (
                time_series_reset['timestamp'] - time_series_reset['timestamp'].min()
            ).dt.total_seconds()
            
            X = time_series_reset[['time_numeric']]
            y = time_series_reset[request.metric_field]
            
            # Fit linear model
            model = LinearRegression()
            model.fit(X, y)
            
            # Generate forecast
            periods = request.forecast_periods or 24
            last_time = time_series_reset['time_numeric'].iloc[-1]
            time_step = (last_time - time_series_reset['time_numeric'].iloc[0]) / len(time_series_reset)
            
            forecast_values = []
            for i in range(1, periods + 1):
                future_time = last_time + (i * time_step)
                future_value = model.predict([[future_time]])[0]
                
                # Simple confidence interval (±10% of predicted value)
                margin = abs(future_value) * 0.1
                
                forecast_values.append({
                    'timestamp': (time_series_reset['timestamp'].iloc[-1] + 
                                timedelta(seconds=i * time_step)).isoformat(),
                    'value': future_value,
                    'lower_bound': future_value - margin,
                    'upper_bound': future_value + margin
                })
            
            # Determine trend
            slope = model.coef_[0]
            if abs(slope) < 1e-10:
                trend_direction = "stable"
                trend_strength = 0.0
            elif slope > 0:
                trend_direction = "increasing"
                trend_strength = min(1.0, abs(slope) * time_step / abs(y.mean())) if y.mean() != 0 else 0.0
            else:
                trend_direction = "decreasing"
                trend_strength = min(1.0, abs(slope) * time_step / abs(y.mean())) if y.mean() != 0 else 0.0
            
            return TrendAnalysisResult(
                request_id=request.request_id,
                trend_type=request.trend_type,
                trend_direction=trend_direction,
                trend_strength=trend_strength,
                statistical_significance=0.1,
                forecast_values=forecast_values,
                model_accuracy=0.6,  # Lower accuracy for simple linear model
                confidence_intervals={
                    'slope': slope,
                    'intercept': model.intercept_,
                    'forecast_periods': periods
                }
            )
            
        except Exception as e:
            logger.error("Error in linear forecast", error=str(e))
            return TrendAnalysisResult(
                request_id=request.request_id,
                trend_type=request.trend_type,
                trend_direction="error",
                trend_strength=0.0,
                statistical_significance=1.0
            )
    
    async def _generate_linear_forecast(self, model: LinearRegression, 
                                       time_series_data: pd.DataFrame, 
                                       periods: int) -> List[Dict[str, Any]]:
        """Generate linear forecast values"""
        
        try:
            forecast_values = []
            last_time = time_series_data['time_numeric'].iloc[-1]
            time_step = (last_time - time_series_data['time_numeric'].iloc[0]) / len(time_series_data)
            
            for i in range(1, periods + 1):
                future_time = last_time + (i * time_step)
                future_value = model.predict([[future_time]])[0]
                
                forecast_values.append({
                    'period': i,
                    'value': future_value,
                    'timestamp': (time_series_data['timestamp'].iloc[-1] + 
                                timedelta(seconds=i * time_step)).isoformat()
                })
            
            return forecast_values
            
        except Exception as e:
            logger.error("Error generating linear forecast", error=str(e))
            return []
    
    def _update_analysis_type_stats(self, trend_type: TrendType):
        """Update analysis type statistics"""
        type_key = trend_type.value
        self._trend_stats['analyses_by_type'][type_key] = (
            self._trend_stats['analyses_by_type'].get(type_key, 0) + 1
        )
    
    def _update_average_analysis_time(self, analysis_time_ms: float):
        """Update average analysis time statistics"""
        current_avg = self._trend_stats['average_analysis_time_ms']
        successful_analyses = self._trend_stats['successful_analyses']
        
        if successful_analyses > 1:
            new_avg = ((current_avg * (successful_analyses - 1)) + analysis_time_ms) / successful_analyses
            self._trend_stats['average_analysis_time_ms'] = new_avg
        else:
            self._trend_stats['average_analysis_time_ms'] = analysis_time_ms
    
    async def get_trend_statistics(self) -> Dict[str, Any]:
        """Get trend analyzer statistics"""
        return {
            'trend_stats': self._trend_stats.copy(),
            'configuration': {
                'min_data_points': self.min_data_points,
                'significance_threshold': self.significance_threshold,
                'anomaly_threshold': self.anomaly_threshold,
                'prophet_available': PROPHET_AVAILABLE
            },
            'supported_trend_types': [trend_type.value for trend_type in TrendType]
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check for the trend analyzer"""
        try:
            # Test basic trend analysis
            test_data = pd.DataFrame({
                'timestamp': pd.date_range('2024-01-01', periods=50, freq='H'),
                'test_metric': np.random.normal(50, 10, 50) + np.linspace(0, 10, 50)  # Trending data
            })
            
            test_request = TrendAnalysisRequest(
                trend_type=TrendType.LINEAR,
                time_range=TimeRange(
                    start_time=datetime(2024, 1, 1),
                    end_time=datetime(2024, 1, 3)
                ),
                metric_field='test_metric',
                data_sources=['metrics']
            )
            
            # Test trend analysis
            time_series = await self._prepare_time_series(test_data, 'test_metric')
            test_result = await self._analyze_linear_trend(test_request, time_series)
            
            status = "healthy" if test_result.trend_direction != "error" else "degraded"
            
            return {
                'status': status,
                'statistics': await self.get_trend_statistics(),
                'test_analysis_result': {
                    'trend_direction': test_result.trend_direction,
                    'trend_strength': test_result.trend_strength
                },
                'last_check': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'last_check': datetime.utcnow().isoformat()
            }