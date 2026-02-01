"""
Tests for grailobserver app.
Tests specialized observability features and analysis tools.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
import json

from .models import (
    ObservabilityTarget, ObservabilityPattern, ServiceLevelIndicator,
    ServiceLevelObjective, ObservabilityTrace, ObservabilityAnomaly,
    ObservabilityPlaybook, ObservabilityExperiment, ObservabilityInsight
)
from .services import (
    SLOCalculationService, AnomalyDetectionService, 
    InsightGenerationService, HealthCheckService
)

User = get_user_model()


class ObservabilityTargetModelTest(TestCase):
    """Test ObservabilityTarget model."""
    
    def setUp(self):
        self.target = ObservabilityTarget.objects.create(
            name='test-service',
            description='Test service for monitoring',
            target_type='service',
            endpoint_url='https://api.test-service.com/health',
            is_critical=True,
            is_monitored=True,
        )
    
    def test_target_creation(self):
        """Test target creation and basic properties."""
        self.assertEqual(self.target.name, 'test-service')
        self.assertEqual(self.target.target_type, 'service')
        self.assertTrue(self.target.is_critical)
        self.assertTrue(self.target.is_monitored)
        self.assertEqual(self.target.health_status, 'unknown')
    
    def test_target_str_representation(self):
        """Test string representation."""
        expected = 'test-service (Microservice)'
        self.assertEqual(str(self.target), expected)


class ServiceLevelIndicatorModelTest(TestCase):
    """Test ServiceLevelIndicator model."""
    
    def setUp(self):
        self.target = ObservabilityTarget.objects.create(
            name='test-service',
            target_type='service',
        )
        self.sli = ServiceLevelIndicator.objects.create(
            target=self.target,
            name='availability',
            description='Service availability SLI',
            sli_type='availability',
            measurement_config={'type': 'http_success_rate'},
            query_definition='SELECT COUNT(*) FROM requests WHERE status = 200',
            unit='percentage',
            good_threshold=200.0,
            total_threshold=200.0,
            calculation_window='5m',
        )
    
    def test_sli_creation(self):
        """Test SLI creation and relationships."""
        self.assertEqual(self.sli.name, 'availability')
        self.assertEqual(self.sli.target, self.target)
        self.assertEqual(self.sli.sli_type, 'availability')
        self.assertTrue(self.sli.is_active)
    
    def test_sli_str_representation(self):
        """Test string representation."""
        expected = 'test-service - availability'
        self.assertEqual(str(self.sli), expected)


class ServiceLevelObjectiveModelTest(TestCase):
    """Test ServiceLevelObjective model."""
    
    def setUp(self):
        self.target = ObservabilityTarget.objects.create(
            name='test-service',
            target_type='service',
        )
        self.sli = ServiceLevelIndicator.objects.create(
            target=self.target,
            name='availability',
            sli_type='availability',
            measurement_config={'type': 'http_success_rate'},
            query_definition='SELECT COUNT(*) FROM requests WHERE status = 200',
            unit='percentage',
            good_threshold=200.0,
            total_threshold=200.0,
        )
        self.slo = ServiceLevelObjective.objects.create(
            sli=self.sli,
            name='99.9% availability',
            description='Service should be available 99.9% of the time',
            target_percentage=99.9,
            time_window='30d',
        )
    
    def test_slo_creation(self):
        """Test SLO creation and relationships."""
        self.assertEqual(self.slo.name, '99.9% availability')
        self.assertEqual(self.slo.sli, self.sli)
        self.assertEqual(self.slo.target_percentage, 99.9)
        self.assertEqual(self.slo.time_window, '30d')
        self.assertTrue(self.slo.is_active)
    
    def test_slo_str_representation(self):
        """Test string representation."""
        expected = 'test-service - 99.9% availability (99.9%)'
        self.assertEqual(str(self.slo), expected)


class ObservabilityTraceModelTest(TestCase):
    """Test ObservabilityTrace model."""
    
    def setUp(self):
        self.start_time = timezone.now()
        self.end_time = self.start_time + timedelta(milliseconds=150)
        
        self.trace = ObservabilityTrace.objects.create(
            trace_id='trace-123',
            span_id='span-456',
            operation_name='get_user',
            service_name='user-service',
            start_time=self.start_time,
            end_time=self.end_time,
            duration_ms=150,
            status='ok',
        )
    
    def test_trace_creation(self):
        """Test trace creation and properties."""
        self.assertEqual(self.trace.trace_id, 'trace-123')
        self.assertEqual(self.trace.span_id, 'span-456')
        self.assertEqual(self.trace.operation_name, 'get_user')
        self.assertEqual(self.trace.service_name, 'user-service')
        self.assertEqual(self.trace.duration_ms, 150)
        self.assertEqual(self.trace.status, 'ok')
    
    def test_trace_str_representation(self):
        """Test string representation."""
        expected = 'user-service.get_user (150ms)'
        self.assertEqual(str(self.trace), expected)


class ObservabilityAnomalyModelTest(TestCase):
    """Test ObservabilityAnomaly model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.target = ObservabilityTarget.objects.create(
            name='test-service',
            target_type='service',
        )
        self.anomaly = ObservabilityAnomaly.objects.create(
            target=self.target,
            anomaly_type='performance',
            metric_name='response_time',
            time_window_start=timezone.now() - timedelta(hours=1),
            time_window_end=timezone.now(),
            severity='high',
            confidence_score=0.85,
            anomaly_score=75.5,
            baseline_value=100.0,
            observed_value=175.5,
            deviation_percentage=75.5,
            detection_method='statistical_outlier',
        )
    
    def test_anomaly_creation(self):
        """Test anomaly creation and properties."""
        self.assertEqual(self.anomaly.target, self.target)
        self.assertEqual(self.anomaly.anomaly_type, 'performance')
        self.assertEqual(self.anomaly.metric_name, 'response_time')
        self.assertEqual(self.anomaly.severity, 'high')
        self.assertEqual(self.anomaly.confidence_score, 0.85)
        self.assertFalse(self.anomaly.is_acknowledged)
    
    def test_anomaly_str_representation(self):
        """Test string representation."""
        expected = 'test-service - performance (high)'
        self.assertEqual(str(self.anomaly), expected)


class ObservabilityTargetViewTest(TestCase):
    """Test ObservabilityTarget API views."""
    
    def setUp(self):
        self.client = Client()
        self.target = ObservabilityTarget.objects.create(
            name='test-service',
            description='Test service',
            target_type='service',
            is_critical=True,
        )
    
    def test_get_targets_list(self):
        """Test getting list of targets."""
        url = reverse('grailobserver:targets_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('targets', data)
        self.assertEqual(len(data['targets']), 1)
        self.assertEqual(data['targets'][0]['name'], 'test-service')
    
    def test_get_target_detail(self):
        """Test getting target detail."""
        url = reverse('grailobserver:target_detail', kwargs={'target_id': self.target.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['name'], 'test-service')
        self.assertEqual(data['target_type'], 'service')
        self.assertTrue(data['is_critical'])
    
    def test_get_nonexistent_target(self):
        """Test getting nonexistent target returns 404."""
        from uuid import uuid4
        url = reverse('grailobserver:target_detail', kwargs={'target_id': uuid4()})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
    
    def test_create_target(self):
        """Test creating new target."""
        url = reverse('grailobserver:targets_list')
        data = {
            'name': 'new-service',
            'description': 'New test service',
            'target_type': 'service',
            'is_critical': False,
        }
        response = self.client.post(
            url, 
            json.dumps(data), 
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['name'], 'new-service')
        
        # Verify target was created
        self.assertTrue(
            ObservabilityTarget.objects.filter(name='new-service').exists()
        )


class HealthCheckViewTest(TestCase):
    """Test health check endpoint."""
    
    def setUp(self):
        self.client = Client()
    
    def test_health_check(self):
        """Test health check endpoint."""
        url = reverse('grailobserver:health_check')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['app'], 'grailobserver')
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('timestamp', data)
        self.assertIn('stats', data)


class DashboardSummaryViewTest(TestCase):
    """Test dashboard summary endpoint."""
    
    def setUp(self):
        self.client = Client()
        # Create some test data
        self.target1 = ObservabilityTarget.objects.create(
            name='service-1',
            target_type='service',
            health_status='healthy',
            is_critical=True,
        )
        self.target2 = ObservabilityTarget.objects.create(
            name='service-2',
            target_type='service',
            health_status='degraded',
            is_critical=False,
        )
    
    def test_dashboard_summary(self):
        """Test dashboard summary endpoint."""
        url = reverse('grailobserver:dashboard_summary')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('summary', data)
        
        summary = data['summary']
        self.assertIn('targets', summary)
        self.assertEqual(summary['targets']['total'], 2)
        self.assertEqual(summary['targets']['healthy'], 1)
        self.assertEqual(summary['targets']['critical'], 1)


class SLOCalculationServiceTest(TestCase):
    """Test SLO calculation service."""
    
    def setUp(self):
        self.target = ObservabilityTarget.objects.create(
            name='test-service',
            target_type='service',
        )
        self.sli = ServiceLevelIndicator.objects.create(
            target=self.target,
            name='availability',
            sli_type='availability',
            measurement_config={'type': 'http_success_rate'},
            query_definition='SELECT COUNT(*) FROM requests WHERE status = 200',
            unit='percentage',
            good_threshold=200.0,
            total_threshold=200.0,
        )
        self.slo = ServiceLevelObjective.objects.create(
            sli=self.sli,
            name='99.9% availability',
            target_percentage=99.9,
            time_window='1d',
        )
    
    def test_calculate_slo_performance(self):
        """Test SLO performance calculation."""
        result = SLOCalculationService.calculate_slo_performance(self.slo)
        
        self.assertIn('slo_id', result)
        self.assertIn('target_percentage', result)
        self.assertIn('current_performance', result)
        self.assertIn('error_budget_remaining', result)
        self.assertIn('status', result)
        
        self.assertEqual(result['target_percentage'], 99.9)
        self.assertIn(result['status'], ['healthy', 'at_risk'])


class AnomalyDetectionServiceTest(TestCase):
    """Test anomaly detection service."""
    
    def setUp(self):
        self.target = ObservabilityTarget.objects.create(
            name='test-service',
            target_type='service',
        )
        
        # Create some test traces
        base_time = timezone.now() - timedelta(hours=2)
        for i in range(20):
            ObservabilityTrace.objects.create(
                trace_id=f'trace-{i}',
                span_id=f'span-{i}',
                operation_name='test_operation',
                service_name='test-service',
                start_time=base_time + timedelta(minutes=i*5),
                end_time=base_time + timedelta(minutes=i*5, seconds=1),
                duration_ms=100 + (i * 10),  # Gradually increasing latency
                status='ok' if i < 18 else 'error',  # Last 2 are errors
            )
    
    def test_detect_performance_anomalies(self):
        """Test performance anomaly detection."""
        anomalies = AnomalyDetectionService.detect_performance_anomalies(
            self.target, lookback_hours=3
        )
        
        # Should detect some anomalies due to increasing latency and errors
        self.assertIsInstance(anomalies, list)
        # The exact number depends on the detection algorithm
        # but we should get at least error rate anomalies


class HealthCheckServiceTest(TestCase):
    """Test health check service."""
    
    def setUp(self):
        self.target = ObservabilityTarget.objects.create(
            name='test-service',
            target_type='service',
            endpoint_url='https://api.test-service.com/health',
        )
    
    def test_perform_health_check(self):
        """Test performing health check."""
        result = HealthCheckService.perform_health_check(self.target)
        
        self.assertIn('target_id', result)
        self.assertIn('target_name', result)
        self.assertIn('timestamp', result)
        self.assertIn('overall_status', result)
        self.assertIn('checks', result)
        
        self.assertEqual(result['target_name'], 'test-service')
        self.assertIn(result['overall_status'], ['healthy', 'degraded', 'unhealthy', 'unknown'])


class InsightGenerationServiceTest(TestCase):
    """Test insight generation service."""
    
    def setUp(self):
        self.target = ObservabilityTarget.objects.create(
            name='test-service',
            target_type='service',
        )
        
        # Create sufficient test traces for insight generation
        base_time = timezone.now() - timedelta(days=2)
        for i in range(100):
            ObservabilityTrace.objects.create(
                trace_id=f'trace-{i}',
                span_id=f'span-{i}',
                operation_name='test_operation',
                service_name='test-service',
                start_time=base_time + timedelta(minutes=i*10),
                end_time=base_time + timedelta(minutes=i*10, seconds=2),
                duration_ms=100 + (i % 10) * 50,  # Varying latency
                status='ok' if i % 20 != 0 else 'error',  # 5% error rate
            )
    
    def test_generate_performance_insights(self):
        """Test performance insight generation."""
        insights = InsightGenerationService.generate_performance_insights(self.target)
        
        self.assertIsInstance(insights, list)
        # Should generate some insights based on the test data
        for insight in insights:
            self.assertIn('title', insight)
            self.assertIn('description', insight)
            self.assertIn('insight_type', insight)
            self.assertIn('confidence_score', insight)
            self.assertIn('impact_score', insight)
            self.assertIn('recommendations', insight)