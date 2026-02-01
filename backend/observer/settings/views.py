from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
import json
from typing import Dict, Any, List, Optional

from .models import (
    ConfigurationCategory,
    ConfigurationSetting,
    ConfigurationProfile,
    ConfigurationProfileSetting,
    ConfigurationDeployment,
    ConfigurationChangeLog,
    ConfigurationValidationRule
)


@require_http_methods(["GET"])
def get_categories(request):
    """Get all configuration categories."""
    try:
        categories = ConfigurationCategory.objects.filter(is_active=True)
        data = []
        
        for category in categories:
            settings_count = category.settings.filter(is_active=True).count()
            data.append({
                'id': str(category.id),
                'name': category.name,
                'display_name': category.display_name,
                'description': category.description,
                'icon': category.icon,
                'sort_order': category.sort_order,
                'settings_count': settings_count,
                'created_at': category.created_at.isoformat(),
                'updated_at': category.updated_at.isoformat(),
            })
        
        return JsonResponse({
            'success': True,
            'data': data,
            'count': len(data)
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def get_settings(request):
    """Get configuration settings, optionally filtered by category."""
    try:
        category_id = request.GET.get('category_id')
        include_sensitive = request.GET.get('include_sensitive', 'false').lower() == 'true'
        
        settings = ConfigurationSetting.objects.filter(is_active=True)
        
        if category_id:
            settings = settings.filter(category_id=category_id)
        
        data = []
        for setting in settings:
            setting_data = {
                'id': str(setting.id),
                'key': setting.key,
                'display_name': setting.display_name,
                'description': setting.description,
                'setting_type': setting.setting_type,
                'default_value': setting.default_value,
                'is_sensitive': setting.is_sensitive,
                'is_required': setting.is_required,
                'is_readonly': setting.is_readonly,
                'validation_rules': setting.validation_rules,
                'choices': setting.choices,
                'help_text': setting.help_text,
                'sort_order': setting.sort_order,
                'category': {
                    'id': str(setting.category.id),
                    'name': setting.category.name,
                    'display_name': setting.category.display_name,
                },
                'created_at': setting.created_at.isoformat(),
                'updated_at': setting.updated_at.isoformat(),
            }
            
            # Include current value, masking sensitive settings
            if setting.is_sensitive and not include_sensitive:
                setting_data['current_value'] = '***' if setting.current_value else None
            else:
                setting_data['current_value'] = setting.current_value
            
            data.append(setting_data)
        
        return JsonResponse({
            'success': True,
            'data': data,
            'count': len(data)
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def update_setting(request, setting_id):
    """Update a configuration setting value."""
    try:
        setting = get_object_or_404(ConfigurationSetting, id=setting_id, is_active=True)
        
        if setting.is_readonly:
            return JsonResponse({
                'success': False,
                'error': 'This setting is read-only'
            }, status=400)
        
        data = json.loads(request.body)
        new_value = data.get('value')
        change_reason = data.get('reason', '')
        
        # Store old value for logging
        old_value = setting.current_value
        
        # Validate and set new value
        try:
            setting.set_value(new_value, user=request.user)
        except ValidationError as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
        
        # Log the change with additional context
        change_log = ConfigurationChangeLog.objects.create(
            setting=setting,
            old_value=old_value,
            new_value=new_value,
            changed_by=request.user,
            change_reason=change_reason,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Setting {setting.key} updated successfully',
            'data': {
                'id': str(setting.id),
                'key': setting.key,
                'current_value': new_value if not setting.is_sensitive else '***',
                'updated_at': setting.updated_at.isoformat(),
                'change_log_id': str(change_log.id)
            }
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def get_profiles(request):
    """Get all configuration profiles."""
    try:
        profiles = ConfigurationProfile.objects.filter(is_active=True)
        data = []
        
        for profile in profiles:
            settings_count = profile.profile_settings.count()
            data.append({
                'id': str(profile.id),
                'name': profile.name,
                'display_name': profile.display_name,
                'description': profile.description,
                'is_default': profile.is_default,
                'is_system': profile.is_system,
                'settings_count': settings_count,
                'created_by': profile.created_by.email if profile.created_by else None,
                'created_at': profile.created_at.isoformat(),
                'updated_at': profile.updated_at.isoformat(),
            })
        
        return JsonResponse({
            'success': True,
            'data': data,
            'count': len(data)
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def create_profile(request):
    """Create a new configuration profile."""
    try:
        data = json.loads(request.body)
        
        profile = ConfigurationProfile.objects.create(
            name=data['name'],
            display_name=data['display_name'],
            description=data.get('description', ''),
            is_default=data.get('is_default', False),
            created_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Profile {profile.name} created successfully',
            'data': {
                'id': str(profile.id),
                'name': profile.name,
                'display_name': profile.display_name,
                'created_at': profile.created_at.isoformat()
            }
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def deploy_profile(request, profile_id):
    """Deploy a configuration profile."""
    try:
        profile = get_object_or_404(ConfigurationProfile, id=profile_id, is_active=True)
        data = json.loads(request.body)
        deployment_notes = data.get('notes', '')
        
        # Create deployment record
        deployment = ConfigurationDeployment.objects.create(
            profile=profile,
            deployed_by=request.user,
            deployment_notes=deployment_notes,
            started_at=timezone.now(),
            status='in_progress'
        )
        
        try:
            with transaction.atomic():
                # Apply all profile settings
                profile_settings = ConfigurationProfileSetting.objects.filter(
                    profile=profile
                ).select_related('setting')
                
                applied_count = 0
                for profile_setting in profile_settings:
                    setting = profile_setting.setting
                    if not setting.is_readonly:
                        old_value = setting.current_value
                        setting.current_value = profile_setting.value
                        setting.save()
                        
                        # Log the change
                        ConfigurationChangeLog.objects.create(
                            setting=setting,
                            old_value=old_value,
                            new_value=profile_setting.value,
                            changed_by=request.user,
                            change_reason=f'Profile deployment: {profile.name}',
                            ip_address=get_client_ip(request),
                            user_agent=request.META.get('HTTP_USER_AGENT', '')
                        )
                        applied_count += 1
                
                # Mark deployment as completed
                deployment.status = 'completed'
                deployment.completed_at = timezone.now()
                deployment.save()
                
                return JsonResponse({
                    'success': True,
                    'message': f'Profile {profile.name} deployed successfully',
                    'data': {
                        'deployment_id': str(deployment.id),
                        'applied_settings': applied_count,
                        'completed_at': deployment.completed_at.isoformat()
                    }
                })
        
        except Exception as e:
            # Mark deployment as failed
            deployment.status = 'failed'
            deployment.error_message = str(e)
            deployment.completed_at = timezone.now()
            deployment.save()
            raise e
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def get_change_history(request):
    """Get configuration change history."""
    try:
        setting_id = request.GET.get('setting_id')
        limit = int(request.GET.get('limit', 50))
        
        change_logs = ConfigurationChangeLog.objects.filter(is_active=True)
        
        if setting_id:
            change_logs = change_logs.filter(setting_id=setting_id)
        
        change_logs = change_logs.select_related('setting', 'changed_by')[:limit]
        
        data = []
        for log in change_logs:
            data.append({
                'id': str(log.id),
                'setting': {
                    'id': str(log.setting.id),
                    'key': log.setting.key,
                    'display_name': log.setting.display_name,
                },
                'old_value': log.old_value if not log.setting.is_sensitive else '***',
                'new_value': log.new_value if not log.setting.is_sensitive else '***',
                'changed_by': log.changed_by.email if log.changed_by else 'System',
                'change_reason': log.change_reason,
                'ip_address': log.ip_address,
                'created_at': log.created_at.isoformat(),
            })
        
        return JsonResponse({
            'success': True,
            'data': data,
            'count': len(data)
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def validate_settings(request):
    """Validate configuration settings."""
    try:
        data = json.loads(request.body)
        settings_to_validate = data.get('settings', [])
        
        validation_results = []
        
        for setting_data in settings_to_validate:
            setting_id = setting_data.get('id')
            value = setting_data.get('value')
            
            try:
                setting = ConfigurationSetting.objects.get(id=setting_id, is_active=True)
                setting._validate_value(value)
                
                validation_results.append({
                    'setting_id': setting_id,
                    'valid': True,
                    'message': 'Valid'
                })
            
            except ConfigurationSetting.DoesNotExist:
                validation_results.append({
                    'setting_id': setting_id,
                    'valid': False,
                    'message': 'Setting not found'
                })
            
            except ValidationError as e:
                validation_results.append({
                    'setting_id': setting_id,
                    'valid': False,
                    'message': str(e)
                })
        
        all_valid = all(result['valid'] for result in validation_results)
        
        return JsonResponse({
            'success': True,
            'all_valid': all_valid,
            'results': validation_results
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@require_http_methods(["GET"])
def health_check(request):
    """Health check endpoint for settings service."""
    try:
        # Check database connectivity
        categories_count = ConfigurationCategory.objects.count()
        settings_count = ConfigurationSetting.objects.count()
        
        return JsonResponse({
            'success': True,
            'service': 'settings',
            'status': 'healthy',
            'data': {
                'categories_count': categories_count,
                'settings_count': settings_count,
                'timestamp': timezone.now().isoformat()
            }
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'service': 'settings',
            'status': 'unhealthy',
            'error': str(e)
        }, status=500)
