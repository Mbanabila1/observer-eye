from django.apps import AppConfig


class SettingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'settings'
    verbose_name = 'Platform Configuration Settings'
    
    def ready(self):
        """Initialize the settings app."""
        # Import signals if any are defined
        try:
            from . import signals
        except ImportError:
            pass
    
    def initialize_default_settings(self):
        """Initialize default configuration categories and settings."""
        # This will be called during app initialization
        # Default settings will be created via management commands or migrations
        pass
