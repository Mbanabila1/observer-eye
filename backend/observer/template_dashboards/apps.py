from django.apps import AppConfig


class TemplateDashboardsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'template_dashboards'
    verbose_name = 'Dashboard Templates'
    
    def ready(self):
        """Initialize app when Django starts"""
        # Import signals if any
        pass
