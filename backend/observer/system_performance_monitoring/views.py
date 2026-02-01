from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

@require_http_methods(["GET"])
def placeholder_view(request):
    """Placeholder view for system_performance_monitoring app."""
    return JsonResponse({
        'app': 'system_performance_monitoring',
        'status': 'placeholder',
        'message': 'system_performance_monitoring endpoints will be implemented in future tasks'
    })
