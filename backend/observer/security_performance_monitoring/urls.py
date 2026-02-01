from django.urls import path
from . import views

app_name = 'security_performance_monitoring'

urlpatterns = [
    path('metrics/', views.security_metrics_summary, name='security_metrics_summary'),
    path('incidents/', views.security_incidents, name='security_incidents'),
]