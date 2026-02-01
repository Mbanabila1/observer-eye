from django.core.management.base import BaseCommand
from django.db import transaction
from settings.models import ConfigurationCategory, ConfigurationSetting, ConfigurationProfile


class Command(BaseCommand):
    help = 'Initialize default configuration categories and settings for Observer Eye Platform'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of existing settings',
        )

    def handle(self, *args, **options):
        force = options['force']
        
        self.stdout.write(
            self.style.SUCCESS('Initializing Observer Eye Platform configuration settings...')
        )
        
        with transaction.atomic():
            # Create configuration categories
            categories = self._create_categories(force)
            
            # Create default settings for each category
            settings_created = 0
            for category_name, category_obj in categories.items():
                count = self._create_settings_for_category(category_name, category_obj, force)
                settings_created += count
            
            # Create default configuration profile
            self._create_default_profile(force)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully initialized {len(categories)} categories and {settings_created} settings'
            )
        )

    def _create_categories(self, force):
        """Create default configuration categories."""
        categories_data = [
            {
                'name': 'authentication',
                'display_name': 'Authentication & Security',
                'description': 'Authentication providers, security policies, and session management',
                'icon': 'shield-check',
                'sort_order': 10
            },
            {
                'name': 'monitoring',
                'display_name': 'Monitoring & Performance',
                'description': 'Performance monitoring, metrics collection, and alerting configuration',
                'icon': 'chart-line',
                'sort_order': 20
            },
            {
                'name': 'notifications',
                'display_name': 'Notifications & Alerts',
                'description': 'Email, SMS, webhook, and other notification channel settings',
                'icon': 'bell',
                'sort_order': 30
            },
            {
                'name': 'data_processing',
                'display_name': 'Data Processing',
                'description': 'Data validation, transformation, and storage settings',
                'icon': 'database',
                'sort_order': 40
            },
            {
                'name': 'ui_preferences',
                'display_name': 'UI & Dashboard',
                'description': 'User interface preferences and dashboard configuration',
                'icon': 'layout-dashboard',
                'sort_order': 50
            },
            {
                'name': 'system',
                'display_name': 'System Configuration',
                'description': 'Core system settings, logging, and maintenance',
                'icon': 'settings',
                'sort_order': 60
            }
        ]
        
        categories = {}
        for cat_data in categories_data:
            category, created = ConfigurationCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            
            if not created and force:
                for key, value in cat_data.items():
                    setattr(category, key, value)
                category.save()
                self.stdout.write(f'Updated category: {category.display_name}')
            elif created:
                self.stdout.write(f'Created category: {category.display_name}')
            
            categories[cat_data['name']] = category
        
        return categories

    def _create_settings_for_category(self, category_name, category_obj, force):
        """Create default settings for a specific category."""
        settings_data = self._get_settings_data_for_category(category_name)
        settings_created = 0
        
        for setting_data in settings_data:
            setting_data['category'] = category_obj
            
            setting, created = ConfigurationSetting.objects.get_or_create(
                key=setting_data['key'],
                defaults=setting_data
            )
            
            if not created and force:
                for key, value in setting_data.items():
                    if key != 'key':  # Don't update the key
                        setattr(setting, key, value)
                setting.save()
                self.stdout.write(f'  Updated setting: {setting.key}')
            elif created:
                self.stdout.write(f'  Created setting: {setting.key}')
                settings_created += 1
        
        return settings_created

    def _get_settings_data_for_category(self, category_name):
        """Get default settings data for each category."""
        settings_map = {
            'authentication': [
                {
                    'key': 'auth.session_timeout_hours',
                    'display_name': 'Session Timeout (Hours)',
                    'description': 'Number of hours before user sessions expire',
                    'setting_type': 'integer',
                    'default_value': 24,
                    'is_required': True,
                    'validation_rules': {'min_value': 1, 'max_value': 168},
                    'help_text': 'Sessions will automatically expire after this many hours of inactivity',
                    'sort_order': 10
                },
                {
                    'key': 'auth.max_login_attempts',
                    'display_name': 'Maximum Login Attempts',
                    'description': 'Maximum failed login attempts before account lockout',
                    'setting_type': 'integer',
                    'default_value': 5,
                    'is_required': True,
                    'validation_rules': {'min_value': 3, 'max_value': 20},
                    'help_text': 'Account will be temporarily locked after this many failed attempts',
                    'sort_order': 20
                },
                {
                    'key': 'auth.lockout_duration_minutes',
                    'display_name': 'Account Lockout Duration (Minutes)',
                    'description': 'Duration of account lockout after max failed attempts',
                    'setting_type': 'integer',
                    'default_value': 15,
                    'is_required': True,
                    'validation_rules': {'min_value': 5, 'max_value': 1440},
                    'help_text': 'Account will be locked for this many minutes',
                    'sort_order': 30
                },
                {
                    'key': 'auth.password_min_length',
                    'display_name': 'Minimum Password Length',
                    'description': 'Minimum required password length',
                    'setting_type': 'integer',
                    'default_value': 16,
                    'is_required': True,
                    'is_readonly': True,
                    'validation_rules': {'min_value': 8, 'max_value': 128},
                    'help_text': 'Observer Eye Platform requires minimum 16 characters',
                    'sort_order': 40
                }
            ],
            'monitoring': [
                {
                    'key': 'monitoring.metrics_retention_days',
                    'display_name': 'Metrics Retention (Days)',
                    'description': 'Number of days to retain performance metrics',
                    'setting_type': 'integer',
                    'default_value': 365,
                    'is_required': True,
                    'validation_rules': {'min_value': 30, 'max_value': 2555},
                    'help_text': 'Older metrics will be automatically purged',
                    'sort_order': 10
                },
                {
                    'key': 'monitoring.telemetry_enabled',
                    'display_name': 'Enable Telemetry Collection',
                    'description': 'Enable or disable telemetry data collection',
                    'setting_type': 'boolean',
                    'default_value': True,
                    'is_required': True,
                    'help_text': 'Telemetry provides insights into system performance',
                    'sort_order': 20
                },
                {
                    'key': 'monitoring.telemetry_sample_rate',
                    'display_name': 'Telemetry Sample Rate',
                    'description': 'Percentage of telemetry events to sample (0.0 to 1.0)',
                    'setting_type': 'float',
                    'default_value': 0.1,
                    'is_required': True,
                    'validation_rules': {'min_value': 0.0, 'max_value': 1.0},
                    'help_text': '0.1 means 10% of events will be sampled',
                    'sort_order': 30
                },
                {
                    'key': 'monitoring.alert_check_interval_seconds',
                    'display_name': 'Alert Check Interval (Seconds)',
                    'description': 'How often to check alert conditions',
                    'setting_type': 'integer',
                    'default_value': 60,
                    'is_required': True,
                    'validation_rules': {'min_value': 10, 'max_value': 3600},
                    'help_text': 'More frequent checks provide faster alerting but use more resources',
                    'sort_order': 40
                }
            ],
            'notifications': [
                {
                    'key': 'notifications.email_enabled',
                    'display_name': 'Enable Email Notifications',
                    'description': 'Enable or disable email notifications',
                    'setting_type': 'boolean',
                    'default_value': True,
                    'is_required': True,
                    'help_text': 'Email notifications for alerts and system events',
                    'sort_order': 10
                },
                {
                    'key': 'notifications.default_from_email',
                    'display_name': 'Default From Email',
                    'description': 'Default email address for outgoing notifications',
                    'setting_type': 'email',
                    'default_value': 'noreply@observer-eye.com',
                    'is_required': True,
                    'help_text': 'This email will appear as the sender for notifications',
                    'sort_order': 20
                },
                {
                    'key': 'notifications.webhook_timeout_seconds',
                    'display_name': 'Webhook Timeout (Seconds)',
                    'description': 'Timeout for webhook notification delivery',
                    'setting_type': 'integer',
                    'default_value': 30,
                    'is_required': True,
                    'validation_rules': {'min_value': 5, 'max_value': 300},
                    'help_text': 'Webhooks will timeout after this many seconds',
                    'sort_order': 30
                }
            ],
            'data_processing': [
                {
                    'key': 'data.max_batch_size',
                    'display_name': 'Maximum Batch Size',
                    'description': 'Maximum number of records to process in a single batch',
                    'setting_type': 'integer',
                    'default_value': 1000,
                    'is_required': True,
                    'validation_rules': {'min_value': 100, 'max_value': 10000},
                    'help_text': 'Larger batches improve throughput but use more memory',
                    'sort_order': 10
                },
                {
                    'key': 'data.validation_strict_mode',
                    'display_name': 'Strict Validation Mode',
                    'description': 'Enable strict data validation (reject invalid data)',
                    'setting_type': 'boolean',
                    'default_value': True,
                    'is_required': True,
                    'help_text': 'When disabled, invalid data will be logged but not rejected',
                    'sort_order': 20
                },
                {
                    'key': 'data.compression_enabled',
                    'display_name': 'Enable Data Compression',
                    'description': 'Enable compression for stored data',
                    'setting_type': 'boolean',
                    'default_value': True,
                    'is_required': True,
                    'help_text': 'Compression reduces storage space but increases CPU usage',
                    'sort_order': 30
                }
            ],
            'ui_preferences': [
                {
                    'key': 'ui.default_theme',
                    'display_name': 'Default Theme',
                    'description': 'Default UI theme for new users',
                    'setting_type': 'choice',
                    'default_value': 'light',
                    'choices': [
                        {'value': 'light', 'label': 'Light Theme'},
                        {'value': 'dark', 'label': 'Dark Theme'},
                        {'value': 'auto', 'label': 'Auto (System Preference)'}
                    ],
                    'is_required': True,
                    'help_text': 'Users can override this in their personal settings',
                    'sort_order': 10
                },
                {
                    'key': 'ui.dashboard_refresh_interval_seconds',
                    'display_name': 'Dashboard Refresh Interval (Seconds)',
                    'description': 'How often dashboards automatically refresh',
                    'setting_type': 'integer',
                    'default_value': 30,
                    'is_required': True,
                    'validation_rules': {'min_value': 5, 'max_value': 300},
                    'help_text': 'More frequent refreshes provide real-time data but use more resources',
                    'sort_order': 20
                }
            ],
            'system': [
                {
                    'key': 'system.log_level',
                    'display_name': 'System Log Level',
                    'description': 'Minimum log level for system logging',
                    'setting_type': 'choice',
                    'default_value': 'INFO',
                    'choices': [
                        {'value': 'DEBUG', 'label': 'Debug (Most Verbose)'},
                        {'value': 'INFO', 'label': 'Info'},
                        {'value': 'WARNING', 'label': 'Warning'},
                        {'value': 'ERROR', 'label': 'Error'},
                        {'value': 'CRITICAL', 'label': 'Critical (Least Verbose)'}
                    ],
                    'is_required': True,
                    'help_text': 'Lower levels include all higher level messages',
                    'sort_order': 10
                },
                {
                    'key': 'system.maintenance_mode',
                    'display_name': 'Maintenance Mode',
                    'description': 'Enable maintenance mode to restrict access',
                    'setting_type': 'boolean',
                    'default_value': False,
                    'is_required': True,
                    'help_text': 'When enabled, only administrators can access the system',
                    'sort_order': 20
                },
                {
                    'key': 'system.audit_log_retention_days',
                    'display_name': 'Audit Log Retention (Days)',
                    'description': 'Number of days to retain audit logs',
                    'setting_type': 'integer',
                    'default_value': 90,
                    'is_required': True,
                    'validation_rules': {'min_value': 30, 'max_value': 2555},
                    'help_text': 'Audit logs track all system configuration changes',
                    'sort_order': 30
                }
            ]
        }
        
        return settings_map.get(category_name, [])

    def _create_default_profile(self, force):
        """Create default configuration profile."""
        profile_data = {
            'name': 'default',
            'display_name': 'Default Configuration',
            'description': 'Default configuration profile for Observer Eye Platform',
            'is_default': True,
            'is_system': True
        }
        
        profile, created = ConfigurationProfile.objects.get_or_create(
            name='default',
            defaults=profile_data
        )
        
        if not created and force:
            for key, value in profile_data.items():
                if key != 'name':
                    setattr(profile, key, value)
            profile.save()
            self.stdout.write('Updated default configuration profile')
        elif created:
            self.stdout.write('Created default configuration profile')