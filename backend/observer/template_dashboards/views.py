from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError, PermissionDenied
from django.db.models import Q, Count, F
import json
import logging

from .models import DashboardTemplate, Dashboard, TemplateShare, DashboardShare, DashboardWidget
from core.models import User

logger = logging.getLogger(__name__)


def json_response(data, status=200):
    """Helper function to create JSON responses"""
    return JsonResponse(data, status=status, safe=False)


def get_user_or_error(request):
    """Get authenticated user or return error response"""
    if not request.user.is_authenticated:
        return None, json_response({'error': 'Authentication required'}, 401)
    return request.user, None


def parse_json_body(request):
    """Parse JSON request body with error handling"""
    try:
        return json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        logger.error(f"JSON parsing error: {e}")
        return None


# Dashboard Template Views

@require_http_methods(["GET"])
def list_templates(request):
    """
    List dashboard templates with filtering and pagination.
    Supports public templates and user's own templates.
    
    Query parameters:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    - category: Filter by category
    - search: Search in name and description
    - public_only: Show only public templates (default: false)
    - my_templates: Show only user's templates (requires auth)
    """
    user, error_response = get_user_or_error(request)
    if error_response and request.GET.get('my_templates'):
        return error_response
    
    # Build queryset
    queryset = DashboardTemplate.objects.select_related('created_by').prefetch_related('shared_with')
    
    # Apply filters
    if request.GET.get('public_only') == 'true':
        queryset = queryset.filter(is_public=True)
    elif request.GET.get('my_templates') == 'true' and user:
        queryset = queryset.filter(
            Q(created_by=user) | Q(shared_with=user) | Q(is_public=True)
        ).distinct()
    elif user:
        # Show public templates and user's accessible templates
        queryset = queryset.filter(
            Q(is_public=True) | Q(created_by=user) | Q(shared_with=user)
        ).distinct()
    else:
        # Anonymous users see only public templates
        queryset = queryset.filter(is_public=True)
    
    # Search filter
    search = request.GET.get('search')
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) | Q(description__icontains=search)
        )
    
    # Category filter
    category = request.GET.get('category')
    if category:
        queryset = queryset.filter(category=category)
    
    # Pagination
    page = int(request.GET.get('page', 1))
    page_size = min(int(request.GET.get('page_size', 20)), 100)
    
    paginator = Paginator(queryset.order_by('-usage_count', '-created_at'), page_size)
    page_obj = paginator.get_page(page)
    
    # Serialize templates
    templates = []
    for template in page_obj:
        template_data = {
            'id': str(template.id),
            'name': template.name,
            'description': template.description,
            'version': template.version,
            'category': template.category,
            'tags': template.tags,
            'is_public': template.is_public,
            'is_system_template': template.is_system_template,
            'usage_count': template.usage_count,
            'created_by': {
                'id': str(template.created_by.id),
                'email': template.created_by.email,
            },
            'created_at': template.created_at.isoformat(),
            'updated_at': template.updated_at.isoformat(),
        }
        
        # Add access information for authenticated users
        if user:
            template_data['can_access'] = template.can_user_access(user)
            template_data['is_owner'] = template.created_by == user
        
        templates.append(template_data)
    
    return json_response({
        'templates': templates,
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        }
    })


@require_http_methods(["GET"])
def get_template(request, template_id):
    """Get detailed information about a specific template"""
    user, _ = get_user_or_error(request)
    
    try:
        template = DashboardTemplate.objects.select_related('created_by', 'parent_template').get(id=template_id)
    except DashboardTemplate.DoesNotExist:
        return json_response({'error': 'Template not found'}, 404)
    
    # Check access permissions
    if not template.can_user_access(user):
        return json_response({'error': 'Access denied'}, 403)
    
    # Get template versions
    versions = []
    for version in template.get_all_versions():
        versions.append({
            'id': str(version.id),
            'version': version.version,
            'created_at': version.created_at.isoformat(),
            'is_current': version.id == template.id,
        })
    
    template_data = {
        'id': str(template.id),
        'name': template.name,
        'description': template.description,
        'version': template.version,
        'category': template.category,
        'tags': template.tags,
        'layout_config': template.layout_config,
        'widget_configs': template.widget_configs,
        'is_public': template.is_public,
        'is_system_template': template.is_system_template,
        'usage_count': template.usage_count,
        'created_by': {
            'id': str(template.created_by.id),
            'email': template.created_by.email,
        },
        'parent_template': {
            'id': str(template.parent_template.id),
            'name': template.parent_template.name,
            'version': template.parent_template.version,
        } if template.parent_template else None,
        'versions': versions,
        'created_at': template.created_at.isoformat(),
        'updated_at': template.updated_at.isoformat(),
    }
    
    # Add access information for authenticated users
    if user:
        template_data['can_access'] = template.can_user_access(user)
        template_data['is_owner'] = template.created_by == user
        template_data['can_edit'] = template.created_by == user
    
    return json_response(template_data)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def create_template(request):
    """Create a new dashboard template"""
    user, error_response = get_user_or_error(request)
    if error_response:
        return error_response
    
    data = parse_json_body(request)
    if not data:
        return json_response({'error': 'Invalid JSON data'}, 400)
    
    try:
        with transaction.atomic():
            template = DashboardTemplate(
                name=data.get('name'),
                description=data.get('description', ''),
                layout_config=data.get('layout_config', {}),
                widget_configs=data.get('widget_configs', []),
                version=data.get('version', '1.0.0'),
                category=data.get('category', ''),
                tags=data.get('tags', []),
                is_public=data.get('is_public', False),
                created_by=user,
            )
            template.full_clean()
            template.save()
            
            logger.info(f"Template created: {template.name} by {user.email}")
            
            return json_response({
                'id': str(template.id),
                'name': template.name,
                'version': template.version,
                'message': 'Template created successfully'
            }, 201)
            
    except ValidationError as e:
        return json_response({'error': 'Validation error', 'details': e.message_dict}, 400)
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        return json_response({'error': 'Failed to create template'}, 500)


@csrf_exempt
@require_http_methods(["PUT"])
@login_required
def update_template(request, template_id):
    """Update an existing dashboard template"""
    user, error_response = get_user_or_error(request)
    if error_response:
        return error_response
    
    try:
        template = DashboardTemplate.objects.get(id=template_id)
    except DashboardTemplate.DoesNotExist:
        return json_response({'error': 'Template not found'}, 404)
    
    # Check permissions
    if template.created_by != user:
        return json_response({'error': 'Permission denied'}, 403)
    
    data = parse_json_body(request)
    if not data:
        return json_response({'error': 'Invalid JSON data'}, 400)
    
    try:
        with transaction.atomic():
            # Update fields
            if 'name' in data:
                template.name = data['name']
            if 'description' in data:
                template.description = data['description']
            if 'layout_config' in data:
                template.layout_config = data['layout_config']
            if 'widget_configs' in data:
                template.widget_configs = data['widget_configs']
            if 'category' in data:
                template.category = data['category']
            if 'tags' in data:
                template.tags = data['tags']
            if 'is_public' in data:
                template.is_public = data['is_public']
            
            template.full_clean()
            template.save()
            
            logger.info(f"Template updated: {template.name} by {user.email}")
            
            return json_response({
                'id': str(template.id),
                'message': 'Template updated successfully'
            })
            
    except ValidationError as e:
        return json_response({'error': 'Validation error', 'details': e.message_dict}, 400)
    except Exception as e:
        logger.error(f"Error updating template: {e}")
        return json_response({'error': 'Failed to update template'}, 500)


@csrf_exempt
@require_http_methods(["DELETE"])
@login_required
def delete_template(request, template_id):
    """Delete a dashboard template"""
    user, error_response = get_user_or_error(request)
    if error_response:
        return error_response
    
    try:
        template = DashboardTemplate.objects.get(id=template_id)
    except DashboardTemplate.DoesNotExist:
        return json_response({'error': 'Template not found'}, 404)
    
    # Check permissions
    if template.created_by != user and not template.is_system_template:
        return json_response({'error': 'Permission denied'}, 403)
    
    # Prevent deletion of system templates by non-superusers
    if template.is_system_template and not user.is_superuser:
        return json_response({'error': 'Cannot delete system templates'}, 403)
    
    try:
        template_name = template.name
        template.delete()
        
        logger.info(f"Template deleted: {template_name} by {user.email}")
        
        return json_response({'message': 'Template deleted successfully'})
        
    except Exception as e:
        logger.error(f"Error deleting template: {e}")
        return json_response({'error': 'Failed to delete template'}, 500)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def create_template_version(request, template_id):
    """Create a new version of an existing template"""
    user, error_response = get_user_or_error(request)
    if error_response:
        return error_response
    
    try:
        template = DashboardTemplate.objects.get(id=template_id)
    except DashboardTemplate.DoesNotExist:
        return json_response({'error': 'Template not found'}, 404)
    
    # Check permissions
    if template.created_by != user:
        return json_response({'error': 'Permission denied'}, 403)
    
    data = parse_json_body(request)
    if not data:
        return json_response({'error': 'Invalid JSON data'}, 400)
    
    version = data.get('version')
    if not version:
        return json_response({'error': 'Version is required'}, 400)
    
    try:
        with transaction.atomic():
            new_template = template.create_new_version(
                version=version,
                user=user,
                description=data.get('description'),
                layout_config=data.get('layout_config'),
                widget_configs=data.get('widget_configs'),
                is_public=data.get('is_public'),
                category=data.get('category'),
                tags=data.get('tags'),
            )
            
            logger.info(f"Template version created: {new_template.name} v{version} by {user.email}")
            
            return json_response({
                'id': str(new_template.id),
                'name': new_template.name,
                'version': new_template.version,
                'message': 'Template version created successfully'
            }, 201)
            
    except ValidationError as e:
        return json_response({'error': 'Validation error', 'details': e.message_dict}, 400)
    except Exception as e:
        logger.error(f"Error creating template version: {e}")
        return json_response({'error': 'Failed to create template version'}, 500)


# Dashboard Instance Views

@require_http_methods(["GET"])
@login_required
def list_dashboards(request):
    """List user's dashboards with filtering and pagination"""
    user, error_response = get_user_or_error(request)
    if error_response:
        return error_response
    
    # Build queryset - user's own dashboards and shared dashboards
    queryset = Dashboard.objects.filter(
        Q(owner=user) | Q(shared_with=user)
    ).select_related('owner', 'template').distinct()
    
    # Apply filters
    if request.GET.get('favorites_only') == 'true':
        queryset = queryset.filter(is_favorite=True)
    
    if request.GET.get('shared_only') == 'true':
        queryset = queryset.filter(shared_with=user)
    
    # Search filter
    search = request.GET.get('search')
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) | Q(description__icontains=search)
        )
    
    # Pagination
    page = int(request.GET.get('page', 1))
    page_size = min(int(request.GET.get('page_size', 20)), 100)
    
    paginator = Paginator(queryset.order_by('-last_accessed', '-created_at'), page_size)
    page_obj = paginator.get_page(page)
    
    # Serialize dashboards
    dashboards = []
    for dashboard in page_obj:
        dashboard_data = {
            'id': str(dashboard.id),
            'name': dashboard.name,
            'description': dashboard.description,
            'template': {
                'id': str(dashboard.template.id),
                'name': dashboard.template.name,
                'version': dashboard.template_version,
            } if dashboard.template else None,
            'is_shared': dashboard.is_shared,
            'is_favorite': dashboard.is_favorite,
            'is_default': dashboard.is_default,
            'access_count': dashboard.access_count,
            'last_accessed': dashboard.last_accessed.isoformat() if dashboard.last_accessed else None,
            'owner': {
                'id': str(dashboard.owner.id),
                'email': dashboard.owner.email,
            },
            'is_owner': dashboard.owner == user,
            'can_edit': dashboard.can_user_edit(user),
            'created_at': dashboard.created_at.isoformat(),
            'updated_at': dashboard.updated_at.isoformat(),
        }
        dashboards.append(dashboard_data)
    
    return json_response({
        'dashboards': dashboards,
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        }
    })


@require_http_methods(["GET"])
@login_required
def get_dashboard(request, dashboard_id):
    """Get detailed information about a specific dashboard"""
    user, error_response = get_user_or_error(request)
    if error_response:
        return error_response
    
    try:
        dashboard = Dashboard.objects.select_related('owner', 'template').prefetch_related('widgets').get(id=dashboard_id)
    except Dashboard.DoesNotExist:
        return json_response({'error': 'Dashboard not found'}, 404)
    
    # Check access permissions
    if not dashboard.can_user_access(user):
        return json_response({'error': 'Access denied'}, 403)
    
    # Increment access count
    dashboard.increment_access()
    
    # Get widgets
    widgets = []
    for widget in dashboard.widgets.all():
        widgets.append({
            'id': str(widget.id),
            'title': widget.title,
            'widget_type': widget.widget_type,
            'position_x': widget.position_x,
            'position_y': widget.position_y,
            'width': widget.width,
            'height': widget.height,
            'config': widget.config,
            'is_visible': widget.is_visible,
            'refresh_interval': widget.refresh_interval,
        })
    
    dashboard_data = {
        'id': str(dashboard.id),
        'name': dashboard.name,
        'description': dashboard.description,
        'configuration': dashboard.configuration,
        'template': {
            'id': str(dashboard.template.id),
            'name': dashboard.template.name,
            'version': dashboard.template_version,
        } if dashboard.template else None,
        'widgets': widgets,
        'is_shared': dashboard.is_shared,
        'is_favorite': dashboard.is_favorite,
        'is_default': dashboard.is_default,
        'access_count': dashboard.access_count,
        'last_accessed': dashboard.last_accessed.isoformat() if dashboard.last_accessed else None,
        'owner': {
            'id': str(dashboard.owner.id),
            'email': dashboard.owner.email,
        },
        'is_owner': dashboard.owner == user,
        'can_edit': dashboard.can_user_edit(user),
        'created_at': dashboard.created_at.isoformat(),
        'updated_at': dashboard.updated_at.isoformat(),
    }
    
    return json_response(dashboard_data)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def create_dashboard(request):
    """Create a new dashboard, optionally from a template"""
    user, error_response = get_user_or_error(request)
    if error_response:
        return error_response
    
    data = parse_json_body(request)
    if not data:
        return json_response({'error': 'Invalid JSON data'}, 400)
    
    try:
        with transaction.atomic():
            template = None
            template_id = data.get('template_id')
            
            if template_id:
                try:
                    template = DashboardTemplate.objects.get(id=template_id)
                    if not template.can_user_access(user):
                        return json_response({'error': 'Template access denied'}, 403)
                except DashboardTemplate.DoesNotExist:
                    return json_response({'error': 'Template not found'}, 404)
            
            if template:
                # Create dashboard from template
                dashboard = Dashboard()
                dashboard = dashboard.create_from_template(
                    template=template,
                    user=user,
                    name=data.get('name')
                )
            else:
                # Create dashboard from scratch
                dashboard = Dashboard(
                    name=data.get('name'),
                    description=data.get('description', ''),
                    configuration=data.get('configuration', {}),
                    owner=user,
                    is_favorite=data.get('is_favorite', False),
                    is_default=data.get('is_default', False),
                )
                dashboard.full_clean()
                dashboard.save()
            
            logger.info(f"Dashboard created: {dashboard.name} by {user.email}")
            
            return json_response({
                'id': str(dashboard.id),
                'name': dashboard.name,
                'message': 'Dashboard created successfully'
            }, 201)
            
    except ValidationError as e:
        return json_response({'error': 'Validation error', 'details': e.message_dict}, 400)
    except Exception as e:
        logger.error(f"Error creating dashboard: {e}")
        return json_response({'error': 'Failed to create dashboard'}, 500)


@csrf_exempt
@require_http_methods(["PUT"])
@login_required
def update_dashboard(request, dashboard_id):
    """Update an existing dashboard"""
    user, error_response = get_user_or_error(request)
    if error_response:
        return error_response
    
    try:
        dashboard = Dashboard.objects.get(id=dashboard_id)
    except Dashboard.DoesNotExist:
        return json_response({'error': 'Dashboard not found'}, 404)
    
    # Check permissions
    if not dashboard.can_user_edit(user):
        return json_response({'error': 'Permission denied'}, 403)
    
    data = parse_json_body(request)
    if not data:
        return json_response({'error': 'Invalid JSON data'}, 400)
    
    try:
        with transaction.atomic():
            # Update fields
            if 'name' in data:
                dashboard.name = data['name']
            if 'description' in data:
                dashboard.description = data['description']
            if 'configuration' in data:
                dashboard.configuration = data['configuration']
            if 'is_favorite' in data:
                dashboard.is_favorite = data['is_favorite']
            if 'is_default' in data:
                dashboard.is_default = data['is_default']
            
            dashboard.full_clean()
            dashboard.save()
            
            logger.info(f"Dashboard updated: {dashboard.name} by {user.email}")
            
            return json_response({
                'id': str(dashboard.id),
                'message': 'Dashboard updated successfully'
            })
            
    except ValidationError as e:
        return json_response({'error': 'Validation error', 'details': e.message_dict}, 400)
    except Exception as e:
        logger.error(f"Error updating dashboard: {e}")
        return json_response({'error': 'Failed to update dashboard'}, 500)


@csrf_exempt
@require_http_methods(["DELETE"])
@login_required
def delete_dashboard(request, dashboard_id):
    """Delete a dashboard"""
    user, error_response = get_user_or_error(request)
    if error_response:
        return error_response
    
    try:
        dashboard = Dashboard.objects.get(id=dashboard_id)
    except Dashboard.DoesNotExist:
        return json_response({'error': 'Dashboard not found'}, 404)
    
    # Check permissions - only owner can delete
    if dashboard.owner != user:
        return json_response({'error': 'Permission denied'}, 403)
    
    try:
        dashboard_name = dashboard.name
        dashboard.delete()
        
        logger.info(f"Dashboard deleted: {dashboard_name} by {user.email}")
        
        return json_response({'message': 'Dashboard deleted successfully'})
        
    except Exception as e:
        logger.error(f"Error deleting dashboard: {e}")
        return json_response({'error': 'Failed to delete dashboard'}, 500)


# Sharing Views

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def share_template(request, template_id):
    """Share a template with another user"""
    user, error_response = get_user_or_error(request)
    if error_response:
        return error_response
    
    try:
        template = DashboardTemplate.objects.get(id=template_id)
    except DashboardTemplate.DoesNotExist:
        return json_response({'error': 'Template not found'}, 404)
    
    # Check permissions
    if template.created_by != user:
        return json_response({'error': 'Permission denied'}, 403)
    
    data = parse_json_body(request)
    if not data:
        return json_response({'error': 'Invalid JSON data'}, 400)
    
    user_email = data.get('user_email')
    permission_level = data.get('permission_level', 'view')
    
    if not user_email:
        return json_response({'error': 'User email is required'}, 400)
    
    try:
        target_user = User.objects.get(email=user_email)
    except User.DoesNotExist:
        return json_response({'error': 'User not found'}, 404)
    
    try:
        share = template.share_with_user(target_user, permission_level, shared_by=user)
        
        logger.info(f"Template shared: {template.name} with {user_email} by {user.email}")
        
        return json_response({
            'message': f'Template shared with {user_email}',
            'permission_level': permission_level
        })
        
    except Exception as e:
        logger.error(f"Error sharing template: {e}")
        return json_response({'error': 'Failed to share template'}, 500)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def share_dashboard(request, dashboard_id):
    """Share a dashboard with another user"""
    user, error_response = get_user_or_error(request)
    if error_response:
        return error_response
    
    try:
        dashboard = Dashboard.objects.get(id=dashboard_id)
    except Dashboard.DoesNotExist:
        return json_response({'error': 'Dashboard not found'}, 404)
    
    # Check permissions
    if dashboard.owner != user:
        return json_response({'error': 'Permission denied'}, 403)
    
    data = parse_json_body(request)
    if not data:
        return json_response({'error': 'Invalid JSON data'}, 400)
    
    user_email = data.get('user_email')
    permission_level = data.get('permission_level', 'view')
    
    if not user_email:
        return json_response({'error': 'User email is required'}, 400)
    
    try:
        target_user = User.objects.get(email=user_email)
    except User.DoesNotExist:
        return json_response({'error': 'User not found'}, 404)
    
    try:
        share = dashboard.share_with_user(target_user, permission_level, shared_by=user)
        
        logger.info(f"Dashboard shared: {dashboard.name} with {user_email} by {user.email}")
        
        return json_response({
            'message': f'Dashboard shared with {user_email}',
            'permission_level': permission_level
        })
        
    except Exception as e:
        logger.error(f"Error sharing dashboard: {e}")
        return json_response({'error': 'Failed to share dashboard'}, 500)


# Statistics and Analytics Views

@require_http_methods(["GET"])
def get_template_categories(request):
    """Get available template categories with counts"""
    categories = DashboardTemplate.objects.values('category').annotate(
        count=Count('id')
    ).filter(
        Q(is_public=True) | Q(created_by=request.user) if request.user.is_authenticated else Q(is_public=True)
    ).order_by('category')
    
    category_data = []
    for cat in categories:
        if cat['category']:  # Skip empty categories
            category_data.append({
                'category': cat['category'],
                'count': cat['count'],
                'display_name': dict(DashboardTemplate._meta.get_field('category').choices).get(
                    cat['category'], cat['category'].title()
                )
            })
    
    return json_response({'categories': category_data})


@require_http_methods(["GET"])
@login_required
def get_dashboard_stats(request):
    """Get dashboard usage statistics for the user"""
    user, error_response = get_user_or_error(request)
    if error_response:
        return error_response
    
    stats = {
        'total_dashboards': Dashboard.objects.filter(owner=user).count(),
        'shared_dashboards': Dashboard.objects.filter(shared_with=user).count(),
        'favorite_dashboards': Dashboard.objects.filter(owner=user, is_favorite=True).count(),
        'templates_created': DashboardTemplate.objects.filter(created_by=user).count(),
        'templates_used': Dashboard.objects.filter(owner=user, template__isnull=False).count(),
        'most_accessed_dashboard': None,
    }
    
    # Get most accessed dashboard
    most_accessed = Dashboard.objects.filter(owner=user).order_by('-access_count').first()
    if most_accessed:
        stats['most_accessed_dashboard'] = {
            'id': str(most_accessed.id),
            'name': most_accessed.name,
            'access_count': most_accessed.access_count,
        }
    
    return json_response(stats)