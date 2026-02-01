from django.urls import path
from . import views

app_name = 'notification'

urlpatterns = [
    # Notification channels
    path('channels/', views.NotificationChannelView.as_view(), name='channels'),
    
    # Alert rules
    path('rules/', views.AlertRuleView.as_view(), name='alert_rules'),
    
    # Alerts
    path('alerts/', views.AlertView.as_view(), name='alerts'),
    path('alerts/<uuid:alert_id>/action/', views.AlertActionView.as_view(), name='alert_action'),
    
    # Alert evaluation
    path('evaluate/', views.trigger_alert_evaluation, name='evaluate_alerts'),
    
    # Statistics and monitoring
    path('statistics/', views.alert_statistics, name='statistics'),
    path('health/', views.health_check, name='health_check'),
]