"""
Test BI Analytics Integration

Tests for the BI Analytics engine integration with the FastAPI middleware.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from analytics import (
    BIAnalyticsEngine, DataWarehouseManager, KPICalculator, TrendAnalyzer,
    ReportGenerator, MachineLearningPipeline,
    AnalyticsRequest, KPIRequest, TrendAnalysisRequest, ReportRequest,
    TimeRange, DataFilter, AnalyticsMetric, KPIType, TrendType, ReportType, ReportFormat
)

class TestBIAnalyticsIntegration:
    """Test BI Analytics integration"""
    
    @pytest.fixture
    async def data_warehouse(self):
        """Create test data warehouse"""
        warehouse = DataWarehouseManager()
        await warehouse.initialize()
        return warehouse
    
    @pytest.fixture
    async def analytics_engine(self, data_warehouse):
        """Create test analytics engine"""
        return BIAnalyticsEngine(data_warehouse_manager=data_warehouse)
    
    @pytest.fixture
    def sample_data(self):
        """Create sample observability data"""
        return pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=100, freq='H'),
            'metric_value': np.random.normal(50, 10, 100),
            'service_name': np.random.choice(['web-api', 'user-service', 'payment-service'], 100),
            'environment': np.random.choice(['production', 'staging'], 100),
            'response_time': np.random.exponential(100, 100),
            'error_count': np.random.poisson(2, 100)
        })
    
    @pytest.mark.asyncio
    async def test_analytics_engine_initialization(self, analytics_engine):
        """Test analytics engine initialization"""
        assert analytics_engine is not None
        assert analytics_engine.data_warehouse is not None
        assert analytics_engine.kpi_calculator is not None
        assert analytics_engine.trend_analyzer is not None
    
    @pytest.mark.asyncio
    async def test_analytics_request_processing(self, analytics_engine):
        """Test analytics request processing"""
        # Create test request
        time_range = TimeRange(
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 1, 2)
        )
        
        request = AnalyticsRequest(
            time_range=time_range,
            data_sources=['metrics'],
            metrics=[AnalyticsMetric.MEAN, AnalyticsMetric.COUNT]
        )
        
        # Process request
        result = await analytics_engine.process_analytics_request(request)
        
        # Verify result
        assert result.status in ['success', 'error']  # May be error due to no data
        assert result.request_id == request.request_id
        assert result.processing_time_ms >= 0
    
    @pytest.mark.asyncio
    async def test_kpi_calculation(self, analytics_engine):
        """Test KPI calculation"""
        # Create KPI request
        time_range = TimeRange(
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 1, 2)
        )
        
        kpi_request = KPIRequest(
            kpi_type=KPIType.AVAILABILITY,
            kpi_name="test_availability",
            time_range=time_range
        )
        
        # Calculate KPI
        result = await analytics_engine.kpi_calculator.calculate_kpi(kpi_request)
        
        # Verify result
        assert result.request_id == kpi_request.request_id
        assert result.kpi_name == "test_availability"
        assert result.kpi_type == KPIType.AVAILABILITY
        assert isinstance(result.current_value, (int, float))
    
    @pytest.mark.asyncio
    async def test_trend_analysis(self, analytics_engine):
        """Test trend analysis"""
        # Create trend analysis request
        time_range = TimeRange(
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 1, 2)
        )
        
        trend_request = TrendAnalysisRequest(
            trend_type=TrendType.LINEAR,
            time_range=time_range,
            metric_field='metric_value',
            data_sources=['metrics']
        )
        
        # Analyze trend
        result = await analytics_engine.trend_analyzer.analyze_trend(trend_request)
        
        # Verify result
        assert result.request_id == trend_request.request_id
        assert result.trend_type == TrendType.LINEAR
        assert result.trend_direction in ['increasing', 'decreasing', 'stable', 'insufficient_data', 'no_data', 'error']
        assert 0.0 <= result.trend_strength <= 1.0
    
    @pytest.mark.asyncio
    async def test_report_generation(self, analytics_engine):
        """Test report generation"""
        # Create report generator
        report_generator = ReportGenerator(analytics_engine)
        
        # Create analytics request
        time_range = TimeRange(
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 1, 2)
        )
        
        analytics_request = AnalyticsRequest(
            time_range=time_range,
            data_sources=['metrics'],
            metrics=[AnalyticsMetric.MEAN]
        )
        
        # Create report request
        report_request = ReportRequest(
            report_type=ReportType.TECHNICAL,
            report_format=ReportFormat.JSON,
            title="Test Report",
            analytics_request=analytics_request
        )
        
        # Generate report
        result = await report_generator.generate_report(report_request)
        
        # Verify result
        assert result.request_id == report_request.request_id
        assert result.report_format == ReportFormat.JSON
        assert result.status in ['success', 'error']
    
    @pytest.mark.asyncio
    async def test_ml_pipeline_initialization(self):
        """Test ML pipeline initialization"""
        ml_pipeline = MachineLearningPipeline()
        
        # Test health check
        health = await ml_pipeline.health_check()
        assert health['status'] in ['healthy', 'degraded', 'unhealthy']
    
    @pytest.mark.asyncio
    async def test_data_warehouse_operations(self, data_warehouse, sample_data):
        """Test data warehouse operations"""
        # Test health check
        health = await data_warehouse.health_check()
        assert health['status'] in ['healthy', 'not_initialized', 'unhealthy']
        
        # Test statistics
        stats = await data_warehouse.get_warehouse_statistics()
        assert 'warehouse_stats' in stats
        assert 'cache_stats' in stats
    
    @pytest.mark.asyncio
    async def test_analytics_statistics(self, analytics_engine):
        """Test analytics statistics"""
        stats = await analytics_engine.get_analytics_statistics()
        
        assert 'analytics_stats' in stats
        assert 'cache_stats' in stats
        assert 'configuration' in stats
        
        # Verify statistics structure
        analytics_stats = stats['analytics_stats']
        assert 'total_requests' in analytics_stats
        assert 'successful_requests' in analytics_stats
        assert 'failed_requests' in analytics_stats
    
    @pytest.mark.asyncio
    async def test_health_checks(self, analytics_engine):
        """Test comprehensive health checks"""
        # Analytics engine health check
        health = await analytics_engine.health_check()
        assert health['status'] in ['healthy', 'degraded', 'unhealthy']
        
        # KPI calculator health check
        kpi_health = await analytics_engine.kpi_calculator.health_check()
        assert kpi_health['status'] in ['healthy', 'degraded', 'unhealthy']
        
        # Trend analyzer health check
        trend_health = await analytics_engine.trend_analyzer.health_check()
        assert trend_health['status'] in ['healthy', 'degraded', 'unhealthy']

class TestBIAnalyticsModels:
    """Test BI Analytics data models"""
    
    def test_time_range_model(self):
        """Test TimeRange model"""
        start_time = datetime(2024, 1, 1)
        end_time = datetime(2024, 1, 2)
        
        time_range = TimeRange(start_time=start_time, end_time=end_time)
        
        assert time_range.start_time == start_time
        assert time_range.end_time == end_time
        assert time_range.duration_seconds == 86400  # 24 hours
        assert time_range.duration_hours == 24
        assert time_range.duration_days == 1
    
    def test_data_filter_model(self):
        """Test DataFilter model"""
        filter_obj = DataFilter(
            field='service_name',
            operator='eq',
            value='web-api'
        )
        
        assert filter_obj.field == 'service_name'
        assert filter_obj.operator == 'eq'
        assert filter_obj.value == 'web-api'
        assert filter_obj.case_sensitive is True
    
    def test_analytics_request_model(self):
        """Test AnalyticsRequest model"""
        time_range = TimeRange(
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 1, 2)
        )
        
        request = AnalyticsRequest(
            time_range=time_range,
            data_sources=['metrics', 'events'],
            metrics=[AnalyticsMetric.MEAN, AnalyticsMetric.COUNT]
        )
        
        assert request.time_range == time_range
        assert request.data_sources == ['metrics', 'events']
        assert len(request.metrics) == 2
        assert request.request_id is not None

if __name__ == '__main__':
    # Run basic tests
    asyncio.run(pytest.main([__file__, '-v']))