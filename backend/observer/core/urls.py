from django.urls import path, include
from . import views, oauth_views
from .ingestion_views import (
    ingest_metrics,
    ingest_logs,
    ingest_telemetry,
    BulkIngestionView,
    ingestion_status
)

app_name = 'core'

urlpatterns = [
    # Health check endpoint
    path('health/', views.health_check, name='health_check'),
    
    # System status endpoint
    path('status/', views.system_status, name='system_status'),
    
    # Configuration endpoints
    path('config/', views.configuration_list, name='configuration_list'),
    path('config/<str:key>/', views.configuration_detail, name='configuration_detail'),
    
    # User management endpoints
    path('users/', views.user_list, name='user_list'),
    path('users/<uuid:user_id>/', views.user_detail, name='user_detail'),
    
    # Session management endpoints
    path('sessions/', views.session_list, name='session_list'),
    path('sessions/<uuid:session_id>/', views.session_detail, name='session_detail'),
    
    # Audit log endpoints
    path('audit/', views.audit_log_list, name='audit_log_list'),
    path('audit/<uuid:log_id>/', views.audit_log_detail, name='audit_log_detail'),
    
    # OAuth authentication endpoints
    path('auth/providers/', oauth_views.oauth_providers, name='oauth_providers'),
    path('auth/oauth/<str:provider>/authorize/', oauth_views.oauth_authorize, name='oauth_authorize'),
    path('auth/oauth/<str:provider>/callback/', oauth_views.oauth_callback, name='oauth_callback'),
    
    # Session management endpoints
    path('auth/session/', oauth_views.SessionView.as_view(), name='session_manage'),
    path('auth/session/refresh/', oauth_views.refresh_session, name='session_refresh'),
    path('auth/session/status/', oauth_views.session_status, name='session_status'),
    
    # Data ingestion endpoints
    path('ingest/metrics/', ingest_metrics, name='ingest_metrics'),
    path('ingest/logs/', ingest_logs, name='ingest_logs'),
    path('ingest/telemetry/', ingest_telemetry, name='ingest_telemetry'),
    path('ingest/bulk/', BulkIngestionView.as_view(), name='ingest_bulk'),
    path('ingest/status/', ingestion_status, name='ingestion_status'),
]