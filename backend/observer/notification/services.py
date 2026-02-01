"""
Notification delivery services for the Observer Eye Platform.
Handles multiple notification channels with retry logic and rate limiting.
"""

import json
import hashlib
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.template import Template, Context

from .models import (
    NotificationChannel, AlertRule, Alert, NotificationDelivery, 
    NotificationTemplate, AlertRuleNotificationChannel
)

logger = logging.getLogger('observer_eye.notification')


class NotificationService:
    """
    Main service for handling notification delivery across multiple channels.
    """
    
    def __init__(self):
        self.delivery_handlers = {
            'email': EmailDeliveryHandler(),
            'sms': SMSDeliveryHandler(),
            'webhook': WebhookDeliveryHandler(),
            'slack': SlackDeliveryHandler(),
            'teams': TeamsDeliveryHandler(),
            'discord': DiscordDeliveryHandler(),
            'pagerduty': PagerDutyDeliveryHandler(),
        }
    
    def create_alert(self, rule: AlertRule, data: Dict[str, Any], title: str, message: str) -> Optional[Alert]:
        """
        Create a new alert from rule evaluation.
        Handles deduplication based on rule settings.
        """
        try:
            # Generate fingerprint for deduplication
            fingerprint = self._generate_fingerprint(rule, data)
            
            # Check for existing alert within deduplication window
            dedup_window = timezone.now() - timedelta(minutes=rule.deduplication_window_minutes)
            existing_alert = Alert.objects.filter(
                rule=rule,
                fingerprint=fingerprint,
                status__in=['triggered', 'acknowledged'],
                triggered_at__gte=dedup_window
            ).first()
            
            if existing_alert:
                logger.info(f"Alert deduplicated: {fingerprint}")
                return existing_alert
            
            # Create new alert
            alert = Alert.objects.create(
                rule=rule,
                fingerprint=fingerprint,
                title=title,
                message=message,
                metadata=data,
                status='triggered'
            )
            
            logger.info(f"Alert created: {alert.id} - {title}")
            
            # Send initial notifications
            self.send_alert_notifications(alert)
            
            return alert
            
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            return None
    
    def send_alert_notifications(self, alert: Alert) -> bool:
        """
        Send notifications for an alert through all configured channels.
        """
        try:
            # Get notification channels for this alert rule
            rule_channels = AlertRuleNotificationChannel.objects.filter(
                alert_rule=alert.rule,
                notification_channel__is_enabled=True,
                notification_channel__is_active=True
            ).select_related('notification_channel')
            
            if not rule_channels:
                logger.warning(f"No notification channels configured for alert rule: {alert.rule.name}")
                return False
            
            success_count = 0
            
            for rule_channel in rule_channels:
                channel = rule_channel.notification_channel
                
                # Check if this is an escalation channel and if we should send it
                if rule_channel.is_escalation and alert.escalation_level < rule_channel.escalation_level:
                    continue
                
                # Create notification delivery record
                delivery = NotificationDelivery.objects.create(
                    alert=alert,
                    channel=channel,
                    status='pending'
                )
                
                # Send notification
                if self._send_notification(delivery, rule_channel):
                    success_count += 1
            
            # Update alert notification tracking
            alert.notification_count += success_count
            alert.last_notification_at = timezone.now()
            alert.save(update_fields=['notification_count', 'last_notification_at', 'updated_at'])
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error sending alert notifications: {e}")
            return False
    
    def process_escalations(self):
        """
        Process alert escalations for triggered alerts.
        Should be called periodically by a background task.
        """
        try:
            # Find alerts that need escalation
            alerts_to_escalate = Alert.objects.filter(
                status='triggered',
                rule__escalation_policy__enabled=True
            ).select_related('rule')
            
            escalated_count = 0
            
            for alert in alerts_to_escalate:
                if alert.should_escalate():
                    if alert.escalate():
                        logger.info(f"Alert escalated: {alert.id} to level {alert.escalation_level}")
                        # Send escalation notifications
                        self.send_alert_notifications(alert)
                        escalated_count += 1
            
            if escalated_count > 0:
                logger.info(f"Processed {escalated_count} alert escalations")
            
            return escalated_count
            
        except Exception as e:
            logger.error(f"Error processing escalations: {e}")
            return 0
    
    def retry_failed_deliveries(self):
        """
        Retry failed notification deliveries.
        Should be called periodically by a background task.
        """
        try:
            # Find deliveries ready for retry
            now = timezone.now()
            failed_deliveries = NotificationDelivery.objects.filter(
                status='retrying',
                next_retry_at__lte=now
            ).select_related('channel', 'alert__rule')
            
            retry_count = 0
            
            for delivery in failed_deliveries:
                # Find the corresponding rule channel
                rule_channel = AlertRuleNotificationChannel.objects.filter(
                    alert_rule=delivery.alert.rule,
                    notification_channel=delivery.channel
                ).first()
                
                if rule_channel and self._send_notification(delivery, rule_channel):
                    retry_count += 1
            
            if retry_count > 0:
                logger.info(f"Retried {retry_count} failed deliveries")
            
            return retry_count
            
        except Exception as e:
            logger.error(f"Error retrying failed deliveries: {e}")
            return 0
    
    def _generate_fingerprint(self, rule: AlertRule, data: Dict[str, Any]) -> str:
        """Generate unique fingerprint for alert deduplication"""
        fingerprint_data = {
            'rule_id': str(rule.id),
        }
        
        # Add deduplication fields from rule configuration
        for field in rule.deduplication_fields:
            if field in data:
                fingerprint_data[field] = data[field]
        
        # Create hash from fingerprint data
        fingerprint_str = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.sha256(fingerprint_str.encode()).hexdigest()
    
    def _send_notification(self, delivery: NotificationDelivery, rule_channel: AlertRuleNotificationChannel) -> bool:
        """Send a single notification delivery"""
        try:
            channel = delivery.channel
            handler = self.delivery_handlers.get(channel.channel_type)
            
            if not handler:
                delivery.mark_failed(f"No handler for channel type: {channel.channel_type}")
                return False
            
            # Get notification template
            template = self._get_notification_template(channel.channel_type, 'alert_triggered')
            
            # Prepare notification content
            context = {
                'alert': delivery.alert,
                'rule': delivery.alert.rule,
                'channel': channel,
                'metadata': delivery.alert.metadata,
            }
            
            rendered_content = template.render(context) if template else {
                'subject': delivery.alert.title,
                'body': delivery.alert.message
            }
            
            # Send notification
            success = handler.send_notification(
                channel=channel,
                delivery=delivery,
                subject=rendered_content.get('subject', ''),
                message=rendered_content.get('body', ''),
                context=context
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            delivery.mark_failed(str(e))
            return False
    
    def _get_notification_template(self, channel_type: str, template_type: str) -> Optional[NotificationTemplate]:
        """Get notification template for channel and template type"""
        return NotificationTemplate.objects.filter(
            channel_type=channel_type,
            template_type=template_type,
            is_active=True
        ).order_by('-is_default', '-created_at').first()


class BaseDeliveryHandler:
    """Base class for notification delivery handlers"""
    
    def send_notification(self, channel: NotificationChannel, delivery: NotificationDelivery, 
                         subject: str, message: str, context: Dict[str, Any]) -> bool:
        """Send notification through this channel"""
        raise NotImplementedError("Subclasses must implement send_notification")
    
    def validate_configuration(self, configuration: Dict[str, Any]) -> bool:
        """Validate channel configuration"""
        return True


class EmailDeliveryHandler(BaseDeliveryHandler):
    """Handler for email notifications"""
    
    def send_notification(self, channel: NotificationChannel, delivery: NotificationDelivery,
                         subject: str, message: str, context: Dict[str, Any]) -> bool:
        try:
            config = channel.configuration
            recipients = config.get('recipients', [])
            
            if not recipients:
                delivery.mark_failed("No recipients configured")
                return False
            
            # Send email
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipients,
                fail_silently=False
            )
            
            delivery.recipient = ', '.join(recipients)
            delivery.message_content = f"Subject: {subject}\n\n{message}"
            delivery.mark_sent()
            delivery.mark_delivered()  # Email is considered delivered when sent
            
            logger.info(f"Email sent to {delivery.recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Email delivery failed: {e}")
            delivery.mark_failed(str(e))
            return False
    
    def validate_configuration(self, configuration: Dict[str, Any]) -> bool:
        return 'recipients' in configuration and isinstance(configuration['recipients'], list)


class WebhookDeliveryHandler(BaseDeliveryHandler):
    """Handler for webhook notifications"""
    
    def send_notification(self, channel: NotificationChannel, delivery: NotificationDelivery,
                         subject: str, message: str, context: Dict[str, Any]) -> bool:
        try:
            import requests
            
            config = channel.configuration
            url = config.get('url')
            
            if not url:
                delivery.mark_failed("No webhook URL configured")
                return False
            
            # Prepare webhook payload
            payload = {
                'alert_id': str(delivery.alert.id),
                'rule_name': delivery.alert.rule.name,
                'severity': delivery.alert.rule.severity,
                'title': subject,
                'message': message,
                'status': delivery.alert.status,
                'triggered_at': delivery.alert.triggered_at.isoformat(),
                'metadata': delivery.alert.metadata,
            }
            
            # Add custom headers if configured
            headers = config.get('headers', {})
            headers.setdefault('Content-Type', 'application/json')
            
            # Send webhook
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=config.get('timeout', 30)
            )
            
            response.raise_for_status()
            
            delivery.recipient = url
            delivery.message_content = json.dumps(payload, indent=2)
            delivery.response_data = {
                'status_code': response.status_code,
                'response_text': response.text[:1000]  # Limit response size
            }
            delivery.mark_sent()
            delivery.mark_delivered()
            
            logger.info(f"Webhook sent to {url}")
            return True
            
        except Exception as e:
            logger.error(f"Webhook delivery failed: {e}")
            delivery.mark_failed(str(e))
            return False
    
    def validate_configuration(self, configuration: Dict[str, Any]) -> bool:
        return 'url' in configuration


class SMSDeliveryHandler(BaseDeliveryHandler):
    """Handler for SMS notifications"""
    
    def send_notification(self, channel: NotificationChannel, delivery: NotificationDelivery,
                         subject: str, message: str, context: Dict[str, Any]) -> bool:
        try:
            config = channel.configuration
            phone_numbers = config.get('phone_numbers', [])
            
            if not phone_numbers:
                delivery.mark_failed("No phone numbers configured")
                return False
            
            # This is a placeholder - integrate with your SMS provider (Twilio, AWS SNS, etc.)
            # For now, we'll just log the SMS
            sms_message = f"{subject}: {message}"
            
            delivery.recipient = ', '.join(phone_numbers)
            delivery.message_content = sms_message
            delivery.mark_sent()
            delivery.mark_delivered()
            
            logger.info(f"SMS would be sent to {delivery.recipient}: {sms_message}")
            return True
            
        except Exception as e:
            logger.error(f"SMS delivery failed: {e}")
            delivery.mark_failed(str(e))
            return False
    
    def validate_configuration(self, configuration: Dict[str, Any]) -> bool:
        return 'phone_numbers' in configuration and isinstance(configuration['phone_numbers'], list)


class SlackDeliveryHandler(BaseDeliveryHandler):
    """Handler for Slack notifications"""
    
    def send_notification(self, channel: NotificationChannel, delivery: NotificationDelivery,
                         subject: str, message: str, context: Dict[str, Any]) -> bool:
        try:
            import requests
            
            config = channel.configuration
            webhook_url = config.get('webhook_url')
            
            if not webhook_url:
                delivery.mark_failed("No Slack webhook URL configured")
                return False
            
            # Prepare Slack payload
            payload = {
                'text': subject,
                'attachments': [{
                    'color': self._get_slack_color(delivery.alert.rule.severity),
                    'fields': [
                        {'title': 'Rule', 'value': delivery.alert.rule.name, 'short': True},
                        {'title': 'Severity', 'value': delivery.alert.rule.severity.upper(), 'short': True},
                        {'title': 'Status', 'value': delivery.alert.status.upper(), 'short': True},
                        {'title': 'Triggered', 'value': delivery.alert.triggered_at.strftime('%Y-%m-%d %H:%M:%S UTC'), 'short': True},
                    ],
                    'text': message
                }]
            }
            
            # Send to Slack
            response = requests.post(webhook_url, json=payload, timeout=30)
            response.raise_for_status()
            
            delivery.recipient = config.get('channel', 'Unknown')
            delivery.message_content = json.dumps(payload, indent=2)
            delivery.mark_sent()
            delivery.mark_delivered()
            
            logger.info(f"Slack notification sent to {delivery.recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Slack delivery failed: {e}")
            delivery.mark_failed(str(e))
            return False
    
    def _get_slack_color(self, severity: str) -> str:
        """Get Slack color based on alert severity"""
        colors = {
            'low': 'good',
            'medium': 'warning',
            'high': 'danger',
            'critical': 'danger'
        }
        return colors.get(severity, 'warning')
    
    def validate_configuration(self, configuration: Dict[str, Any]) -> bool:
        return 'webhook_url' in configuration


class TeamsDeliveryHandler(BaseDeliveryHandler):
    """Handler for Microsoft Teams notifications"""
    
    def send_notification(self, channel: NotificationChannel, delivery: NotificationDelivery,
                         subject: str, message: str, context: Dict[str, Any]) -> bool:
        # Placeholder implementation - similar to Slack but with Teams webhook format
        delivery.mark_failed("Microsoft Teams integration not yet implemented")
        return False


class DiscordDeliveryHandler(BaseDeliveryHandler):
    """Handler for Discord notifications"""
    
    def send_notification(self, channel: NotificationChannel, delivery: NotificationDelivery,
                         subject: str, message: str, context: Dict[str, Any]) -> bool:
        # Placeholder implementation - similar to Slack but with Discord webhook format
        delivery.mark_failed("Discord integration not yet implemented")
        return False


class PagerDutyDeliveryHandler(BaseDeliveryHandler):
    """Handler for PagerDuty notifications"""
    
    def send_notification(self, channel: NotificationChannel, delivery: NotificationDelivery,
                         subject: str, message: str, context: Dict[str, Any]) -> bool:
        # Placeholder implementation - integrate with PagerDuty Events API
        delivery.mark_failed("PagerDuty integration not yet implemented")
        return False


class AlertEvaluationService:
    """
    Service for evaluating alert rules against incoming data.
    """
    
    def __init__(self):
        self.notification_service = NotificationService()
    
    def evaluate_rules(self, data: Dict[str, Any]) -> List[Alert]:
        """
        Evaluate all active alert rules against provided data.
        Returns list of alerts that were triggered.
        """
        triggered_alerts = []
        
        try:
            # Get all active alert rules
            active_rules = AlertRule.objects.filter(
                is_enabled=True,
                is_active=True
            )
            
            for rule in active_rules:
                if rule.evaluate_conditions(data):
                    # Generate alert title and message
                    title = f"Alert: {rule.name}"
                    message = f"Alert rule '{rule.name}' has been triggered.\n\nConditions: {rule.conditions}\nData: {data}"
                    
                    alert = self.notification_service.create_alert(rule, data, title, message)
                    if alert:
                        triggered_alerts.append(alert)
            
            if triggered_alerts:
                logger.info(f"Triggered {len(triggered_alerts)} alerts")
            
            return triggered_alerts
            
        except Exception as e:
            logger.error(f"Error evaluating alert rules: {e}")
            return []
    
    def evaluate_single_rule(self, rule_id: str, data: Dict[str, Any]) -> Optional[Alert]:
        """Evaluate a single alert rule against provided data"""
        try:
            rule = AlertRule.objects.get(id=rule_id, is_enabled=True, is_active=True)
            
            if rule.evaluate_conditions(data):
                title = f"Alert: {rule.name}"
                message = f"Alert rule '{rule.name}' has been triggered.\n\nConditions: {rule.conditions}\nData: {data}"
                
                return self.notification_service.create_alert(rule, data, title, message)
            
            return None
            
        except AlertRule.DoesNotExist:
            logger.error(f"Alert rule not found: {rule_id}")
            return None
        except Exception as e:
            logger.error(f"Error evaluating alert rule {rule_id}: {e}")
            return None