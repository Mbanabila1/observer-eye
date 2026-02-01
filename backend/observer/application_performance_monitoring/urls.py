from django.urls import path
from . import views

app_name = 'application_performance_monitoring'

urlpatterns = [
    path('services/', views.services_list, name='services_list'),
    path('services/<uuid:service_id>/metrics/', views.service_metrics, name='service_metrics'),
    path('health/', views.health_status, name='health_status'),
]