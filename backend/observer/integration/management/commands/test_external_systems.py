"""
Management command to test connections to all external systems.
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from integration.models import ExternalSystem
from integration.utils import ExternalSystemConnector


class Command(BaseCommand):
    help = 'Test connections to all external systems'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--system-id',
            type=str,
            help='Test specific system by ID',
        )
        parser.add_argument(
            '--system-name',
            type=str,
            help='Test specific system by name',
        )
        parser.add_argument(
            '--system-type',
            type=str,
            help='Test systems of specific type',
        )
        parser.add_argument(
            '--update-health',
            action='store_true',
            help='Update health status based on test results',
        )
    
    def handle(self, *args, **options):
        # Build queryset based on options
        queryset = ExternalSystem.objects.filter(is_active=True)
        
        if options['system_id']:
            queryset = queryset.filter(id=options['system_id'])
        elif options['system_name']:
            queryset = queryset.filter(name=options['system_name'])
        elif options['system_type']:
            queryset = queryset.filter(system_type=options['system_type'])
        
        systems = list(queryset)
        
        if not systems:
            self.stdout.write(
                self.style.WARNING('No external systems found matching criteria')
            )
            return
        
        self.stdout.write(f'Testing {len(systems)} external system(s)...\n')
        
        results = []
        for system in systems:
            self.stdout.write(f'Testing {system.name} ({system.system_type})...', ending=' ')
            
            connector = ExternalSystemConnector(system)
            result = connector.test_connection()
            
            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(f"✓ OK ({result.get('response_time_ms', 0):.1f}ms)")
                )
                if options['update_health']:
                    system.is_healthy = True
                    system.last_health_check = timezone.now()
                    system.save()
            else:
                self.stdout.write(
                    self.style.ERROR(f"✗ FAILED - {result.get('error', 'Unknown error')}")
                )
                if options['update_health']:
                    system.is_healthy = False
                    system.last_health_check = timezone.now()
                    system.save()
            
            results.append({
                'system': system,
                'result': result
            })
        
        # Summary
        successful = sum(1 for r in results if r['result']['success'])
        failed = len(results) - successful
        
        self.stdout.write(f'\nSummary:')
        self.stdout.write(f'  Successful: {successful}')
        self.stdout.write(f'  Failed: {failed}')
        
        if failed > 0:
            self.stdout.write(f'\nFailed systems:')
            for r in results:
                if not r['result']['success']:
                    system = r['system']
                    error = r['result'].get('error', 'Unknown error')
                    self.stdout.write(f'  - {system.name}: {error}')
        
        if options['update_health']:
            self.stdout.write(f'\nHealth status updated for all tested systems.')