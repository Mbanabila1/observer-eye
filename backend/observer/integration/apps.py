from django.apps import AppConfig


class IntegrationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'integration'
    verbose_name = 'External System Integration'
    
    def ready(self):
        """Initialize the integration app when Django starts."""
        # Import signal handlers
        import integration.signals
