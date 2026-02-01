from django.urls import path
from . import views

app_name = 'analytics_performance_monitoring'

urlpatterns = [
    # Performance metrics
    path('metrics/', views.performance_metrics_list, name='performance_metrics_list'),
    path('summary/', views.performance_summary, name='performance_summary'),
    
    # Query performance
    path('queries/', views.query_performance_list, name='query_performance_list'),
    
    # Resource usage
    path('resources/', views.resource_usage_current, name='resource_usage_current'),
    
    # Performance alerts
    path('alerts/', views.performance_alerts_list, name='performance_alerts_list'),
]