from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

@require_http_methods(["GET"])
def placeholder_view(request):
    """Placeholder view for sysmetrics app."""
    return JsonResponse({
        'app': 'sysmetrics',
        'status': 'placeholder',
        'message': 'sysmetrics endpoints will be implemented in future tasks'
    })
