import json
import logging
from typing import Dict, Any
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.db.models import Q, Count
from django.utils import timezone

from .models import (
    NotificationChannel, AlertRule, Alert, NotificationDelivery, 
    NotificationTemplate, AlertRuleNotificationChannel
)
from .services import NotificationService, AlertEvaluationService

logger = logging.getLogger('observer_eye.notification')


class NotificationChannelView(View):
    """API endpoints for managing notification channels"""
    
    @method_decorator(login_required)
    def get(self, request):
        """List notification channels for the current user"""
        try:
            channels = NotificationChannel.objects.filter(
                created_by=request.user,
                is_active=True
            ).order_by('-created_at')
            
            # Pagination
            page = request.GET.get('page', 1)
            per_page = min(int(request.GET.get('per_page', 20)), 100)
            paginator = Paginator(channels, per_page)
            page_obj = paginator.get_page(page)
            
            channels_data = []
            for channel in page_obj:
                channels_data.append({
                    'id': str(channel.id),
                    'name': channel.name,
                    'channel_type': channel.channel_type,
                    'is_enabled': channel.is_enabled,
                    'rate_limit_per_hour': channel.rate_limit_per_hour,
                    'created_at': channel.created_at.isoformat(),
                    'updated_at': channel.updated_at.isoformat(),
                })
            
            return JsonResponse({
                'channels': channels_data,
                'pagination': {
                    'page': page_obj.number,
                    'per_page': per_page,
                    'total_pages': paginator.num_pages,
                    'total_count': paginator.count,
                }
            })
            
        except Exception as e:
            logger.error(f"Error listing notification channels: {e}")
            return JsonResponse({'error': 'Failed to list channels'}, status=500)
    
    @method_decorator(login_required)
    @method_decorator(csrf_exempt)
    def post(self, request):
        """Create a new notification channel"""
        try:
            data = json.loads(request.body)
            
            # Validate required fields
            required_fields = ['name', 'channel_type', 'configuration']
            for field in required_fields:
                if field not in data:
                    return JsonResponse({'error': f'Missing required field: {field}'}, status=400)
            
            # Create channel
            channel = NotificationChannel.objects.create(
                name=data['name'],
                channel_type=data['channel_type'],
                configuration=data['configuration'],
                is_enabled=data.get('is_enabled', True),
                rate_limit_per_hour=data.get('rate_limit_per_hour', 100),
                max_retries=data.get('max_retries', 3),
                retry_delay_seconds=data.get('retry_delay_seconds', 300),
                created_by=request.user
            )
            
            return JsonResponse({
                'id': str(channel.id),
                'name': channel.name,
                'channel_type': channel.channel_type,
                'is_enabled': channel.is_enabled,
                'created_at': channel.created_at.isoformat(),
            }, status=201)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            logger.error(f"Error creating notification channel: {e}")
            return JsonResponse({'error': 'Failed to create channel'}, status=500)


class AlertRuleView(View):
    """API endpoints for managing alert rules"""
    
    @method_decorator(login_required)
    def get(self, request):
        """List alert rules for the current user"""
        try:
            rules = AlertRule.objects.filter(
                created_by=request.user,
                is_active=True
            ).order_by('-created_at')
            
            # Filtering
            severity = request.GET.get('severity')
            if severity:
                rules = rules.filter(severity=severity)
            
            enabled = request.GET.get('enabled')
            if enabled is not None:
                rules = rules.filter(is_enabled=enabled.lower() == 'true')
            
            # Pagination
            page = request.GET.get('page', 1)
            per_page = min(int(request.GET.get('per_page', 20)), 100)
            paginator = Paginator(rules, per_page)
            page_obj = paginator.get_page(page)
            
            rules_data = []
            for rule in page_obj:
                rules_data.append({
                    'id': str(rule.id),
                    'name': rule.name,
                    'description': rule.description,
                    'severity': rule.severity,
                    'is_enabled': rule.is_enabled,
                    'conditions': rule.conditions,
                    'threshold_value': rule.threshold_value,
                    'evaluation_window_minutes': rule.evaluation_window_minutes,
                    'created_at': rule.created_at.isoformat(),
                    'updated_at': rule.updated_at.isoformat(),
                })
            
            return JsonResponse({
                'rules': rules_data,
                'pagination': {
                    'page': page_obj.number,
                    'per_page': per_page,
                    'total_pages': paginator.num_pages,
                    'total_count': paginator.count,
                }
            })
            
        except Exception as e:
            logger.error(f"Error listing alert rules: {e}")
            return JsonResponse({'error': 'Failed to list alert rules'}, status=500)
    
    @method_decorator(login_required)
    @method_decorator(csrf_exempt)
    def post(self, request):
        """Create a new alert rule"""
        try:
            data = json.loads(request.body)
            
            # Validate required fields
            required_fields = ['name', 'conditions']
            for field in required_fields:
                if field not in data:
                    return JsonResponse({'error': f'Missing required field: {field}'}, status=400)
            
            # Create alert rule
            rule = AlertRule.objects.create(
                name=data['name'],
                description=data.get('description', ''),
                conditions=data['conditions'],
                threshold_value=data.get('threshold_value'),
                evaluation_window_minutes=data.get('evaluation_window_minutes', 5),
                severity=data.get('severity', 'medium'),
                tags=data.get('tags', {}),
                escalation_policy=data.get('escalation_policy', {}),
                notification_schedule=data.get('notification_schedule', {}),
                deduplication_window_minutes=data.get('deduplication_window_minutes', 60),
                deduplication_fields=data.get('deduplication_fields', []),
                is_enabled=data.get('is_enabled', True),
                created_by=request.user
            )
            
            # Add notification channels if provided
            channel_ids = data.get('notification_channel_ids', [])
            for channel_id in channel_ids:
                try:
                    channel = NotificationChannel.objects.get(
                        id=channel_id,
                        created_by=request.user,
                        is_active=True
                    )
                    AlertRuleNotificationChannel.objects.create(
                        alert_rule=rule,
                        notification_channel=channel
                    )
                except NotificationChannel.DoesNotExist:
                    logger.warning(f"Notification channel not found: {channel_id}")
            
            return JsonResponse({
                'id': str(rule.id),
                'name': rule.name,
                'severity': rule.severity,
                'is_enabled': rule.is_enabled,
                'created_at': rule.created_at.isoformat(),
            }, status=201)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error creating alert rule: {e}")
            return JsonResponse({'error': 'Failed to create alert rule'}, status=500)


class AlertView(View):
    """API endpoints for managing alerts"""
    
    @method_decorator(login_required)
    def get(self, request):
        """List alerts"""
        try:
            # Get alerts for rules created by the current user
            alerts = Alert.objects.filter(
                rule__created_by=request.user,
                rule__is_active=True
            ).select_related('rule', 'acknowledged_by', 'resolved_by').order_by('-triggered_at')
            
            # Filtering
            status = request.GET.get('status')
            if status:
                alerts = alerts.filter(status=status)
            
            severity = request.GET.get('severity')
            if severity:
                alerts = alerts.filter(rule__severity=severity)
            
            rule_id = request.GET.get('rule_id')
            if rule_id:
                alerts = alerts.filter(rule_id=rule_id)
            
            # Pagination
            page = request.GET.get('page', 1)
            per_page = min(int(request.GET.get('per_page', 20)), 100)
            paginator = Paginator(alerts, per_page)
            page_obj = paginator.get_page(page)
            
            alerts_data = []
            for alert in page_obj:
                alerts_data.append({
                    'id': str(alert.id),
                    'rule_id': str(alert.rule.id),
                    'rule_name': alert.rule.name,
                    'title': alert.title,
                    'message': alert.message,
                    'status': alert.status,
                    'severity': alert.rule.severity,
                    'fingerprint': alert.fingerprint,
                    'triggered_at': alert.triggered_at.isoformat(),
                    'acknowledged_at': alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                    'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None,
                    'acknowledged_by': alert.acknowledged_by.email if alert.acknowledged_by else None,
                    'resolved_by': alert.resolved_by.email if alert.resolved_by else None,
                    'escalation_level': alert.escalation_level,
                    'notification_count': alert.notification_count,
                    'metadata': alert.metadata,
                })
            
            return JsonResponse({
                'alerts': alerts_data,
                'pagination': {
                    'page': page_obj.number,
                    'per_page': per_page,
                    'total_pages': paginator.num_pages,
                    'total_count': paginator.count,
                }
            })
            
        except Exception as e:
            logger.error(f"Error listing alerts: {e}")
            return JsonResponse({'error': 'Failed to list alerts'}, status=500)


class AlertActionView(View):
    """API endpoints for alert actions (acknowledge, resolve)"""
    
    @method_decorator(login_required)
    @method_decorator(csrf_exempt)
    def post(self, request, alert_id):
        """Perform action on an alert"""
        try:
            data = json.loads(request.body)
            action = data.get('action')
            
            if not action:
                return JsonResponse({'error': 'Missing action parameter'}, status=400)
            
            # Get alert (ensure user has access)
            alert = get_object_or_404(
                Alert,
                id=alert_id,
                rule__created_by=request.user,
                rule__is_active=True
            )
            
            if action == 'acknowledge':
                alert.acknowledge(request.user)
                return JsonResponse({
                    'message': 'Alert acknowledged',
                    'status': alert.status,
                    'acknowledged_at': alert.acknowledged_at.isoformat(),
                    'acknowledged_by': alert.acknowledged_by.email
                })
            
            elif action == 'resolve':
                alert.resolve(request.user)
                return JsonResponse({
                    'message': 'Alert resolved',
                    'status': alert.status,
                    'resolved_at': alert.resolved_at.isoformat(),
                    'resolved_by': alert.resolved_by.email
                })
            
            elif action == 'suppress':
                alert.suppress()
                return JsonResponse({
                    'message': 'Alert suppressed',
                    'status': alert.status
                })
            
            else:
                return JsonResponse({'error': f'Unknown action: {action}'}, status=400)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error performing alert action: {e}")
            return JsonResponse({'error': 'Failed to perform action'}, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def trigger_alert_evaluation(request):
    """
    Endpoint for triggering alert evaluation with provided data.
    This would typically be called by monitoring systems or the middleware layer.
    """
    try:
        data = json.loads(request.body)
        
        # Validate that we have data to evaluate
        if not data:
            return JsonResponse({'error': 'No data provided for evaluation'}, status=400)
        
        # Initialize evaluation service
        evaluation_service = AlertEvaluationService()
        
        # Evaluate specific rule if rule_id is provided
        rule_id = data.get('rule_id')
        if rule_id:
            alert = evaluation_service.evaluate_single_rule(rule_id, data)
            if alert:
                return JsonResponse({
                    'message': 'Alert triggered',
                    'alert_id': str(alert.id),
                    'rule_name': alert.rule.name,
                    'severity': alert.rule.severity
                })
            else:
                return JsonResponse({'message': 'No alert triggered'})
        
        # Evaluate all rules
        triggered_alerts = evaluation_service.evaluate_rules(data)
        
        return JsonResponse({
            'message': f'{len(triggered_alerts)} alerts triggered',
            'triggered_alerts': [
                {
                    'alert_id': str(alert.id),
                    'rule_name': alert.rule.name,
                    'severity': alert.rule.severity,
                    'title': alert.title
                }
                for alert in triggered_alerts
            ]
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error in alert evaluation: {e}")
        return JsonResponse({'error': 'Failed to evaluate alerts'}, status=500)


@require_http_methods(["GET"])
def alert_statistics(request):
    """Get alert statistics and metrics"""
    try:
        # Get date range from query parameters
        from datetime import datetime, timedelta
        
        days = int(request.GET.get('days', 7))
        start_date = timezone.now() - timedelta(days=days)
        
        # Get alerts in date range
        alerts = Alert.objects.filter(
            triggered_at__gte=start_date,
            rule__is_active=True
        )
        
        # Calculate statistics
        total_alerts = alerts.count()
        alerts_by_status = alerts.values('status').annotate(count=Count('status'))
        alerts_by_severity = alerts.values('rule__severity').annotate(count=Count('rule__severity'))
        
        # Top alert rules
        top_rules = alerts.values('rule__name', 'rule__id').annotate(
            count=Count('rule__id')
        ).order_by('-count')[:10]
        
        return JsonResponse({
            'period_days': days,
            'total_alerts': total_alerts,
            'alerts_by_status': list(alerts_by_status),
            'alerts_by_severity': list(alerts_by_severity),
            'top_alert_rules': list(top_rules),
        })
        
    except Exception as e:
        logger.error(f"Error getting alert statistics: {e}")
        return JsonResponse({'error': 'Failed to get statistics'}, status=500)


@require_http_methods(["GET"])
def health_check(request):
    """Health check endpoint for notification service"""
    try:
        # Check database connectivity
        channel_count = NotificationChannel.objects.filter(is_active=True).count()
        rule_count = AlertRule.objects.filter(is_active=True, is_enabled=True).count()
        active_alerts = Alert.objects.filter(status='triggered').count()
        
        return JsonResponse({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'metrics': {
                'active_channels': channel_count,
                'active_rules': rule_count,
                'active_alerts': active_alerts,
            }
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=500)
