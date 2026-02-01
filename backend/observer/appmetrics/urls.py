from django.urls import path
from . import views

app_name = 'appmetrics'

urlpatterns = [
    path('instances/', views.instances_list, name='instances_list'),
    path('summary/', views.metrics_summary, name='metrics_summary'),
]