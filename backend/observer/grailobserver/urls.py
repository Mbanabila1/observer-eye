"""
URL patterns for grailobserver app.
Provides REST API endpoints for specialized observability features.
"""

from django.urls import path
from . import views

app_name = 'grailobserver'

urlpatterns = [
    # Health and status endpoints
    path('health/', views.health_check, name='health_check'),
    path('dashboard/summary/', views.dashboard_summary, name='dashboard_summary'),
    
    # Observability targets
    path('targets/', views.ObservabilityTargetView.as_view(), name='targets_list'),
    path('targets/<uuid:target_id>/', views.ObservabilityTargetView.as_view(), name='target_detail'),
    
    # Service Level Indicators (SLIs)
    path('slis/', views.SLIView.as_view(), name='slis_list'),
    path('slis/<uuid:sli_id>/', views.SLIView.as_view(), name='sli_detail'),
    
    # Service Level Objectives (SLOs)
    path('slos/', views.SLOView.as_view(), name='slos_list'),
    path('slos/<uuid:slo_id>/', views.SLOView.as_view(), name='slo_detail'),
    
    # Distributed tracing
    path('traces/', views.TraceView.as_view(), name='traces_list'),
    path('traces/<str:trace_id>/', views.TraceView.as_view(), name='trace_detail'),
    
    # Anomaly detection
    path('anomalies/', views.AnomalyView.as_view(), name='anomalies_list'),
    path('anomalies/<uuid:anomaly_id>/', views.AnomalyView.as_view(), name='anomaly_detail'),
    
    # AI insights
    path('insights/', views.InsightView.as_view(), name='insights_list'),
    path('insights/<uuid:insight_id>/', views.InsightView.as_view(), name='insight_detail'),
]