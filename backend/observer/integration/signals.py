"""
Signal handlers for the integration app.
Handles automatic logging, health checks, and other integration events.
"""

import logging
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta

from .models import (
    ExternalSystem, DataConnector, DataImportExportJob, 
    IntegrationLog, ServiceDiscovery
)

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ExternalSystem)
def external_system_created_or_updated(sender, instance, created, **kwargs):
    """Log when external systems are created or updated."""
    action = 'created' if created else 'updated'
    
    IntegrationLog.objects.create(
        external_system=instance,
        level='INFO',
        activity_type='system',
        message=f'External system "{instance.name}" {action}',
        details={
            'system_id': str(instance.id),
            'system_type': instance.system_type,
            'action': action
        }
    )
    
    logger.info(f'External system {action}: {instance.name} ({instance.system_type})')


@receiver(post_delete, sender=ExternalSystem)
def external_system_deleted(sender, instance, **kwargs):
    """Log when external systems are deleted."""
    IntegrationLog.objects.create(
        level='INFO',
        activity_type='system',
        message=f'External system "{instance.name}" deleted',
        details={
            'system_id': str(instance.id),
            'system_type': instance.system_type,
            'action': 'deleted'
        }
    )
    
    logger.info(f'External system deleted: {instance.name} ({instance.system_type})')


@receiver(post_save, sender=DataConnector)
def data_connector_created_or_updated(sender, instance, created, **kwargs):
    """Log when data connectors are created or updated."""
    action = 'created' if created else 'updated'
    
    IntegrationLog.objects.create(
        external_system=instance.external_system,
        connector=instance,
        level='INFO',
        activity_type='system',
        message=f'Data connector "{instance.name}" {action}',
        details={
            'connector_id': str(instance.id),
            'connector_type': instance.connector_type,
            'action': action
        }
    )
    
    logger.info(f'Data connector {action}: {instance.name} ({instance.connector_type})')


@receiver(pre_save, sender=DataImportExportJob)
def job_status_changed(sender, instance, **kwargs):
    """Log when job status changes."""
    if instance.pk:  # Only for existing jobs
        try:
            old_instance = DataImportExportJob.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                # Status changed
                IntegrationLog.objects.create(
                    external_system=instance.connector.external_system,
                    connector=instance.connector,
                    job=instance,
                    level='INFO',
                    activity_type='data_transfer',
                    message=f'Job status changed from {old_instance.status} to {instance.status}',
                    details={
                        'job_id': str(instance.id),
                        'job_type': instance.job_type,
                        'old_status': old_instance.status,
                        'new_status': instance.status
                    }
                )
                
                # Update connector last sync info if job completed
                if instance.status == 'completed':
                    instance.connector.last_sync = timezone.now()
                    instance.connector.last_sync_status = 'completed'
                    instance.connector.last_sync_message = 'Job completed successfully'
                    instance.connector.save()
                elif instance.status == 'failed':
                    instance.connector.last_sync_status = 'failed'
                    instance.connector.last_sync_message = instance.error_message or 'Job failed'
                    instance.connector.save()
        except DataImportExportJob.DoesNotExist:
            pass


@receiver(post_save, sender=ServiceDiscovery)
def service_registered_or_updated(sender, instance, created, **kwargs):
    """Log when services are registered or updated."""
    action = 'registered' if created else 'updated'
    
    IntegrationLog.objects.create(
        level='INFO',
        activity_type='system',
        message=f'Service {action}: {instance.service_name}:{instance.instance_id}',
        details={
            'service_name': instance.service_name,
            'instance_id': instance.instance_id,
            'service_type': instance.service_type,
            'host': instance.host,
            'port': instance.port,
            'action': action
        }
    )
    
    logger.info(f'Service {action}: {instance.service_name}:{instance.instance_id} at {instance.host}:{instance.port}')


@receiver(post_delete, sender=ServiceDiscovery)
def service_deregistered(sender, instance, **kwargs):
    """Log when services are deregistered."""
    IntegrationLog.objects.create(
        level='INFO',
        activity_type='system',
        message=f'Service deregistered: {instance.service_name}:{instance.instance_id}',
        details={
            'service_name': instance.service_name,
            'instance_id': instance.instance_id,
            'service_type': instance.service_type,
            'action': 'deregistered'
        }
    )
    
    logger.info(f'Service deregistered: {instance.service_name}:{instance.instance_id}')


# Periodic health check functions (would be called by Celery tasks or similar)
def check_external_system_health():
    """Check health of all external systems."""
    from .utils import ExternalSystemConnector
    
    systems = ExternalSystem.objects.filter(is_active=True)
    
    for system in systems:
        # Only check if it's been more than the configured interval
        if system.last_health_check:
            time_since_check = timezone.now() - system.last_health_check
            if time_since_check.total_seconds() < (system.health_check_interval_minutes * 60):
                continue  # Skip, too soon
        
        connector = ExternalSystemConnector(system)
        result = connector.test_connection()
        
        # Update health status
        system.is_healthy = result['success']
        system.last_health_check = timezone.now()
        system.save()
        
        if not result['success']:
            logger.warning(f'Health check failed for {system.name}: {result.get("error", "Unknown error")}')


def cleanup_old_logs(days_to_keep: int = 30):
    """Clean up old integration logs."""
    cutoff_date = timezone.now() - timedelta(days=days_to_keep)
    
    deleted_count = IntegrationLog.objects.filter(
        created_at__lt=cutoff_date
    ).delete()[0]
    
    if deleted_count > 0:
        logger.info(f'Cleaned up {deleted_count} old integration logs')


def cleanup_completed_jobs(days_to_keep: int = 7):
    """Clean up old completed jobs."""
    cutoff_date = timezone.now() - timedelta(days=days_to_keep)
    
    deleted_count = DataImportExportJob.objects.filter(
        status='completed',
        completed_at__lt=cutoff_date
    ).delete()[0]
    
    if deleted_count > 0:
        logger.info(f'Cleaned up {deleted_count} old completed jobs')


def cleanup_stale_services(minutes_to_keep: int = 10):
    """Clean up stale service instances."""
    from .utils import ServiceDiscoveryManager
    ServiceDiscoveryManager.cleanup_stale_instances(minutes_to_keep)