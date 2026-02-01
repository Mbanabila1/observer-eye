import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from .models import (
    NotificationChannel, AlertRule, Alert, NotificationDelivery,
    NotificationTemplate, AlertRuleNotificationChannel
)
from .services import NotificationService, AlertEvaluationService

User = get_user_model()


class NotificationModelTests(TestCase):
    """Test notification models"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123456'
        )
    
    def test_notification_channel_creation(self):
        """Test creating a notification channel"""
        channel = NotificationChannel.objects.create(
            name='Test Email Channel',
            channel_type='email',
            configuration={'recipients': ['admin@example.com']},
            created_by=self.user
        )
        
        self.assertEqual(channel.name, 'Test Email Channel')
        self.assertEqual(channel.channel_type, 'email')
        self.assertTrue(channel.is_enabled)
        self.assertEqual(channel.created_by, self.user)
    
    def test_notification_channel_validation(self):
        """Test notification channel configuration validation"""
        # Valid email configuration
        channel = NotificationChannel(
            name='Test Email',
            channel_type='email',
            configuration={'recipients': ['test@example.com']},
            created_by=self.user
        )
        channel.validate_configuration()  # Should not raise
        
        # Invalid email configuration
        channel.configuration = {'invalid': 'config'}
        with self.assertRaises(ValueError):
            channel.validate_configuration()
    
    def test_alert_rule_creation(self):
        """Test creating an alert rule"""
        rule = AlertRule.objects.create(
            name='Test Rule',
            description='Test alert rule',
            conditions={'rules': [{'field': 'cpu_usage', 'operator': 'gt', 'value': 80}]},
            severity='high',
            created_by=self.user
        )
        
        self.assertEqual(rule.name, 'Test Rule')
        self.assertEqual(rule.severity, 'high')
        self.assertTrue(rule.is_enabled)
    
    def test_alert_rule_evaluation(self):
        """Test alert rule condition evaluation"""
        rule = AlertRule.objects.create(
            name='CPU Alert',
            conditions={'rules': [{'field': 'cpu_usage', 'operator': 'gt', 'value': 80}]},
            created_by=self.user
        )
        
        # Test data that should trigger the alert
        trigger_data = {'cpu_usage': 85}
        self.assertTrue(rule.evaluate_conditions(trigger_data))
        
        # Test data that should not trigger the alert
        normal_data = {'cpu_usage': 70}
        self.assertFalse(rule.evaluate_conditions(normal_data))
    
    def test_alert_creation_and_lifecycle(self):
        """Test alert creation and lifecycle methods"""
        rule = AlertRule.objects.create(
            name='Test Rule',
            conditions={'rules': []},
            created_by=self.user
        )
        
        alert = Alert.objects.create(
            rule=rule,
            fingerprint='test-fingerprint',
            title='Test Alert',
            message='Test alert message',
            metadata={'test': 'data'}
        )
        
        self.assertEqual(alert.status, 'triggered')
        self.assertIsNone(alert.acknowledged_by)
        
        # Test acknowledgment
        alert.acknowledge(self.user)
        self.assertEqual(alert.status, 'acknowledged')
        self.assertEqual(alert.acknowledged_by, self.user)
        self.assertIsNotNone(alert.acknowledged_at)
        
        # Test resolution
        alert.resolve(self.user)
        self.assertEqual(alert.status, 'resolved')
        self.assertEqual(alert.resolved_by, self.user)
        self.assertIsNotNone(alert.resolved_at)


class NotificationServiceTests(TestCase):
    """Test notification service functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123456'
        )
        
        self.channel = NotificationChannel.objects.create(
            name='Test Email Channel',
            channel_type='email',
            configuration={'recipients': ['admin@example.com']},
            created_by=self.user
        )
        
        self.rule = AlertRule.objects.create(
            name='Test Rule',
            conditions={'rules': [{'field': 'cpu_usage', 'operator': 'gt', 'value': 80}]},
            severity='high',
            created_by=self.user
        )
        
        # Link rule to channel
        AlertRuleNotificationChannel.objects.create(
            alert_rule=self.rule,
            notification_channel=self.channel
        )
        
        self.service = NotificationService()
    
    def test_alert_creation_with_deduplication(self):
        """Test alert creation with deduplication"""
        data = {'cpu_usage': 85, 'host': 'server1'}
        
        # Create first alert
        alert1 = self.service.create_alert(
            self.rule, data, 'High CPU Usage', 'CPU usage is 85%'
        )
        self.assertIsNotNone(alert1)
        
        # Create second alert with same data (should be deduplicated)
        alert2 = self.service.create_alert(
            self.rule, data, 'High CPU Usage', 'CPU usage is 85%'
        )
        
        # Should return the same alert due to deduplication
        self.assertEqual(alert1.id, alert2.id)
    
    def test_fingerprint_generation(self):
        """Test alert fingerprint generation"""
        data1 = {'cpu_usage': 85, 'host': 'server1'}
        data2 = {'cpu_usage': 90, 'host': 'server1'}  # Different CPU but same host
        data3 = {'cpu_usage': 85, 'host': 'server2'}  # Same CPU but different host
        
        # Set deduplication fields to include host
        self.rule.deduplication_fields = ['host']
        self.rule.save()
        
        fingerprint1 = self.service._generate_fingerprint(self.rule, data1)
        fingerprint2 = self.service._generate_fingerprint(self.rule, data2)
        fingerprint3 = self.service._generate_fingerprint(self.rule, data3)
        
        # Same host should generate same fingerprint
        self.assertEqual(fingerprint1, fingerprint2)
        # Different host should generate different fingerprint
        self.assertNotEqual(fingerprint1, fingerprint3)


class AlertEvaluationServiceTests(TestCase):
    """Test alert evaluation service"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123456'
        )
        
        self.channel = NotificationChannel.objects.create(
            name='Test Channel',
            channel_type='email',
            configuration={'recipients': ['admin@example.com']},
            created_by=self.user
        )
        
        self.rule = AlertRule.objects.create(
            name='CPU Alert',
            conditions={'rules': [{'field': 'cpu_usage', 'operator': 'gt', 'value': 80}]},
            severity='high',
            is_enabled=True,
            created_by=self.user
        )
        
        AlertRuleNotificationChannel.objects.create(
            alert_rule=self.rule,
            notification_channel=self.channel
        )
        
        self.evaluation_service = AlertEvaluationService()
    
    def test_rule_evaluation(self):
        """Test evaluating rules against data"""
        # Data that should trigger alert
        trigger_data = {'cpu_usage': 85, 'memory_usage': 60}
        alerts = self.evaluation_service.evaluate_rules(trigger_data)
        
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].rule, self.rule)
        self.assertEqual(alerts[0].status, 'triggered')
        
        # Data that should not trigger alert
        normal_data = {'cpu_usage': 70, 'memory_usage': 60}
        alerts = self.evaluation_service.evaluate_rules(normal_data)
        
        self.assertEqual(len(alerts), 0)
    
    def test_single_rule_evaluation(self):
        """Test evaluating a single rule"""
        trigger_data = {'cpu_usage': 85}
        
        alert = self.evaluation_service.evaluate_single_rule(str(self.rule.id), trigger_data)
        self.assertIsNotNone(alert)
        self.assertEqual(alert.rule, self.rule)
        
        normal_data = {'cpu_usage': 70}
        alert = self.evaluation_service.evaluate_single_rule(str(self.rule.id), normal_data)
        self.assertIsNone(alert)


class NotificationAPITests(TestCase):
    """Test notification API endpoints"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123456'
        )
        self.client.force_login(self.user)
    
    def test_create_notification_channel(self):
        """Test creating notification channel via API"""
        data = {
            'name': 'Test API Channel',
            'channel_type': 'email',
            'configuration': {'recipients': ['test@example.com']},
            'is_enabled': True
        }
        
        response = self.client.post(
            reverse('notification:channels'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['name'], 'Test API Channel')
        self.assertEqual(response_data['channel_type'], 'email')
    
    def test_list_notification_channels(self):
        """Test listing notification channels via API"""
        # Create a test channel
        NotificationChannel.objects.create(
            name='Test Channel',
            channel_type='email',
            configuration={'recipients': ['test@example.com']},
            created_by=self.user
        )
        
        response = self.client.get(reverse('notification:channels'))
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.content)
        self.assertIn('channels', response_data)
        self.assertEqual(len(response_data['channels']), 1)
        self.assertEqual(response_data['channels'][0]['name'], 'Test Channel')
    
    def test_create_alert_rule(self):
        """Test creating alert rule via API"""
        data = {
            'name': 'API Test Rule',
            'description': 'Test rule created via API',
            'conditions': {'rules': [{'field': 'cpu_usage', 'operator': 'gt', 'value': 80}]},
            'severity': 'high',
            'is_enabled': True
        }
        
        response = self.client.post(
            reverse('notification:alert_rules'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['name'], 'API Test Rule')
        self.assertEqual(response_data['severity'], 'high')
    
    def test_alert_evaluation_endpoint(self):
        """Test alert evaluation endpoint"""
        # Create rule and channel
        rule = AlertRule.objects.create(
            name='Test Rule',
            conditions={'rules': [{'field': 'cpu_usage', 'operator': 'gt', 'value': 80}]},
            severity='high',
            is_enabled=True,
            created_by=self.user
        )
        
        channel = NotificationChannel.objects.create(
            name='Test Channel',
            channel_type='email',
            configuration={'recipients': ['test@example.com']},
            created_by=self.user
        )
        
        AlertRuleNotificationChannel.objects.create(
            alert_rule=rule,
            notification_channel=channel
        )
        
        # Test data that should trigger alert
        data = {'cpu_usage': 85, 'host': 'server1'}
        
        response = self.client.post(
            reverse('notification:evaluate_alerts'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertIn('triggered_alerts', response_data)
        self.assertEqual(len(response_data['triggered_alerts']), 1)
    
    def test_health_check_endpoint(self):
        """Test health check endpoint"""
        response = self.client.get(reverse('notification:health_check'))
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'healthy')
        self.assertIn('metrics', response_data)
