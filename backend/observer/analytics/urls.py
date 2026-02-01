from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    # Data sources
    path('data-sources/', views.data_sources_list, name='data_sources_list'),
    
    # Analytics data querying
    path('data/query/', views.analytics_data_query, name='analytics_data_query'),
    
    # Analytics summary and statistics
    path('summary/', views.analytics_summary, name='analytics_summary'),
    path('metrics/statistics/', views.metric_statistics, name='metric_statistics'),
]