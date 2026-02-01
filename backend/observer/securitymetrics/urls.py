from django.urls import path
from . import views

app_name = 'securitymetrics'

urlpatterns = [
    path('events/', views.security_events_summary, name='security_events_summary'),
    path('vulnerabilities/', views.vulnerability_summary, name='vulnerability_summary'),
]