"""
Management command for processing notification escalations and retries.
This should be run periodically (e.g., every minute) as a background task.
"""

import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from notification.services import NotificationService

logger = logging.getLogger('observer_eye.notification')


class Command(BaseCommand):
    help = 'Process notification escalations and retry failed deliveries'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--escalations-only',
            action='store_true',
            help='Only process escalations, skip retries',
        )
        parser.add_argument(
            '--retries-only',
            action='store_true',
            help='Only process retries, skip escalations',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output',
        )
    
    def handle(self, *args, **options):
        verbose = options['verbose']
        escalations_only = options['escalations_only']
        retries_only = options['retries_only']
        
        if verbose:
            self.stdout.write(f"Starting notification processing at {timezone.now()}")
        
        notification_service = NotificationService()
        
        escalated_count = 0
        retried_count = 0
        
        try:
            # Process escalations unless retries-only is specified
            if not retries_only:
                escalated_count = notification_service.process_escalations()
                if verbose and escalated_count > 0:
                    self.stdout.write(
                        self.style.SUCCESS(f'Processed {escalated_count} alert escalations')
                    )
            
            # Process retries unless escalations-only is specified
            if not escalations_only:
                retried_count = notification_service.retry_failed_deliveries()
                if verbose and retried_count > 0:
                    self.stdout.write(
                        self.style.SUCCESS(f'Retried {retried_count} failed deliveries')
                    )
            
            # Summary
            if verbose or escalated_count > 0 or retried_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Notification processing completed: '
                        f'{escalated_count} escalations, {retried_count} retries'
                    )
                )
        
        except Exception as e:
            logger.error(f"Error in notification processing: {e}")
            self.stdout.write(
                self.style.ERROR(f'Error processing notifications: {e}')
            )
            raise