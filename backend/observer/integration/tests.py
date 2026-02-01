import json
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, Mock

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import (
    ExternalSystem, DataConnector, DataImportExportJob, 
    IntegrationEndpoint, IntegrationLog, ServiceDiscovery
)

User = get_user_model()


class ExternalSystemModelTest(TestCase):
    """Test cases for ExternalSystem model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser'
        )
    
    def test_external_system_creation(self):
        """Test creating an external system."""
        system = ExternalSystem.objects.create(
            name='Test API',
            description='Test external API system',
            system_type='api',
            base_url='https://api.example.com',
            version='v1.0',
            auth_type='api_key',
            auth_config={'api_key': 'test-key'},
            created_by=self.user
        )
        
        self.assertEqual(system.name, 'Test API')
        self.assertEqual(system.system_type, 'api')
        self.assertEqual(system.auth_type, 'api_key')
        self.assertTrue(system.is_active)
        self.assertTrue(system.is_healthy)
        self.assertEqual(system.created_by, self.user)
    
    def test_external_system_str_representation(self):
        """Test string representation of external system."""
        system = ExternalSystem.objects.create(
            name='Test System',
            system_type='database',
            created_by=self.user
        )
        
        expected = 'Test System (Database)'
        self.assertEqual(str(system), expected)
    
    def test_external_system_soft_delete(self):
        """Test soft delete functionality."""
        system = ExternalSystem.objects.create(
            name='Test System',
            system_type='api',
            created_by=self.user
        )
        
        self.assertTrue(system.is_active)
        system.soft_delete()
        self.assertFalse(system.is_active)
        
        # Test restore
        system.restore()
        self.assertTrue(system.is_active)


class DataConnectorModelTest(TestCase):
    """Test cases for DataConnector model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser'
        )
        self.external_system = ExternalSystem.objects.create(
            name='Test System',
            system_type='api',
            created_by=self.user
        )
    
    def test_data_connector_creation(self):
        """Test creating a data connector."""
        connector = DataConnector.objects.create(
            external_system=self.external_system,
            name='Test Connector',
            description='Test data connector',
            connector_type='pull',
            data_format='json',
            source_endpoint='/api/data',
            sync_frequency='hourly',
            batch_size=500
        )
        
        self.assertEqual(connector.name, 'Test Connector')
        self.assertEqual(connector.connector_type, 'pull')
        self.assertEqual(connector.data_format, 'json')
        self.assertEqual(connector.batch_size, 500)
        self.assertTrue(connector.is_enabled)
        self.assertEqual(connector.external_system, self.external_system)
    
    def test_data_connector_str_representation(self):
        """Test string representation of data connector."""
        connector = DataConnector.objects.create(
            external_system=self.external_system,
            name='Test Connector',
            connector_type='pull'
        )
        
        expected = f'{self.external_system.name} - Test Connector'
        self.assertEqual(str(connector), expected)


class DataImportExportJobModelTest(TestCase):
    """Test cases for DataImportExportJob model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser'
        )
        self.external_system = ExternalSystem.objects.create(
            name='Test System',
            system_type='api',
            created_by=self.user
        )
        self.connector = DataConnector.objects.create(
            external_system=self.external_system,
            name='Test Connector',
            connector_type='pull'
        )
    
    def test_job_creation(self):
        """Test creating a data import/export job."""
        job = DataImportExportJob.objects.create(
            connector=self.connector,
            job_type='import',
            status='pending',
            job_config={'batch_size': 1000},
            parameters={'start_date': '2024-01-01'},
            triggered_by=self.user
        )
        
        self.assertEqual(job.job_type, 'import')
        self.assertEqual(job.status, 'pending')
        self.assertEqual(job.connector, self.connector)
        self.assertEqual(job.triggered_by, self.user)
        self.assertEqual(job.retry_count, 0)
        self.assertEqual(job.max_retries, 3)
    
    def test_job_str_representation(self):
        """Test string representation of job."""
        job = DataImportExportJob.objects.create(
            connector=self.connector,
            job_type='export',
            status='running'
        )
        
        expected = f'Data Export - {self.connector.name} (running)'
        self.assertEqual(str(job), expected)


class IntegrationEndpointModelTest(TestCase):
    """Test cases for IntegrationEndpoint model."""
    
    def test_endpoint_creation(self):
        """Test creating an integration endpoint."""
        endpoint = IntegrationEndpoint.objects.create(
            name='Webhook Receiver',
            description='Receives webhook data',
            endpoint_type='webhook',
            path='/api/v1/webhooks/data',
            http_methods=['POST'],
            version='v1',
            requires_authentication=True,
            rate_limit_per_minute=100
        )
        
        self.assertEqual(endpoint.name, 'Webhook Receiver')
        self.assertEqual(endpoint.endpoint_type, 'webhook')
        self.assertEqual(endpoint.version, 'v1')
        self.assertTrue(endpoint.requires_authentication)
        self.assertTrue(endpoint.is_enabled)
        self.assertFalse(endpoint.is_deprecated)
    
    def test_endpoint_str_representation(self):
        """Test string representation of endpoint."""
        endpoint = IntegrationEndpoint.objects.create(
            name='Test Endpoint',
            endpoint_type='api',
            path='/api/test',
            version='v2'
        )
        
        expected = 'Test Endpoint (v2)'
        self.assertEqual(str(endpoint), expected)


class ServiceDiscoveryModelTest(TestCase):
    """Test cases for ServiceDiscovery model."""
    
    def test_service_discovery_creation(self):
        """Test creating a service discovery entry."""
        service = ServiceDiscovery.objects.create(
            service_name='observer-api',
            service_type='logic',
            instance_id='api-001',
            host='localhost',
            port=8400,
            protocol='http',
            version='1.0.0',
            environment='development',
            weight=100,
            max_connections=1000
        )
        
        self.assertEqual(service.service_name, 'observer-api')
        self.assertEqual(service.service_type, 'logic')
        self.assertEqual(service.instance_id, 'api-001')
        self.assertEqual(service.host, 'localhost')
        self.assertEqual(service.port, 8400)
        self.assertEqual(service.health_status, 'unknown')
    
    def test_service_full_url_property(self):
        """Test the full_url property."""
        service = ServiceDiscovery.objects.create(
            service_name='test-service',
            service_type='data',
            instance_id='test-001',
            host='api.example.com',
            port=443,
            protocol='https',
            base_path='/api/v1/',
            version='1.0.0'
        )
        
        expected_url = 'https://api.example.com:443/api/v1/'
        self.assertEqual(service.full_url, expected_url)
    
    def test_service_str_representation(self):
        """Test string representation of service."""
        service = ServiceDiscovery.objects.create(
            service_name='test-service',
            service_type='data',
            instance_id='test-001',
            host='localhost',
            port=8000,
            version='1.0.0',
            health_status='healthy'
        )
        
        expected = 'test-service:test-001 (healthy)'
        self.assertEqual(str(service), expected)


class IntegrationLogModelTest(TestCase):
    """Test cases for IntegrationLog model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser'
        )
        self.external_system = ExternalSystem.objects.create(
            name='Test System',
            system_type='api',
            created_by=self.user
        )
    
    def test_integration_log_creation(self):
        """Test creating an integration log entry."""
        log = IntegrationLog.objects.create(
            external_system=self.external_system,
            level='INFO',
            activity_type='connection',
            message='Successfully connected to external system',
            details={'response_time': 150, 'status_code': 200},
            request_id='req-123',
            ip_address='192.168.1.1',
            duration_ms=150
        )
        
        self.assertEqual(log.level, 'INFO')
        self.assertEqual(log.activity_type, 'connection')
        self.assertEqual(log.external_system, self.external_system)
        self.assertEqual(log.request_id, 'req-123')
        self.assertEqual(log.duration_ms, 150)
    
    def test_log_str_representation(self):
        """Test string representation of log."""
        log = IntegrationLog.objects.create(
            external_system=self.external_system,
            level='ERROR',
            activity_type='error',
            message='This is a very long error message that should be truncated in the string representation'
        )
        
        expected = 'ERROR - error: This is a very long error message that should be t...'
        self.assertEqual(str(log), expected)


class IntegrationViewsTest(TestCase):
    """Test cases for integration views."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser'
        )
        self.external_system = ExternalSystem.objects.create(
            name='Test System',
            system_type='api',
            base_url='https://api.example.com',
            created_by=self.user
        )
    
    def test_health_check_endpoint(self):
        """Test the health check endpoint."""
        url = reverse('integration:health_check')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'integration')
        self.assertEqual(data['version'], 'v1')
        self.assertIn('timestamp', data)
    
    def test_integration_stats_endpoint(self):
        """Test the integration stats endpoint."""
        url = reverse('integration:integration_stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('stats', data)
        self.assertIn('external_systems', data['stats'])
        self.assertIn('data_connectors', data['stats'])
        self.assertIn('jobs', data['stats'])
        self.assertIn('service_discovery', data['stats'])
    
    def test_external_systems_list_endpoint(self):
        """Test listing external systems."""
        url = reverse('integration:external_systems_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('results', data)
        self.assertIn('pagination', data)
        self.assertEqual(len(data['results']), 1)
    
    def test_external_system_detail_endpoint(self):
        """Test getting external system details."""
        url = reverse('integration:external_system_detail', kwargs={'system_id': str(self.external_system.id)})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['name'], 'Test System')
        self.assertEqual(data['system_type'], 'api')
        self.assertEqual(data['base_url'], 'https://api.example.com')
    
    def test_external_system_creation(self):
        """Test creating an external system via API."""
        url = reverse('integration:external_systems_list')
        data = {
            'name': 'New Test System',
            'system_type': 'database',
            'description': 'A new test system',
            'base_url': 'https://db.example.com',
            'auth_type': 'basic_auth',
            'timeout_seconds': 60
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.content)
        self.assertIn('id', response_data)
        self.assertEqual(response_data['message'], 'External system created successfully')
        
        # Verify the system was created
        system = ExternalSystem.objects.get(name='New Test System')
        self.assertEqual(system.system_type, 'database')
        self.assertEqual(system.timeout_seconds, 60)
    
    def test_service_discovery_registration(self):
        """Test service registration via API."""
        url = reverse('integration:service_discovery_list')
        data = {
            'service_name': 'test-service',
            'service_type': 'logic',
            'instance_id': 'test-001',
            'host': 'localhost',
            'port': 8400,
            'version': '1.0.0',
            'environment': 'test'
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.content)
        self.assertIn('Service instance registered successfully', response_data['message'])
        
        # Verify the service was registered
        service = ServiceDiscovery.objects.get(instance_id='test-001')
        self.assertEqual(service.service_name, 'test-service')
        self.assertEqual(service.host, 'localhost')
        self.assertEqual(service.port, 8400)


class IntegrationAPIVersioningTest(TestCase):
    """Test cases for API versioning and backward compatibility."""
    
    def setUp(self):
        self.client = Client()
        self.endpoint_v1 = IntegrationEndpoint.objects.create(
            name='Test Endpoint V1',
            endpoint_type='api',
            path='/api/v1/test',
            version='v1',
            http_methods=['GET', 'POST']
        )
        self.endpoint_v2 = IntegrationEndpoint.objects.create(
            name='Test Endpoint V2',
            endpoint_type='api',
            path='/api/v2/test',
            version='v2',
            http_methods=['GET', 'POST', 'PUT']
        )
    
    def test_endpoint_versioning(self):
        """Test that endpoints support versioning."""
        # Test v1 endpoint
        url = reverse('integration:integration_endpoint_detail', kwargs={'endpoint_id': str(self.endpoint_v1.id)})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['version'], 'v1')
        self.assertEqual(len(data['http_methods']), 2)
        
        # Test v2 endpoint
        url = reverse('integration:integration_endpoint_detail', kwargs={'endpoint_id': str(self.endpoint_v2.id)})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['version'], 'v2')
        self.assertEqual(len(data['http_methods']), 3)
    
    def test_endpoint_deprecation(self):
        """Test endpoint deprecation functionality."""
        # Mark v1 as deprecated
        self.endpoint_v1.is_deprecated = True
        self.endpoint_v1.deprecation_date = timezone.now()
        self.endpoint_v1.replacement_endpoint = self.endpoint_v2
        self.endpoint_v1.save()
        
        url = reverse('integration:integration_endpoint_detail', kwargs={'endpoint_id': str(self.endpoint_v1.id)})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['is_deprecated'])
        self.assertIsNotNone(data['deprecation_date'])
        self.assertEqual(data['replacement_endpoint_id'], str(self.endpoint_v2.id))


class IntegrationErrorHandlingTest(TestCase):
    """Test cases for error handling and resilience."""
    
    def setUp(self):
        self.client = Client()
    
    def test_invalid_system_id(self):
        """Test handling of invalid system ID."""
        invalid_id = str(uuid.uuid4())
        url = reverse('integration:external_system_detail', kwargs={'system_id': invalid_id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
    
    def test_invalid_json_data(self):
        """Test handling of invalid JSON data."""
        url = reverse('integration:external_systems_list')
        response = self.client.post(
            url,
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    def test_missing_required_fields(self):
        """Test handling of missing required fields."""
        url = reverse('integration:external_systems_list')
        data = {
            'description': 'Missing required name field'
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn('error', response_data)
