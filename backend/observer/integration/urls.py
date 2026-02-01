from django.urls import path, include
from . import views

app_name = 'integration'

urlpatterns = [
    # Health check and stats
    path('health/', views.health_check, name='health_check'),
    path('stats/', views.integration_stats, name='integration_stats'),
    
    # External Systems API
    path('systems/', views.ExternalSystemView.as_view(), name='external_systems_list'),
    path('systems/<str:system_id>/', views.ExternalSystemView.as_view(), name='external_system_detail'),
    
    # Data Connectors API
    path('connectors/', views.DataConnectorView.as_view(), name='data_connectors_list'),
    path('connectors/<str:connector_id>/', views.DataConnectorView.as_view(), name='data_connector_detail'),
    
    # Data Import/Export API
    path('data/<str:action>/', views.DataImportExportView.as_view(), name='data_import_export'),
    path('jobs/<str:job_id>/', views.DataImportExportView.as_view(), name='job_status'),
    
    # Integration Endpoints API
    path('endpoints/', views.IntegrationEndpointView.as_view(), name='integration_endpoints_list'),
    path('endpoints/<str:endpoint_id>/', views.IntegrationEndpointView.as_view(), name='integration_endpoint_detail'),
    
    # Service Discovery API
    path('services/', views.ServiceDiscoveryView.as_view(), name='service_discovery_list'),
    path('services/<str:service_name>/', views.ServiceDiscoveryView.as_view(), name='service_discovery_detail'),
    path('services/instances/<str:instance_id>/', views.ServiceDiscoveryView.as_view(), name='service_instance_update'),
]