from django.urls import path
from . import views

app_name = 'identity_performance_monitoring'

urlpatterns = [
    path('providers/', views.provider_metrics, name='provider_metrics'),
    path('events/', views.auth_events_summary, name='auth_events_summary'),
]