from django.urls import path
from . import views

app_name = 'system_performance_monitoring'

urlpatterns = [
    # System performance monitoring endpoints will be implemented later
    path('', views.placeholder_view, name='placeholder'),
]