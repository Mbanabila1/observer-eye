"""
Security Metrics views.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
import structlog

from .models import SecurityEvent, ThreatIntelligence, VulnerabilityAssessment, SecurityMetricData

logger = structlog.get_logger(__name__)


@require_http_methods(["GET"])
@login_required
def security_events_summary(request):
    """Get security events summary."""
    try:
        hours = int(request.GET.get('hours', 24))
        start_time = timezone.now() - timedelta(hours=hours)
        
        # Events by type and severity
        events_by_type = SecurityEvent.objects.filter(
            timestamp__gte=start_time,
            is_active=True
        ).values('event_type', 'severity').annotate(
            count=Count('id')
        ).order_by('event_type', 'severity')
        
        # Blocked vs allowed events
        blocked_events = SecurityEvent.objects.filter(
            timestamp__gte=start_time,
            is_blocked=True,
            is_active=True
        ).count()
        
        total_events = SecurityEvent.objects.filter(
            timestamp__gte=start_time,
            is_active=True
        ).count()
        
        return JsonResponse({
            'events_by_type': list(events_by_type),
            'blocked_events': blocked_events,
            'total_events': total_events,
            'block_rate': (blocked_events / total_events * 100) if total_events > 0 else 0
        })
        
    except Exception as e:
        logger.error("Failed to retrieve security events", error=str(e))
        return JsonResponse({'error': 'Failed to retrieve security events'}, status=500)


@require_http_methods(["GET"])
@login_required
def vulnerability_summary(request):
    """Get vulnerability assessment summary."""
    try:
        # Vulnerabilities by severity
        vulns_by_severity = VulnerabilityAssessment.objects.filter(
            is_active=True
        ).values('severity_level').annotate(
            count=Count('id'),
            patched_count=Count('id', filter=Q(is_patched=True))
        ).order_by('severity_level')
        
        # Critical unpatched vulnerabilities
        critical_unpatched = VulnerabilityAssessment.objects.filter(
            severity_level='critical',
            is_patched=False,
            is_active=True
        ).count()
        
        return JsonResponse({
            'vulnerabilities_by_severity': list(vulns_by_severity),
            'critical_unpatched': critical_unpatched
        })
        
    except Exception as e:
        logger.error("Failed to retrieve vulnerability summary", error=str(e))
        return JsonResponse({'error': 'Failed to retrieve vulnerability summary'}, status=500)