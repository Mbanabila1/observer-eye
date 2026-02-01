from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Configuration for the core app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Observer Eye Core'
    
    def ready(self):
        """Initialize the app when Django starts."""
        # Import signal handlers
        try:
            from . import signals
        except ImportError:
            pass
        
        # Initialize structlog
        self._configure_structlog()
    
    def _configure_structlog(self):
        """Configure structlog for consistent logging."""
        import structlog
        from django.conf import settings
        
        # Configure structlog processors
        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="ISO"),
        ]
        
        if settings.DEBUG:
            processors.append(structlog.dev.ConsoleRenderer())
        else:
            processors.append(structlog.processors.JSONRenderer())
        
        structlog.configure(
            processors=processors,
            wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO level
            logger_factory=structlog.WriteLoggerFactory(),
            cache_logger_on_first_use=True,
        )
