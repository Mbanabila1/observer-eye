import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from django.http import JsonResponse, HttpRequest, Http404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404

from .models import (
    ExternalSystem, DataConnector, DataImportExportJob, 
    IntegrationEndpoint, IntegrationLog, ServiceDiscovery
)
from core.models import User

logger = logging.getLogger(__name__)


class BaseIntegrationView(View):
    """Base view class for integration endpoints with common functionality."""
    
    def dispatch(self, request, *args, **kwargs):
        """Add common request processing and error handling."""
        try:
            return super().dispatch(request, *args, **kwargs)
        except Http404:
            # Re-raise Http404 to return proper 404 status
            raise
        except ValidationError as e:
            # Handle validation errors with 400 status
            return JsonResponse({
                'error': 'Validation error',
                'message': str(e)
            }, status=400)
        except Exception as e:
            logger.error(f"Integration API error: {str(e)}", exc_info=True)
            return JsonResponse({
                'error': 'Internal server error',
                'message': str(e)
            }, status=500)
    
    def get_json_data(self, request: HttpRequest) -> Dict[str, Any]:
        """Parse JSON data from request body."""
        try:
            return json.loads(request.body) if request.body else {}
        except json.JSONDecodeError:
            raise ValidationError("Invalid JSON data")
    
    def paginate_queryset(self, queryset, request: HttpRequest, page_size: int = 20):
        """Paginate queryset and return paginated data."""
        page = request.GET.get('page', 1)
        paginator = Paginator(queryset.order_by('-created_at'), page_size)  # Add ordering to avoid warnings
        page_obj = paginator.get_page(page)
        
        return {
            'results': list(page_obj.object_list.values()),
            'pagination': {
                'page': page_obj.number,
                'pages': paginator.num_pages,
                'per_page': page_size,
                'total': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            }
        }


@method_decorator(csrf_exempt, name='dispatch')
class ExternalSystemView(BaseIntegrationView):
    """API endpoints for managing external systems."""
    
    def get(self, request: HttpRequest, system_id: Optional[str] = None):
        """Get external systems or specific system details."""
        if system_id:
            system = get_object_or_404(ExternalSystem, id=system_id, is_active=True)
            return JsonResponse({
                'id': str(system.id),
                'name': system.name,
                'description': system.description,
                'system_type': system.system_type,
                'base_url': system.base_url,
                'version': system.version,
                'auth_type': system.auth_type,
                'timeout_seconds': system.timeout_seconds,
                'retry_attempts': system.retry_attempts,
                'retry_delay_seconds': system.retry_delay_seconds,
                'health_check_url': system.health_check_url,
                'health_check_interval_minutes': system.health_check_interval_minutes,
                'last_health_check': system.last_health_check.isoformat() if system.last_health_check else None,
                'is_healthy': system.is_healthy,
                'metadata': system.metadata,
                'configuration': system.configuration,
                'created_at': system.created_at.isoformat(),
                'updated_at': system.updated_at.isoformat(),
            })
        
        # List external systems with filtering
        queryset = ExternalSystem.objects.filter(is_active=True)
        
        # Apply filters
        system_type = request.GET.get('system_type')
        if system_type:
            queryset = queryset.filter(system_type=system_type)
        
        is_healthy = request.GET.get('is_healthy')
        if is_healthy is not None:
            queryset = queryset.filter(is_healthy=is_healthy.lower() == 'true')
        
        search = request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(description__icontains=search)
            )
        
        return JsonResponse(self.paginate_queryset(queryset, request))
    
    def post(self, request: HttpRequest):
        """Create a new external system."""
        data = self.get_json_data(request)
        
        try:
            with transaction.atomic():
                system = ExternalSystem.objects.create(
                    name=data['name'],
                    description=data.get('description', ''),
                    system_type=data['system_type'],
                    base_url=data.get('base_url'),
                    version=data.get('version', ''),
                    auth_type=data.get('auth_type', 'none'),
                    auth_config=data.get('auth_config', {}),
                    timeout_seconds=data.get('timeout_seconds', 30),
                    retry_attempts=data.get('retry_attempts', 3),
                    retry_delay_seconds=data.get('retry_delay_seconds', 5),
                    health_check_url=data.get('health_check_url'),
                    health_check_interval_minutes=data.get('health_check_interval_minutes', 5),
                    metadata=data.get('metadata', {}),
                    configuration=data.get('configuration', {}),
                    created_by_id=request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None,
                )
                
                # Log the creation
                IntegrationLog.objects.create(
                    external_system=system,
                    level='INFO',
                    activity_type='system',
                    message=f'External system "{system.name}" created',
                    details={'system_id': str(system.id), 'system_type': system.system_type}
                )
                
                return JsonResponse({
                    'id': str(system.id),
                    'message': 'External system created successfully'
                }, status=201)
                
        except Exception as e:
            return JsonResponse({
                'error': 'Failed to create external system',
                'message': str(e)
            }, status=400)
    
    def put(self, request: HttpRequest, system_id: str):
        """Update an external system."""
        system = get_object_or_404(ExternalSystem, id=system_id, is_active=True)
        data = self.get_json_data(request)
        
        try:
            with transaction.atomic():
                # Update fields
                for field in ['name', 'description', 'system_type', 'base_url', 'version', 
                             'auth_type', 'auth_config', 'timeout_seconds', 'retry_attempts',
                             'retry_delay_seconds', 'health_check_url', 'health_check_interval_minutes',
                             'metadata', 'configuration']:
                    if field in data:
                        setattr(system, field, data[field])
                
                system.last_modified_by_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None
                system.save()
                
                # Log the update
                IntegrationLog.objects.create(
                    external_system=system,
                    level='INFO',
                    activity_type='system',
                    message=f'External system "{system.name}" updated',
                    details={'system_id': str(system.id), 'updated_fields': list(data.keys())}
                )
                
                return JsonResponse({'message': 'External system updated successfully'})
                
        except Exception as e:
            return JsonResponse({
                'error': 'Failed to update external system',
                'message': str(e)
            }, status=400)
    
    def delete(self, request: HttpRequest, system_id: str):
        """Soft delete an external system."""
        system = get_object_or_404(ExternalSystem, id=system_id, is_active=True)
        
        try:
            with transaction.atomic():
                system.soft_delete()
                
                # Log the deletion
                IntegrationLog.objects.create(
                    external_system=system,
                    level='INFO',
                    activity_type='system',
                    message=f'External system "{system.name}" deleted',
                    details={'system_id': str(system.id)}
                )
                
                return JsonResponse({'message': 'External system deleted successfully'})
                
        except Exception as e:
            return JsonResponse({
                'error': 'Failed to delete external system',
                'message': str(e)
            }, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class DataConnectorView(BaseIntegrationView):
    """API endpoints for managing data connectors."""
    
    def get(self, request: HttpRequest, connector_id: Optional[str] = None):
        """Get data connectors or specific connector details."""
        if connector_id:
            connector = get_object_or_404(DataConnector, id=connector_id, is_active=True)
            return JsonResponse({
                'id': str(connector.id),
                'external_system_id': str(connector.external_system.id),
                'external_system_name': connector.external_system.name,
                'name': connector.name,
                'description': connector.description,
                'connector_type': connector.connector_type,
                'data_format': connector.data_format,
                'source_endpoint': connector.source_endpoint,
                'destination_endpoint': connector.destination_endpoint,
                'sync_frequency': connector.sync_frequency,
                'sync_schedule': connector.sync_schedule,
                'transformation_rules': connector.transformation_rules,
                'validation_rules': connector.validation_rules,
                'filters': connector.filters,
                'batch_size': connector.batch_size,
                'is_enabled': connector.is_enabled,
                'last_sync': connector.last_sync.isoformat() if connector.last_sync else None,
                'last_sync_status': connector.last_sync_status,
                'last_sync_message': connector.last_sync_message,
                'total_records_processed': connector.total_records_processed,
                'total_errors': connector.total_errors,
                'created_at': connector.created_at.isoformat(),
                'updated_at': connector.updated_at.isoformat(),
            })
        
        # List data connectors with filtering
        queryset = DataConnector.objects.filter(is_active=True).select_related('external_system')
        
        # Apply filters
        system_id = request.GET.get('system_id')
        if system_id:
            queryset = queryset.filter(external_system_id=system_id)
        
        connector_type = request.GET.get('connector_type')
        if connector_type:
            queryset = queryset.filter(connector_type=connector_type)
        
        is_enabled = request.GET.get('is_enabled')
        if is_enabled is not None:
            queryset = queryset.filter(is_enabled=is_enabled.lower() == 'true')
        
        return JsonResponse(self.paginate_queryset(queryset, request))
    
    def post(self, request: HttpRequest):
        """Create a new data connector."""
        data = self.get_json_data(request)
        
        try:
            with transaction.atomic():
                external_system = get_object_or_404(ExternalSystem, id=data['external_system_id'], is_active=True)
                
                connector = DataConnector.objects.create(
                    external_system=external_system,
                    name=data['name'],
                    description=data.get('description', ''),
                    connector_type=data['connector_type'],
                    data_format=data.get('data_format', 'json'),
                    source_endpoint=data.get('source_endpoint', ''),
                    destination_endpoint=data.get('destination_endpoint', ''),
                    sync_frequency=data.get('sync_frequency', 'manual'),
                    sync_schedule=data.get('sync_schedule', {}),
                    transformation_rules=data.get('transformation_rules', []),
                    validation_rules=data.get('validation_rules', []),
                    filters=data.get('filters', {}),
                    batch_size=data.get('batch_size', 1000),
                    is_enabled=data.get('is_enabled', True),
                )
                
                # Log the creation
                IntegrationLog.objects.create(
                    external_system=external_system,
                    connector=connector,
                    level='INFO',
                    activity_type='system',
                    message=f'Data connector "{connector.name}" created',
                    details={'connector_id': str(connector.id), 'connector_type': connector.connector_type}
                )
                
                return JsonResponse({
                    'id': str(connector.id),
                    'message': 'Data connector created successfully'
                }, status=201)
                
        except Exception as e:
            return JsonResponse({
                'error': 'Failed to create data connector',
                'message': str(e)
            }, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class DataImportExportView(BaseIntegrationView):
    """API endpoints for data import/export operations."""
    
    def post(self, request: HttpRequest, action: str):
        """Trigger data import, export, or sync operations."""
        data = self.get_json_data(request)
        connector_id = data.get('connector_id')
        
        if not connector_id:
            return JsonResponse({'error': 'connector_id is required'}, status=400)
        
        connector = get_object_or_404(DataConnector, id=connector_id, is_active=True, is_enabled=True)
        
        # Validate action against connector type
        valid_actions = {
            'pull': ['import', 'sync'],
            'push': ['export', 'sync'],
            'bidirectional': ['import', 'export', 'sync']
        }
        
        if action not in valid_actions.get(connector.connector_type, []):
            return JsonResponse({
                'error': f'Action "{action}" not supported for connector type "{connector.connector_type}"'
            }, status=400)
        
        try:
            with transaction.atomic():
                # Create job record
                job = DataImportExportJob.objects.create(
                    connector=connector,
                    job_type=action if action != 'sync' else 'sync',
                    status='pending',
                    job_config=data.get('config', {}),
                    parameters=data.get('parameters', {}),
                    triggered_by_id=request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None,
                )
                
                # Log job creation
                IntegrationLog.objects.create(
                    external_system=connector.external_system,
                    connector=connector,
                    job=job,
                    level='INFO',
                    activity_type='data_transfer',
                    message=f'Data {action} job created for connector "{connector.name}"',
                    details={'job_id': str(job.id), 'action': action}
                )
                
                # TODO: Queue job for background processing
                # This would typically integrate with Celery or similar task queue
                
                return JsonResponse({
                    'job_id': str(job.id),
                    'message': f'Data {action} job created successfully',
                    'status': 'pending'
                }, status=201)
                
        except Exception as e:
            return JsonResponse({
                'error': f'Failed to create {action} job',
                'message': str(e)
            }, status=400)
    
    def get(self, request: HttpRequest, job_id: str):
        """Get job status and details."""
        job = get_object_or_404(DataImportExportJob, id=job_id, is_active=True)
        
        return JsonResponse({
            'id': str(job.id),
            'connector_id': str(job.connector.id),
            'connector_name': job.connector.name,
            'job_type': job.job_type,
            'status': job.status,
            'started_at': job.started_at.isoformat() if job.started_at else None,
            'completed_at': job.completed_at.isoformat() if job.completed_at else None,
            'duration_seconds': job.duration_seconds,
            'records_processed': job.records_processed,
            'records_successful': job.records_successful,
            'records_failed': job.records_failed,
            'error_message': job.error_message,
            'retry_count': job.retry_count,
            'max_retries': job.max_retries,
            'created_at': job.created_at.isoformat(),
        })


@method_decorator(csrf_exempt, name='dispatch')
class IntegrationEndpointView(BaseIntegrationView):
    """API endpoints for managing integration endpoints and API versioning."""
    
    def get(self, request: HttpRequest, endpoint_id: Optional[str] = None):
        """Get integration endpoints or specific endpoint details."""
        if endpoint_id:
            endpoint = get_object_or_404(IntegrationEndpoint, id=endpoint_id, is_active=True)
            return JsonResponse({
                'id': str(endpoint.id),
                'name': endpoint.name,
                'description': endpoint.description,
                'endpoint_type': endpoint.endpoint_type,
                'path': endpoint.path,
                'http_methods': endpoint.http_methods,
                'version': endpoint.version,
                'is_deprecated': endpoint.is_deprecated,
                'deprecation_date': endpoint.deprecation_date.isoformat() if endpoint.deprecation_date else None,
                'replacement_endpoint_id': str(endpoint.replacement_endpoint.id) if endpoint.replacement_endpoint else None,
                'requires_authentication': endpoint.requires_authentication,
                'rate_limit_per_minute': endpoint.rate_limit_per_minute,
                'request_schema': endpoint.request_schema,
                'response_schema': endpoint.response_schema,
                'is_enabled': endpoint.is_enabled,
                'total_requests': endpoint.total_requests,
                'total_errors': endpoint.total_errors,
                'last_accessed': endpoint.last_accessed.isoformat() if endpoint.last_accessed else None,
                'created_at': endpoint.created_at.isoformat(),
            })
        
        # List integration endpoints
        queryset = IntegrationEndpoint.objects.filter(is_active=True)
        
        # Apply filters
        version = request.GET.get('version')
        if version:
            queryset = queryset.filter(version=version)
        
        endpoint_type = request.GET.get('endpoint_type')
        if endpoint_type:
            queryset = queryset.filter(endpoint_type=endpoint_type)
        
        is_deprecated = request.GET.get('is_deprecated')
        if is_deprecated is not None:
            queryset = queryset.filter(is_deprecated=is_deprecated.lower() == 'true')
        
        return JsonResponse(self.paginate_queryset(queryset, request))


@method_decorator(csrf_exempt, name='dispatch')
class ServiceDiscoveryView(BaseIntegrationView):
    """API endpoints for service discovery and load balancing."""
    
    def get(self, request: HttpRequest, service_name: Optional[str] = None):
        """Get service instances or specific service details."""
        if service_name:
            # Get healthy instances for a specific service
            instances = ServiceDiscovery.objects.filter(
                service_name=service_name,
                is_active=True,
                health_status='healthy'
            ).order_by('weight', 'current_connections')
            
            return JsonResponse({
                'service_name': service_name,
                'instances': [
                    {
                        'instance_id': instance.instance_id,
                        'host': instance.host,
                        'port': instance.port,
                        'protocol': instance.protocol,
                        'base_path': instance.base_path,
                        'full_url': instance.full_url,
                        'version': instance.version,
                        'environment': instance.environment,
                        'weight': instance.weight,
                        'current_connections': instance.current_connections,
                        'max_connections': instance.max_connections,
                        'last_heartbeat': instance.last_heartbeat.isoformat(),
                    }
                    for instance in instances
                ]
            })
        
        # List all services
        queryset = ServiceDiscovery.objects.filter(is_active=True)
        
        # Apply filters
        service_type = request.GET.get('service_type')
        if service_type:
            queryset = queryset.filter(service_type=service_type)
        
        environment = request.GET.get('environment')
        if environment:
            queryset = queryset.filter(environment=environment)
        
        health_status = request.GET.get('health_status')
        if health_status:
            queryset = queryset.filter(health_status=health_status)
        
        return JsonResponse(self.paginate_queryset(queryset, request))
    
    def post(self, request: HttpRequest):
        """Register a service instance."""
        data = self.get_json_data(request)
        
        try:
            with transaction.atomic():
                service, created = ServiceDiscovery.objects.update_or_create(
                    service_name=data['service_name'],
                    instance_id=data['instance_id'],
                    defaults={
                        'service_type': data['service_type'],
                        'host': data['host'],
                        'port': data['port'],
                        'protocol': data.get('protocol', 'http'),
                        'base_path': data.get('base_path', '/'),
                        'version': data['version'],
                        'environment': data.get('environment', 'development'),
                        'region': data.get('region', ''),
                        'availability_zone': data.get('availability_zone', ''),
                        'health_check_url': data.get('health_check_url', ''),
                        'weight': data.get('weight', 100),
                        'max_connections': data.get('max_connections', 1000),
                        'health_status': 'healthy',
                    }
                )
                
                action = 'registered' if created else 'updated'
                return JsonResponse({
                    'message': f'Service instance {action} successfully',
                    'instance_id': service.instance_id,
                    'service_name': service.service_name
                }, status=201 if created else 200)
                
        except Exception as e:
            return JsonResponse({
                'error': 'Failed to register service instance',
                'message': str(e)
            }, status=400)
    
    def put(self, request: HttpRequest, instance_id: str):
        """Update service instance heartbeat and status."""
        service = get_object_or_404(ServiceDiscovery, instance_id=instance_id, is_active=True)
        data = self.get_json_data(request)
        
        try:
            # Update heartbeat
            service.last_heartbeat = timezone.now()
            
            # Update other fields if provided
            if 'health_status' in data:
                service.health_status = data['health_status']
            if 'current_connections' in data:
                service.current_connections = data['current_connections']
            
            service.save()
            
            return JsonResponse({'message': 'Service instance updated successfully'})
            
        except Exception as e:
            return JsonResponse({
                'error': 'Failed to update service instance',
                'message': str(e)
            }, status=400)


@require_http_methods(["GET"])
def health_check(request: HttpRequest):
    """Health check endpoint for the integration service."""
    try:
        # Check database connectivity
        ExternalSystem.objects.count()
        
        # Check recent activity
        recent_logs = IntegrationLog.objects.filter(
            created_at__gte=timezone.now() - timedelta(minutes=5)
        ).count()
        
        return JsonResponse({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'service': 'integration',
            'version': 'v1',
            'recent_activity': recent_logs,
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'timestamp': timezone.now().isoformat(),
            'service': 'integration',
            'error': str(e)
        }, status=503)


@require_http_methods(["GET"])
def integration_stats(request: HttpRequest):
    """Get integration statistics and metrics."""
    try:
        stats = {
            'external_systems': {
                'total': ExternalSystem.objects.filter(is_active=True).count(),
                'healthy': ExternalSystem.objects.filter(is_active=True, is_healthy=True).count(),
                'by_type': dict(
                    ExternalSystem.objects.filter(is_active=True)
                    .values('system_type')
                    .annotate(count=Count('id'))
                    .values_list('system_type', 'count')
                )
            },
            'data_connectors': {
                'total': DataConnector.objects.filter(is_active=True).count(),
                'enabled': DataConnector.objects.filter(is_active=True, is_enabled=True).count(),
                'by_type': dict(
                    DataConnector.objects.filter(is_active=True)
                    .values('connector_type')
                    .annotate(count=Count('id'))
                    .values_list('connector_type', 'count')
                )
            },
            'jobs': {
                'total': DataImportExportJob.objects.filter(is_active=True).count(),
                'running': DataImportExportJob.objects.filter(is_active=True, status='running').count(),
                'completed_today': DataImportExportJob.objects.filter(
                    is_active=True,
                    status='completed',
                    completed_at__date=timezone.now().date()
                ).count(),
                'by_status': dict(
                    DataImportExportJob.objects.filter(is_active=True)
                    .values('status')
                    .annotate(count=Count('id'))
                    .values_list('status', 'count')
                )
            },
            'service_discovery': {
                'total_services': ServiceDiscovery.objects.filter(is_active=True).count(),
                'healthy_services': ServiceDiscovery.objects.filter(is_active=True, health_status='healthy').count(),
                'by_environment': dict(
                    ServiceDiscovery.objects.filter(is_active=True)
                    .values('environment')
                    .annotate(count=Count('id'))
                    .values_list('environment', 'count')
                )
            }
        }
        
        return JsonResponse({
            'timestamp': timezone.now().isoformat(),
            'stats': stats
        })
        
    except Exception as e:
        return JsonResponse({
            'error': 'Failed to retrieve integration statistics',
            'message': str(e)
        }, status=500)
