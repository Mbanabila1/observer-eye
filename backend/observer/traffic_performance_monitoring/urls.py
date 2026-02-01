from django.urls import path
from . import views

app_name = 'traffic_performance_monitoring'

urlpatterns = [
    path('metrics/', views.traffic_metrics_summary, name='traffic_metrics_summary'),
    path('flows/', views.traffic_flows_summary, name='traffic_flows_summary'),
]