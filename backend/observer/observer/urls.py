"""
URL configuration for Observer Eye Platform.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Admin site customization
admin.site.site_header = "Observer Eye Platform Administration"
admin.site.site_title = "Observer Eye Admin"
admin.site.index_title = "Welcome to Observer Eye Platform Administration"

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/v1/core/', include('core.urls')),
    path('api/v1/analytics/', include('analytics.urls')),
    path('api/v1/metrics/', include('appmetrics.urls')),
    path('api/v1/notifications/', include('notification.urls')),
    path('api/v1/dashboards/', include('template_dashboards.urls')),
    path('api/v1/settings/', include('settings.urls')),
    
    # Performance monitoring endpoints
    path('api/v1/performance/analytics/', include('analytics_performance_monitoring.urls')),
    path('api/v1/performance/application/', include('application_performance_monitoring.urls')),
    path('api/v1/performance/identity/', include('identity_performance_monitoring.urls')),
    path('api/v1/performance/security/', include('security_performance_monitoring.urls')),
    path('api/v1/performance/system/', include('system_performance_monitoring.urls')),
    path('api/v1/performance/traffic/', include('traffic_performance_monitoring.urls')),
    
    # Metrics endpoints
    path('api/v1/metrics/network/', include('netmetrics.urls')),
    path('api/v1/metrics/security/', include('securitymetrics.urls')),
    path('api/v1/metrics/system/', include('sysmetrics.urls')),
    
    # Integration and specialized endpoints
    path('api/v1/integration/', include('integration.urls')),
    path('api/v1/grail/', include('grailobserver.urls')),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
