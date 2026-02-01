"""
Management command to create default notification templates.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from notification.models import NotificationTemplate, NotificationChannel

User = get_user_model()


class Command(BaseCommand):
    help = 'Create default notification templates for all channel types'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user-email',
            type=str,
            help='Email of user to assign as template creator (defaults to first superuser)',
        )
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Overwrite existing default templates',
        )
    
    def handle(self, *args, **options):
        user_email = options.get('user_email')
        overwrite = options['overwrite']
        
        # Get user to assign as creator
        if user_email:
            try:
                user = User.objects.get(email=user_email)
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User with email {user_email} not found')
                )
                return
        else:
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                self.stdout.write(
                    self.style.ERROR('No superuser found. Please create a user first.')
                )
                return
        
        # Template definitions
        templates = [
            # Email templates
            {
                'name': 'Default Email Alert Triggered',
                'template_type': 'alert_triggered',
                'channel_type': 'email',
                'subject_template': '[{{ alert.rule.severity|upper }}] {{ alert.title }}',
                'body_template': '''Alert: {{ alert.title }}

Rule: {{ alert.rule.name }}
Severity: {{ alert.rule.severity|upper }}
Status: {{ alert.status|upper }}
Triggered: {{ alert.triggered_at }}

Message:
{{ alert.message }}

{% if alert.metadata %}
Additional Information:
{% for key, value in alert.metadata.items %}
- {{ key }}: {{ value }}
{% endfor %}
{% endif %}

Alert ID: {{ alert.id }}
Fingerprint: {{ alert.fingerprint }}'''
            },
            {
                'name': 'Default Email Alert Acknowledged',
                'template_type': 'alert_acknowledged',
                'channel_type': 'email',
                'subject_template': '[ACKNOWLEDGED] {{ alert.title }}',
                'body_template': '''Alert Acknowledged: {{ alert.title }}

Rule: {{ alert.rule.name }}
Acknowledged by: {{ alert.acknowledged_by.email }}
Acknowledged at: {{ alert.acknowledged_at }}

Original alert triggered: {{ alert.triggered_at }}

Alert ID: {{ alert.id }}'''
            },
            {
                'name': 'Default Email Alert Resolved',
                'template_type': 'alert_resolved',
                'channel_type': 'email',
                'subject_template': '[RESOLVED] {{ alert.title }}',
                'body_template': '''Alert Resolved: {{ alert.title }}

Rule: {{ alert.rule.name }}
Resolved by: {{ alert.resolved_by.email }}
Resolved at: {{ alert.resolved_at }}

Duration: {{ alert.resolved_at|timesince:alert.triggered_at }}

Alert ID: {{ alert.id }}'''
            },
            
            # Webhook templates
            {
                'name': 'Default Webhook Alert Triggered',
                'template_type': 'alert_triggered',
                'channel_type': 'webhook',
                'subject_template': '{{ alert.title }}',
                'body_template': '''{{ alert.title }}

Rule: {{ alert.rule.name }} ({{ alert.rule.severity }})
Status: {{ alert.status }}
Triggered: {{ alert.triggered_at }}

{{ alert.message }}'''
            },
            
            # Slack templates
            {
                'name': 'Default Slack Alert Triggered',
                'template_type': 'alert_triggered',
                'channel_type': 'slack',
                'subject_template': ':warning: {{ alert.title }}',
                'body_template': '''*{{ alert.rule.name }}* alert triggered

*Severity:* {{ alert.rule.severity|upper }}
*Status:* {{ alert.status|upper }}
*Triggered:* {{ alert.triggered_at }}

{{ alert.message }}'''
            },
            
            # SMS templates (shorter format)
            {
                'name': 'Default SMS Alert Triggered',
                'template_type': 'alert_triggered',
                'channel_type': 'sms',
                'subject_template': 'ALERT: {{ alert.rule.name }}',
                'body_template': 'ALERT [{{ alert.rule.severity|upper }}]: {{ alert.title }} - {{ alert.message|truncatechars:100 }}'
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for template_data in templates:
            # Check if template already exists
            existing = NotificationTemplate.objects.filter(
                template_type=template_data['template_type'],
                channel_type=template_data['channel_type'],
                is_default=True
            ).first()
            
            if existing and not overwrite:
                self.stdout.write(
                    f"Default template already exists for {template_data['channel_type']} "
                    f"{template_data['template_type']}, skipping..."
                )
                continue
            
            if existing and overwrite:
                # Update existing template
                for key, value in template_data.items():
                    if key != 'name':  # Don't update the name
                        setattr(existing, key, value)
                existing.save()
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Updated default template: {template_data['name']}"
                    )
                )
            else:
                # Create new template
                NotificationTemplate.objects.create(
                    **template_data,
                    is_default=True,
                    created_by=user
                )
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created default template: {template_data['name']}"
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Template creation completed: {created_count} created, {updated_count} updated'
            )
        )