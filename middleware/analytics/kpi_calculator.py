"""
KPI Calculator

Key Performance Indicator calculation engine for business intelligence analytics.
Provides automated KPI calculation, threshold monitoring, and trend analysis.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from scipy import stats
import structlog

from .models import (
    KPIRequest, KPIResult, KPIType, TimeRange, DataFilter, AnalyticsMetric
)
from .data_warehouse import DataWarehouseManager

logger = structlog.get_logger(__name__)

class KPICalculator:
    """
    Key Performance Indicator Calculator
    
    Provides comprehensive KPI calculation capabilities including:
    - Standard observability KPIs (availability, performance, error rates)
    - Custom KPI definitions and calculations
    - Threshold monitoring and alerting
    - Historical trend analysis
    - Variance and deviation calculations
    """
    
    def __init__(self, data_warehouse: DataWarehouseManager):
        self.data_warehouse = data_warehouse
        
        # KPI calculation statistics
        self._kpi_stats = {
            'total_calculations': 0,
            'successful_calculations': 0,
            'failed_calculations': 0,
            'kpis_by_type': {},
            'average_calculation_time_ms': 0.0
        }
        
        # Standard KPI definitions
        self.standard_kpis = {
            KPIType.AVAILABILITY: {
                'formula': 'uptime / (uptime + downtime) * 100',
                'unit': 'percent',
                'target': 99.9,
                'warning_threshold': 99.0,
                'critical_threshold': 95.0
            },
            KPIType.ERROR_RATE: {
                'formula': 'error_count / total_requests * 100',
                'unit': 'percent',
                'target': 0.1,
                'warning_threshold': 1.0,
                'critical_threshold': 5.0
            },
            KPIType.LATENCY: {
                'formula': 'avg(response_time)',
                'unit': 'milliseconds',
                'target': 100.0,
                'warning_threshold': 500.0,
                'critical_threshold': 1000.0
            },
            KPIType.THROUGHPUT: {
                'formula': 'sum(requests) / time_period_hours',
                'unit': 'requests_per_hour',
                'target': 1000.0,
                'warning_threshold': 500.0,
                'critical_threshold': 100.0
            },
            KPIType.RESOURCE_UTILIZATION: {
                'formula': 'avg(cpu_usage + memory_usage) / 2',
                'unit': 'percent',
                'target': 70.0,
                'warning_threshold': 80.0,
                'critical_threshold': 90.0
            }
        }
        
        logger.info("KPI Calculator initialized")
    
    async def calculate_kpi(self, request: KPIRequest) -> KPIResult:
        """
        Calculate a KPI based on the request parameters
        
        Args:
            request: KPI calculation request
            
        Returns:
            KPIResult with calculated KPI value and analysis
        """
        start_time = time.time()
        self._kpi_stats['total_calculations'] += 1
        
        try:
            logger.info("Starting KPI calculation",
                       request_id=request.request_id,
                       kpi_name=request.kpi_name,
                       kpi_type=request.kpi_type.value)
            
            # Get KPI definition
            kpi_definition = await self._get_kpi_definition(request)
            
            # Retrieve data for calculation
            data = await self._retrieve_kpi_data(request)
            
            if data.empty:
                return KPIResult(
                    request_id=request.request_id,
                    kpi_name=request.kpi_name,
                    kpi_type=request.kpi_type,
                    current_value=0.0,
                    status="no_data",
                    calculation_details={'message': 'No data available for KPI calculation'}
                )
            
            # Calculate KPI value
            kpi_value = await self._calculate_kpi_value(request, data, kpi_definition)
            
            # Calculate variance from target
            variance_from_target = None
            if request.target_value is not None:
                variance_from_target = ((kpi_value - request.target_value) / request.target_value) * 100
            elif kpi_definition.get('target') is not None:
                target = kpi_definition['target']
                variance_from_target = ((kpi_value - target) / target) * 100
            
            # Determine status based on thresholds
            status = await self._determine_kpi_status(request, kpi_value, kpi_definition)
            
            # Calculate trend
            trend_direction, trend_percentage = await self._calculate_kpi_trend(request, data, kpi_value)
            
            # Get historical values
            historical_values = await self._get_historical_kpi_values(request, data)
            
            # Prepare calculation details
            calculation_details = {
                'formula_used': kpi_definition.get('formula', 'custom'),
                'data_points_used': len(data),
                'time_range_hours': request.time_range.duration_hours,
                'calculation_method': await self._get_calculation_method(request.kpi_type),
                'data_quality_score': await self._assess_kpi_data_quality(data)
            }
            
            calculation_time_ms = (time.time() - start_time) * 1000
            
            # Update statistics
            self._kpi_stats['successful_calculations'] += 1
            self._update_kpi_type_stats(request.kpi_type)
            self._update_average_calculation_time(calculation_time_ms)
            
            result = KPIResult(
                request_id=request.request_id,
                kpi_name=request.kpi_name,
                kpi_type=request.kpi_type,
                current_value=kpi_value,
                target_value=request.target_value or kpi_definition.get('target'),
                variance_from_target=variance_from_target,
                status=status,
                trend_direction=trend_direction,
                trend_percentage=trend_percentage,
                historical_values=historical_values,
                calculation_details=calculation_details
            )
            
            logger.info("KPI calculation completed",
                       request_id=request.request_id,
                       kpi_value=kpi_value,
                       status=status,
                       calculation_time_ms=calculation_time_ms)
            
            return result
            
        except Exception as e:
            self._kpi_stats['failed_calculations'] += 1
            calculation_time_ms = (time.time() - start_time) * 1000
            
            logger.error("KPI calculation failed",
                        request_id=request.request_id,
                        error=str(e),
                        calculation_time_ms=calculation_time_ms)
            
            return KPIResult(
                request_id=request.request_id,
                kpi_name=request.kpi_name,
                kpi_type=request.kpi_type,
                current_value=0.0,
                status="error",
                calculation_details={'error': str(e)}
            )
    
    async def _get_kpi_definition(self, request: KPIRequest) -> Dict[str, Any]:
        """Get KPI definition from standard definitions or custom formula"""
        
        if request.kpi_type in self.standard_kpis:
            definition = self.standard_kpis[request.kpi_type].copy()
            
            # Override with request-specific values
            if request.target_value is not None:
                definition['target'] = request.target_value
            if request.warning_threshold is not None:
                definition['warning_threshold'] = request.warning_threshold
            if request.critical_threshold is not None:
                definition['critical_threshold'] = request.critical_threshold
            if request.calculation_formula is not None:
                definition['formula'] = request.calculation_formula
            
            return definition
        
        else:
            # Custom KPI
            return {
                'formula': request.calculation_formula or 'custom',
                'unit': 'custom',
                'target': request.target_value,
                'warning_threshold': request.warning_threshold,
                'critical_threshold': request.critical_threshold
            }
    
    async def _retrieve_kpi_data(self, request: KPIRequest) -> pd.DataFrame:
        """Retrieve data needed for KPI calculation"""
        
        # Build data query based on KPI type and data sources
        data_sources = request.data_sources if request.data_sources else self._get_default_data_sources(request.kpi_type)
        
        # Query data from warehouse
        data = await self.data_warehouse.query_observability_data(
            data_sources=data_sources,
            start_time=request.time_range.start_time,
            end_time=request.time_range.end_time,
            filters={f.field: f.value for f in request.filters} if request.filters else None
        )
        
        return data
    
    def _get_default_data_sources(self, kpi_type: KPIType) -> List[str]:
        """Get default data sources for KPI type"""
        
        mapping = {
            KPIType.AVAILABILITY: ['metrics', 'events'],
            KPIType.ERROR_RATE: ['metrics', 'events', 'logs'],
            KPIType.LATENCY: ['metrics', 'traces'],
            KPIType.THROUGHPUT: ['metrics', 'traces'],
            KPIType.PERFORMANCE: ['metrics', 'traces'],
            KPIType.RESOURCE_UTILIZATION: ['metrics'],
            KPIType.SECURITY_SCORE: ['events', 'logs'],
            KPIType.COMPLIANCE_SCORE: ['events', 'logs']
        }
        
        return mapping.get(kpi_type, ['metrics', 'events', 'logs', 'traces'])
    
    async def _calculate_kpi_value(self, request: KPIRequest, data: pd.DataFrame, 
                                  kpi_definition: Dict[str, Any]) -> float:
        """Calculate the actual KPI value"""
        
        try:
            if request.kpi_type == KPIType.AVAILABILITY:
                return await self._calculate_availability(data)
            
            elif request.kpi_type == KPIType.ERROR_RATE:
                return await self._calculate_error_rate(data)
            
            elif request.kpi_type == KPIType.LATENCY:
                return await self._calculate_latency(data)
            
            elif request.kpi_type == KPIType.THROUGHPUT:
                return await self._calculate_throughput(data, request.time_range)
            
            elif request.kpi_type == KPIType.RESOURCE_UTILIZATION:
                return await self._calculate_resource_utilization(data)
            
            elif request.kpi_type == KPIType.PERFORMANCE:
                return await self._calculate_performance_score(data)
            
            elif request.kpi_type == KPIType.SECURITY_SCORE:
                return await self._calculate_security_score(data)
            
            elif request.kpi_type == KPIType.COMPLIANCE_SCORE:
                return await self._calculate_compliance_score(data)
            
            elif request.kpi_type == KPIType.CUSTOM:
                return await self._calculate_custom_kpi(data, request.calculation_formula)
            
            else:
                # Fallback to simple average of numeric columns
                numeric_data = data.select_dtypes(include=[np.number])
                if not numeric_data.empty:
                    return float(numeric_data.mean().mean())
                return 0.0
        
        except Exception as e:
            logger.error("Error calculating KPI value", 
                        kpi_type=request.kpi_type.value, error=str(e))
            return 0.0
    
    async def _calculate_availability(self, data: pd.DataFrame) -> float:
        """Calculate availability KPI"""
        
        # Look for availability-related metrics
        availability_columns = [col for col in data.columns 
                              if any(keyword in col.lower() for keyword in ['availability', 'uptime', 'up'])]
        
        if availability_columns:
            # Use existing availability metrics
            availability_data = data[availability_columns[0]].dropna()
            if not availability_data.empty:
                return float(availability_data.mean())
        
        # Calculate from error events
        if 'data_source' in data.columns:
            events_data = data[data['data_source'] == 'events']
            if not events_data.empty and 'severity' in events_data.columns:
                total_events = len(events_data)
                error_events = len(events_data[events_data['severity'].isin(['error', 'critical'])])
                
                if total_events > 0:
                    availability = ((total_events - error_events) / total_events) * 100
                    return float(availability)
        
        # Default high availability if no error indicators
        return 99.9
    
    async def _calculate_error_rate(self, data: pd.DataFrame) -> float:
        """Calculate error rate KPI"""
        
        # Look for error rate metrics
        error_rate_columns = [col for col in data.columns 
                            if any(keyword in col.lower() for keyword in ['error_rate', 'error_count'])]
        
        if error_rate_columns:
            error_data = data[error_rate_columns[0]].dropna()
            if not error_data.empty:
                return float(error_data.mean())
        
        # Calculate from events and logs
        total_requests = 0
        error_requests = 0
        
        if 'data_source' in data.columns:
            # Count from events
            events_data = data[data['data_source'] == 'events']
            if not events_data.empty:
                total_requests += len(events_data)
                if 'severity' in events_data.columns:
                    error_requests += len(events_data[events_data['severity'].isin(['error', 'critical'])])
            
            # Count from logs
            logs_data = data[data['data_source'] == 'logs']
            if not logs_data.empty:
                total_requests += len(logs_data)
                if 'log_level' in logs_data.columns:
                    error_requests += len(logs_data[logs_data['log_level'].isin(['error', 'fatal'])])
        
        if total_requests > 0:
            error_rate = (error_requests / total_requests) * 100
            return float(error_rate)
        
        return 0.0
    
    async def _calculate_latency(self, data: pd.DataFrame) -> float:
        """Calculate latency KPI"""
        
        # Look for latency/response time metrics
        latency_columns = [col for col in data.columns 
                         if any(keyword in col.lower() for keyword in 
                               ['latency', 'response_time', 'duration'])]
        
        if latency_columns:
            latency_data = data[latency_columns[0]].dropna()
            if not latency_data.empty:
                return float(latency_data.mean())
        
        # Calculate from traces
        if 'data_source' in data.columns:
            traces_data = data[data['data_source'] == 'traces']
            if not traces_data.empty and 'duration_microseconds' in traces_data.columns:
                # Convert microseconds to milliseconds
                duration_ms = traces_data['duration_microseconds'] / 1000
                return float(duration_ms.mean())
        
        return 0.0
    
    async def _calculate_throughput(self, data: pd.DataFrame, time_range: TimeRange) -> float:
        """Calculate throughput KPI"""
        
        # Look for throughput metrics
        throughput_columns = [col for col in data.columns 
                            if any(keyword in col.lower() for keyword in ['throughput', 'requests', 'rps'])]
        
        if throughput_columns:
            throughput_data = data[throughput_columns[0]].dropna()
            if not throughput_data.empty:
                return float(throughput_data.sum())
        
        # Calculate from request counts
        total_requests = len(data)
        time_hours = time_range.duration_hours
        
        if time_hours > 0:
            throughput = total_requests / time_hours
            return float(throughput)
        
        return 0.0
    
    async def _calculate_resource_utilization(self, data: pd.DataFrame) -> float:
        """Calculate resource utilization KPI"""
        
        # Look for resource utilization metrics
        resource_columns = [col for col in data.columns 
                          if any(keyword in col.lower() for keyword in 
                                ['cpu', 'memory', 'disk', 'utilization', 'usage'])]
        
        if resource_columns:
            resource_data = data[resource_columns].select_dtypes(include=[np.number])
            if not resource_data.empty:
                return float(resource_data.mean().mean())
        
        return 0.0
    
    async def _calculate_performance_score(self, data: pd.DataFrame) -> float:
        """Calculate overall performance score"""
        
        # Combine multiple performance indicators
        performance_indicators = []
        
        # Latency component (lower is better)
        latency = await self._calculate_latency(data)
        if latency > 0:
            latency_score = max(0, 100 - (latency / 10))  # Normalize latency
            performance_indicators.append(latency_score)
        
        # Throughput component (higher is better)
        throughput = await self._calculate_throughput(data, TimeRange(
            start_time=datetime.now() - timedelta(hours=1),
            end_time=datetime.now()
        ))
        if throughput > 0:
            throughput_score = min(100, throughput / 10)  # Normalize throughput
            performance_indicators.append(throughput_score)
        
        # Error rate component (lower is better)
        error_rate = await self._calculate_error_rate(data)
        error_score = max(0, 100 - (error_rate * 10))
        performance_indicators.append(error_score)
        
        if performance_indicators:
            return float(np.mean(performance_indicators))
        
        return 50.0  # Neutral score
    
    async def _calculate_security_score(self, data: pd.DataFrame) -> float:
        """Calculate security score KPI"""
        
        security_score = 100.0  # Start with perfect score
        
        if 'data_source' in data.columns:
            # Analyze security events
            events_data = data[data['data_source'] == 'events']
            if not events_data.empty and 'category' in events_data.columns:
                security_events = events_data[events_data['category'] == 'security']
                
                if len(security_events) > 0:
                    # Deduct points for security events
                    critical_events = len(security_events[security_events.get('severity', '') == 'critical'])
                    error_events = len(security_events[security_events.get('severity', '') == 'error'])
                    warning_events = len(security_events[security_events.get('severity', '') == 'warning'])
                    
                    # Weighted deduction
                    deduction = (critical_events * 10) + (error_events * 5) + (warning_events * 1)
                    security_score = max(0, security_score - deduction)
        
        return float(security_score)
    
    async def _calculate_compliance_score(self, data: pd.DataFrame) -> float:
        """Calculate compliance score KPI"""
        
        # This is a simplified compliance score calculation
        # In practice, this would involve complex compliance rule evaluation
        
        compliance_score = 100.0
        
        if 'data_source' in data.columns:
            # Check for compliance-related events
            events_data = data[data['data_source'] == 'events']
            if not events_data.empty:
                # Look for compliance violations
                compliance_keywords = ['compliance', 'violation', 'audit', 'policy']
                
                for keyword in compliance_keywords:
                    if 'message' in events_data.columns:
                        violations = events_data[events_data['message'].str.contains(keyword, case=False, na=False)]
                        compliance_score -= len(violations) * 2  # Deduct 2 points per violation
        
        return float(max(0, compliance_score))
    
    async def _calculate_custom_kpi(self, data: pd.DataFrame, formula: Optional[str]) -> float:
        """Calculate custom KPI using provided formula"""
        
        if not formula:
            # Default to average of numeric columns
            numeric_data = data.select_dtypes(include=[np.number])
            if not numeric_data.empty:
                return float(numeric_data.mean().mean())
            return 0.0
        
        try:
            # Simple formula evaluation (in practice, use a safer evaluation method)
            # This is a simplified implementation
            
            # Replace common aggregation functions
            formula = formula.lower()
            numeric_columns = data.select_dtypes(include=[np.number]).columns.tolist()
            
            if 'avg(' in formula and numeric_columns:
                return float(data[numeric_columns[0]].mean())
            elif 'sum(' in formula and numeric_columns:
                return float(data[numeric_columns[0]].sum())
            elif 'count(' in formula:
                return float(len(data))
            elif 'max(' in formula and numeric_columns:
                return float(data[numeric_columns[0]].max())
            elif 'min(' in formula and numeric_columns:
                return float(data[numeric_columns[0]].min())
            
            # Default fallback
            if numeric_columns:
                return float(data[numeric_columns[0]].mean())
            
            return 0.0
        
        except Exception as e:
            logger.error("Error evaluating custom KPI formula", formula=formula, error=str(e))
            return 0.0
    
    async def _determine_kpi_status(self, request: KPIRequest, kpi_value: float, 
                                   kpi_definition: Dict[str, Any]) -> str:
        """Determine KPI status based on thresholds"""
        
        critical_threshold = request.critical_threshold or kpi_definition.get('critical_threshold')
        warning_threshold = request.warning_threshold or kpi_definition.get('warning_threshold')
        
        # For error rates and resource utilization, higher values are worse
        if request.kpi_type in [KPIType.ERROR_RATE, KPIType.RESOURCE_UTILIZATION]:
            if critical_threshold and kpi_value >= critical_threshold:
                return "critical"
            elif warning_threshold and kpi_value >= warning_threshold:
                return "warning"
            else:
                return "normal"
        
        # For availability, latency (inverted), throughput, higher values are better
        else:
            if critical_threshold and kpi_value <= critical_threshold:
                return "critical"
            elif warning_threshold and kpi_value <= warning_threshold:
                return "warning"
            else:
                return "normal"
    
    async def _calculate_kpi_trend(self, request: KPIRequest, data: pd.DataFrame, 
                                  current_value: float) -> tuple[Optional[str], Optional[float]]:
        """Calculate KPI trend direction and percentage change"""
        
        try:
            if 'timestamp' not in data.columns or len(data) < 2:
                return None, None
            
            # Sort by timestamp
            data_sorted = data.sort_values('timestamp')
            
            # Split into two halves for comparison
            mid_point = len(data_sorted) // 2
            first_half = data_sorted.iloc[:mid_point]
            second_half = data_sorted.iloc[mid_point:]
            
            # Calculate values for each half
            first_value = await self._calculate_kpi_value(request, first_half, {})
            second_value = await self._calculate_kpi_value(request, second_half, {})
            
            if first_value == 0:
                return None, None
            
            # Calculate percentage change
            percentage_change = ((second_value - first_value) / first_value) * 100
            
            # Determine trend direction
            if abs(percentage_change) < 1:  # Less than 1% change
                trend_direction = "stable"
            elif percentage_change > 0:
                trend_direction = "up"
            else:
                trend_direction = "down"
            
            return trend_direction, percentage_change
        
        except Exception as e:
            logger.error("Error calculating KPI trend", error=str(e))
            return None, None
    
    async def _get_historical_kpi_values(self, request: KPIRequest, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Get historical KPI values for trend analysis"""
        
        historical_values = []
        
        try:
            if 'timestamp' not in data.columns or len(data) < 5:
                return historical_values
            
            # Group data by time periods (e.g., hourly)
            data['timestamp'] = pd.to_datetime(data['timestamp'])
            data_grouped = data.groupby(pd.Grouper(key='timestamp', freq='H'))
            
            for timestamp, group_data in data_grouped:
                if len(group_data) > 0:
                    value = await self._calculate_kpi_value(request, group_data, {})
                    historical_values.append({
                        'timestamp': timestamp.isoformat(),
                        'value': value,
                        'data_points': len(group_data)
                    })
            
            # Limit to last 24 values
            return historical_values[-24:]
        
        except Exception as e:
            logger.error("Error getting historical KPI values", error=str(e))
            return []
    
    async def _assess_kpi_data_quality(self, data: pd.DataFrame) -> float:
        """Assess data quality for KPI calculation"""
        
        if data.empty:
            return 0.0
        
        # Simple data quality assessment
        total_cells = data.size
        non_null_cells = data.count().sum()
        completeness = non_null_cells / total_cells if total_cells > 0 else 0.0
        
        # Check for reasonable data distribution
        numeric_data = data.select_dtypes(include=[np.number])
        if not numeric_data.empty:
            # Check for extreme outliers
            outlier_ratio = 0.0
            for col in numeric_data.columns:
                col_data = numeric_data[col].dropna()
                if len(col_data) > 0:
                    Q1 = col_data.quantile(0.25)
                    Q3 = col_data.quantile(0.75)
                    IQR = Q3 - Q1
                    outliers = col_data[(col_data < Q1 - 3*IQR) | (col_data > Q3 + 3*IQR)]
                    outlier_ratio += len(outliers) / len(col_data)
            
            outlier_ratio = outlier_ratio / len(numeric_data.columns) if len(numeric_data.columns) > 0 else 0.0
            quality_score = completeness * (1 - min(0.5, outlier_ratio))
        else:
            quality_score = completeness
        
        return float(quality_score)
    
    async def _get_calculation_method(self, kpi_type: KPIType) -> str:
        """Get calculation method description for KPI type"""
        
        methods = {
            KPIType.AVAILABILITY: "Percentage of uptime vs total time",
            KPIType.ERROR_RATE: "Percentage of error events vs total events",
            KPIType.LATENCY: "Average response time across all requests",
            KPIType.THROUGHPUT: "Total requests per time period",
            KPIType.RESOURCE_UTILIZATION: "Average resource usage percentage",
            KPIType.PERFORMANCE: "Composite score of latency, throughput, and error rate",
            KPIType.SECURITY_SCORE: "Security score based on security events and violations",
            KPIType.COMPLIANCE_SCORE: "Compliance score based on policy violations",
            KPIType.CUSTOM: "Custom formula evaluation"
        }
        
        return methods.get(kpi_type, "Standard aggregation")
    
    def _update_kpi_type_stats(self, kpi_type: KPIType):
        """Update KPI type statistics"""
        type_key = kpi_type.value
        self._kpi_stats['kpis_by_type'][type_key] = (
            self._kpi_stats['kpis_by_type'].get(type_key, 0) + 1
        )
    
    def _update_average_calculation_time(self, calculation_time_ms: float):
        """Update average calculation time statistics"""
        current_avg = self._kpi_stats['average_calculation_time_ms']
        successful_calculations = self._kpi_stats['successful_calculations']
        
        if successful_calculations > 1:
            new_avg = ((current_avg * (successful_calculations - 1)) + calculation_time_ms) / successful_calculations
            self._kpi_stats['average_calculation_time_ms'] = new_avg
        else:
            self._kpi_stats['average_calculation_time_ms'] = calculation_time_ms
    
    async def get_kpi_statistics(self) -> Dict[str, Any]:
        """Get KPI calculator statistics"""
        return {
            'kpi_stats': self._kpi_stats.copy(),
            'standard_kpis_available': list(self.standard_kpis.keys()),
            'supported_kpi_types': [kpi_type.value for kpi_type in KPIType]
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check for the KPI calculator"""
        try:
            # Test basic calculation
            test_data = pd.DataFrame({
                'timestamp': pd.date_range('2024-01-01', periods=10, freq='H'),
                'value': np.random.normal(50, 10, 10)
            })
            
            test_request = KPIRequest(
                kpi_type=KPIType.CUSTOM,
                kpi_name="test_kpi",
                time_range=TimeRange(
                    start_time=datetime(2024, 1, 1),
                    end_time=datetime(2024, 1, 2)
                )
            )
            
            # Test calculation
            test_value = await self._calculate_custom_kpi(test_data, "avg(value)")
            
            status = "healthy" if test_value > 0 else "degraded"
            
            return {
                'status': status,
                'statistics': await self.get_kpi_statistics(),
                'test_calculation_result': test_value,
                'last_check': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'last_check': datetime.utcnow().isoformat()
            }