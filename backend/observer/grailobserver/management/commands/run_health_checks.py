"""
Management command to run health checks on all observability targets.
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from grailobserver.models import ObservabilityTarget
from grailobserver.services import HealthCheckService
import logging

logger = logging.getLogger('observer_eye.grailobserver.commands')


class Command(BaseCommand):
    help = 'Run health checks on all active observability targets'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--target-id',
            type=str,
            help='Run health check for specific target ID only',
        )
        parser.add_argument(
            '--target-type',
            type=str,
            choices=['service', 'database', 'cache', 'queue', 'api', 'infrastructure', 'custom'],
            help='Run health checks for specific target type only',
        )
        parser.add_argument(
            '--critical-only',
            action='store_true',
            help='Run health checks for critical targets only',
        )
    
    def handle(self, *args, **options):
        """Execute the health check command."""
        try:
            # Build query for targets
            targets = ObservabilityTarget.objects.filter(is_active=True, is_monitored=True)
            
            if options['target_id']:
                targets = targets.filter(id=options['target_id'])
                if not targets.exists():
                    raise CommandError(f"Target with ID {options['target_id']} not found")
            
            if options['target_type']:
                targets = targets.filter(target_type=options['target_type'])
            
            if options['critical_only']:
                targets = targets.filter(is_critical=True)
            
            if not targets.exists():
                self.stdout.write(
                    self.style.WARNING('No targets found matching the criteria')
                )
                return
            
            self.stdout.write(
                self.style.SUCCESS(f'Running health checks for {targets.count()} targets...')
            )
            
            # Run health checks
            results = []
            for target in targets:
                self.stdout.write(f'Checking {target.name}...', ending='')
                
                try:
                    result = HealthCheckService.perform_health_check(target)
                    results.append(result)
                    
                    status = result.get('overall_status', 'unknown')
                    if status == 'healthy':
                        self.stdout.write(self.style.SUCCESS(' ✓ Healthy'))
                    elif status == 'degraded':
                        self.stdout.write(self.style.WARNING(' ⚠ Degraded'))
                    elif status == 'unhealthy':
                        self.stdout.write(self.style.ERROR(' ✗ Unhealthy'))
                    else:
                        self.stdout.write(self.style.WARNING(' ? Unknown'))
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f' Error: {e}'))
                    logger.error(f"Health check failed for target {target.id}: {e}")
            
            # Summary
            healthy_count = sum(1 for r in results if r.get('overall_status') == 'healthy')
            degraded_count = sum(1 for r in results if r.get('overall_status') == 'degraded')
            unhealthy_count = sum(1 for r in results if r.get('overall_status') == 'unhealthy')
            unknown_count = len(results) - healthy_count - degraded_count - unhealthy_count
            
            self.stdout.write('\n' + '='*50)
            self.stdout.write('HEALTH CHECK SUMMARY')
            self.stdout.write('='*50)
            self.stdout.write(f'Total targets checked: {len(results)}')
            self.stdout.write(self.style.SUCCESS(f'Healthy: {healthy_count}'))
            self.stdout.write(self.style.WARNING(f'Degraded: {degraded_count}'))
            self.stdout.write(self.style.ERROR(f'Unhealthy: {unhealthy_count}'))
            if unknown_count > 0:
                self.stdout.write(self.style.WARNING(f'Unknown: {unknown_count}'))
            
            # Show detailed results for unhealthy targets
            if unhealthy_count > 0:
                self.stdout.write('\nUNHEALTHY TARGETS:')
                for result in results:
                    if result.get('overall_status') == 'unhealthy':
                        self.stdout.write(f"- {result.get('target_name', 'Unknown')}")
                        for check_name, check_result in result.get('checks', {}).items():
                            if check_result.get('status') == 'unhealthy':
                                details = check_result.get('details', 'No details')
                                self.stdout.write(f"  {check_name}: {details}")
            
            self.stdout.write(f'\nHealth checks completed at {timezone.now()}')
            
        except Exception as e:
            logger.error(f"Health check command failed: {e}")
            raise CommandError(f"Health check command failed: {e}")