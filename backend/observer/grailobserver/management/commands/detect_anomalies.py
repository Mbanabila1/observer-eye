"""
Management command to detect anomalies in observability data.
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from grailobserver.models import ObservabilityTarget, ObservabilityAnomaly
from grailobserver.services import AnomalyDetectionService
import logging

logger = logging.getLogger('observer_eye.grailobserver.commands')


class Command(BaseCommand):
    help = 'Detect anomalies in observability data for all targets'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--target-id',
            type=str,
            help='Detect anomalies for specific target ID only',
        )
        parser.add_argument(
            '--lookback-hours',
            type=int,
            default=24,
            help='Hours to look back for anomaly detection (default: 24)',
        )
        parser.add_argument(
            '--save-anomalies',
            action='store_true',
            help='Save detected anomalies to database',
        )
    
    def handle(self, *args, **options):
        """Execute the anomaly detection command."""
        try:
            # Build query for targets
            targets = ObservabilityTarget.objects.filter(is_active=True, is_monitored=True)
            
            if options['target_id']:
                targets = targets.filter(id=options['target_id'])
                if not targets.exists():
                    raise CommandError(f"Target with ID {options['target_id']} not found")
            
            if not targets.exists():
                self.stdout.write(
                    self.style.WARNING('No targets found for anomaly detection')
                )
                return
            
            lookback_hours = options['lookback_hours']
            save_anomalies = options['save_anomalies']
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Detecting anomalies for {targets.count()} targets '
                    f'(lookback: {lookback_hours} hours)...'
                )
            )
            
            # Detect anomalies
            all_anomalies = []
            for target in targets:
                self.stdout.write(f'Analyzing {target.name}...', ending='')
                
                try:
                    anomalies = AnomalyDetectionService.detect_performance_anomalies(
                        target, lookback_hours
                    )
                    
                    if anomalies:
                        all_anomalies.extend(anomalies)
                        self.stdout.write(
                            self.style.WARNING(f' Found {len(anomalies)} anomalies')
                        )
                        
                        # Show anomaly details
                        for anomaly in anomalies:
                            severity = anomaly.get('severity', 'unknown')
                            metric = anomaly.get('metric_name', 'unknown')
                            deviation = anomaly.get('deviation_percentage', 0)
                            self.stdout.write(
                                f"  - {severity.upper()} {metric} anomaly "
                                f"({deviation:.1f}% deviation)"
                            )
                    else:
                        self.stdout.write(self.style.SUCCESS(' ✓ No anomalies'))
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f' Error: {e}'))
                    logger.error(f"Anomaly detection failed for target {target.id}: {e}")
            
            # Save anomalies if requested
            if save_anomalies and all_anomalies:
                self.stdout.write(f'\nSaving {len(all_anomalies)} anomalies to database...')
                
                saved_count = 0
                for anomaly_data in all_anomalies:
                    try:
                        # Check if similar anomaly already exists
                        existing = ObservabilityAnomaly.objects.filter(
                            target=anomaly_data['target'],
                            anomaly_type=anomaly_data['anomaly_type'],
                            metric_name=anomaly_data['metric_name'],
                            detected_at__gte=timezone.now() - timezone.timedelta(hours=1),
                        ).exists()
                        
                        if not existing:
                            ObservabilityAnomaly.objects.create(**anomaly_data)
                            saved_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error saving anomaly: {e}")
                
                self.stdout.write(
                    self.style.SUCCESS(f'Saved {saved_count} new anomalies')
                )
            
            # Summary
            self.stdout.write('\n' + '='*50)
            self.stdout.write('ANOMALY DETECTION SUMMARY')
            self.stdout.write('='*50)
            self.stdout.write(f'Targets analyzed: {targets.count()}')
            self.stdout.write(f'Total anomalies found: {len(all_anomalies)}')
            
            if all_anomalies:
                # Group by severity
                severity_counts = {}
                for anomaly in all_anomalies:
                    severity = anomaly.get('severity', 'unknown')
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
                
                for severity, count in severity_counts.items():
                    if severity == 'critical':
                        self.stdout.write(self.style.ERROR(f'Critical: {count}'))
                    elif severity == 'high':
                        self.stdout.write(self.style.WARNING(f'High: {count}'))
                    elif severity == 'medium':
                        self.stdout.write(self.style.WARNING(f'Medium: {count}'))
                    else:
                        self.stdout.write(f'{severity.title()}: {count}')
                
                # Group by type
                type_counts = {}
                for anomaly in all_anomalies:
                    anomaly_type = anomaly.get('anomaly_type', 'unknown')
                    type_counts[anomaly_type] = type_counts.get(anomaly_type, 0) + 1
                
                self.stdout.write('\nBy type:')
                for anomaly_type, count in type_counts.items():
                    self.stdout.write(f'  {anomaly_type}: {count}')
            
            if not save_anomalies and all_anomalies:
                self.stdout.write(
                    self.style.WARNING(
                        '\nNote: Use --save-anomalies to save detected anomalies to database'
                    )
                )
            
            self.stdout.write(f'\nAnomaly detection completed at {timezone.now()}')
            
        except Exception as e:
            logger.error(f"Anomaly detection command failed: {e}")
            raise CommandError(f"Anomaly detection command failed: {e}")