"""
Django app configuration for grailobserver.
Specialized observability features for the Observer Eye Platform.
"""

from django.apps import AppConfig


class GrailobserverConfig(AppConfig):
    """Configuration for the grailobserver Django app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'grailobserver'
    verbose_name = 'Grail Observer'
    
    def ready(self):
        """Initialize app when Django starts."""
        # Import signal handlers if any
        # import grailobserver.signals
        pass
