"""
Management command to set up OAuth identity providers.
Creates default OAuth provider configurations in the database.
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from core.models import IdentityProvider


class Command(BaseCommand):
    help = 'Set up OAuth identity providers from settings'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update existing providers',
        )
    
    def handle(self, *args, **options):
        """Set up OAuth providers from settings."""
        force_update = options['force']
        
        # Default OAuth provider configurations
        provider_configs = {
            'github': {
                'authorization_url': 'https://github.com/login/oauth/authorize',
                'token_url': 'https://github.com/login/oauth/access_token',
                'user_info_url': 'https://api.github.com/user',
                'scope': 'user:email'
            },
            'gitlab': {
                'authorization_url': 'https://gitlab.com/oauth/authorize',
                'token_url': 'https://gitlab.com/oauth/token',
                'user_info_url': 'https://gitlab.com/api/v4/user',
                'scope': 'read_user'
            },
            'google': {
                'authorization_url': 'https://accounts.google.com/o/oauth2/v2/auth',
                'token_url': 'https://oauth2.googleapis.com/token',
                'user_info_url': 'https://www.googleapis.com/oauth2/v2/userinfo',
                'scope': 'openid email profile'
            },
            'microsoft': {
                'authorization_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
                'token_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/token',
                'user_info_url': 'https://graph.microsoft.com/v1.0/me',
                'scope': 'openid email profile'
            }
        }
        
        created_count = 0
        updated_count = 0
        
        for provider_name, config in provider_configs.items():
            # Get OAuth settings for this provider
            oauth_settings = settings.OAUTH_PROVIDERS.get(provider_name, {})
            
            if not oauth_settings.get('client_id'):
                self.stdout.write(
                    self.style.WARNING(
                        f'Skipping {provider_name}: No client_id in settings'
                    )
                )
                continue
            
            # Check if provider already exists
            provider, created = IdentityProvider.objects.get_or_create(
                name=provider_name,
                defaults={
                    'client_id': oauth_settings['client_id'],
                    'client_secret': oauth_settings['client_secret'],
                    'authorization_url': config['authorization_url'],
                    'token_url': config['token_url'],
                    'user_info_url': config['user_info_url'],
                    'scope': config['scope'],
                    'is_enabled': oauth_settings.get('enabled', True),
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created OAuth provider: {provider_name}'
                    )
                )
            elif force_update:
                # Update existing provider
                provider.client_id = oauth_settings['client_id']
                provider.client_secret = oauth_settings['client_secret']
                provider.authorization_url = config['authorization_url']
                provider.token_url = config['token_url']
                provider.user_info_url = config['user_info_url']
                provider.scope = config['scope']
                provider.is_enabled = oauth_settings.get('enabled', True)
                provider.save()
                
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Updated OAuth provider: {provider_name}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'OAuth provider {provider_name} already exists (use --force to update)'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'OAuth provider setup complete: {created_count} created, {updated_count} updated'
            )
        )