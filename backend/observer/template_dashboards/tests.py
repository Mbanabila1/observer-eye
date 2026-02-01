import json
import uuid
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from unittest.mock import patch

from .models import DashboardTemplate, Dashboard, TemplateShare, DashboardShare, DashboardWidget

User = get_user_model()


class DashboardTemplateModelTest(TestCase):
    """Test cases for DashboardTemplate model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            email='other@example.com',
            username='otheruser',
            password='testpass123'
        )
    
    def test_create_dashboard_template(self):
        """Test creating a dashboard template with valid data"""
        template = DashboardTemplate.objects.create(
            name='Test Template',
            description='A test template',
            layout_config={'grid_columns': 12, 'grid_rows': 8},
            widget_configs=[
                {
                    'type': 'chart',
                    'position': {'x': 0, 'y': 0},
                    'config': {'chart_type': 'line'}
                }
            ],
            version='1.0.0',
            category='monitoring',
            tags=['test', 'monitoring'],
            created_by=self.user
        )
        
        self.assertEqual(template.name, 'Test Template')
        self.assertEqual(template.version, '1.0.0')
        self.assertEqual(template.created_by, self.user)
        self.assertFalse(template.is_public)
        self.assertEqual(template.usage_count, 0)
    
    def test_template_validation_missing_layout_fields(self):
        """Test template validation fails with missing layout fields"""
        template = DashboardTemplate(
            name='Invalid Template',
            layout_config={'grid_columns': 12},  # Missing grid_rows
            widget_configs=[],
            created_by=self.user
        )
        
        with self.assertRaises(ValidationError):
            template.full_clean()
    
    def test_template_validation_invalid_widget_config(self):
        """Test template validation fails with invalid widget config"""
        template = DashboardTemplate(
            name='Invalid Template',
            layout_config={'grid_columns': 12, 'grid_rows': 8},
            widget_configs=[
                {
                    'type': 'chart',
                    # Missing position and config
                }
            ],
            created_by=self.user
        )
        
        with self.assertRaises(ValidationError):
            template.full_clean()
    
    def test_template_validation_invalid_version_format(self):
        """Test template validation fails with invalid version format"""
        template = DashboardTemplate(
            name='Invalid Template',
            layout_config={'grid_columns': 12, 'grid_rows': 8},
            widget_configs=[],
            version='invalid-version',
            created_by=self.user
        )
        
        with self.assertRaises(ValidationError):
            template.full_clean()
    
    def test_increment_usage(self):
        """Test incrementing template usage count"""
        template = DashboardTemplate.objects.create(
            name='Test Template',
            layout_config={'grid_columns': 12, 'grid_rows': 8},
            widget_configs=[],
            created_by=self.user
        )
        
        initial_count = template.usage_count
        template.increment_usage()
        template.refresh_from_db()
        
        self.assertEqual(template.usage_count, initial_count + 1)
    
    def test_create_new_version(self):
        """Test creating a new version of a template"""
        original_template = DashboardTemplate.objects.create(
            name='Original Template',
            layout_config={'grid_columns': 12, 'grid_rows': 8},
            widget_configs=[],
            version='1.0.0',
            created_by=self.user
        )
        
        new_template = original_template.create_new_version(
            version='1.1.0',
            user=self.user,
            description='Updated template'
        )
        
        self.assertEqual(new_template.name, 'Original Template')
        self.assertEqual(new_template.version, '1.1.0')
        self.assertEqual(new_template.description, 'Updated template')
        self.assertEqual(new_template.parent_template, original_template)
    
    def test_can_user_access_public_template(self):
        """Test user access to public templates"""
        template = DashboardTemplate.objects.create(
            name='Public Template',
            layout_config={'grid_columns': 12, 'grid_rows': 8},
            widget_configs=[],
            is_public=True,
            created_by=self.user
        )
        
        self.assertTrue(template.can_user_access(self.other_user))
        self.assertTrue(template.can_user_access(None))  # Anonymous user
    
    def test_can_user_access_private_template(self):
        """Test user access to private templates"""
        template = DashboardTemplate.objects.create(
            name='Private Template',
            layout_config={'grid_columns': 12, 'grid_rows': 8},
            widget_configs=[],
            is_public=False,
            created_by=self.user
        )
        
        # Owner can access
        self.assertTrue(template.can_user_access(self.user))
        
        # Other users cannot access
        self.assertFalse(template.can_user_access(self.other_user))
        self.assertFalse(template.can_user_access(None))
    
    def test_share_template_with_user(self):
        """Test sharing a template with another user"""
        template = DashboardTemplate.objects.create(
            name='Shared Template',
            layout_config={'grid_columns': 12, 'grid_rows': 8},
            widget_configs=[],
            created_by=self.user
        )
        
        share = template.share_with_user(self.other_user, 'edit')
        
        self.assertEqual(share.template, template)
        self.assertEqual(share.user, self.other_user)
        self.assertEqual(share.permission_level, 'edit')
        self.assertTrue(template.can_user_access(self.other_user))


class DashboardModelTest(TestCase):
    """Test cases for Dashboard model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            email='other@example.com',
            username='otheruser',
            password='testpass123'
        )
        self.template = DashboardTemplate.objects.create(
            name='Test Template',
            layout_config={'grid_columns': 12, 'grid_rows': 8},
            widget_configs=[
                {
                    'type': 'chart',
                    'position': {'x': 0, 'y': 0},
                    'config': {'chart_type': 'line'}
                }
            ],
            version='1.0.0',
            created_by=self.user
        )
    
    def test_create_dashboard(self):
        """Test creating a dashboard"""
        dashboard = Dashboard.objects.create(
            name='Test Dashboard',
            description='A test dashboard',
            configuration={'layout': {}, 'widgets': []},
            owner=self.user
        )
        
        self.assertEqual(dashboard.name, 'Test Dashboard')
        self.assertEqual(dashboard.owner, self.user)
        self.assertFalse(dashboard.is_shared)
        self.assertFalse(dashboard.is_favorite)
        self.assertEqual(dashboard.access_count, 0)
    
    def test_dashboard_validation_missing_config_fields(self):
        """Test dashboard validation fails with missing config fields"""
        dashboard = Dashboard(
            name='Invalid Dashboard',
            configuration={'layout': {}},  # Missing widgets
            owner=self.user
        )
        
        with self.assertRaises(ValidationError):
            dashboard.full_clean()
    
    def test_dashboard_validation_multiple_defaults(self):
        """Test dashboard validation prevents multiple default dashboards"""
        # Create first default dashboard
        Dashboard.objects.create(
            name='Default Dashboard 1',
            configuration={'layout': {}, 'widgets': []},
            owner=self.user,
            is_default=True
        )
        
        # Try to create second default dashboard
        dashboard2 = Dashboard(
            name='Default Dashboard 2',
            configuration={'layout': {}, 'widgets': []},
            owner=self.user,
            is_default=True
        )
        
        with self.assertRaises(ValidationError):
            dashboard2.full_clean()
    
    def test_increment_access(self):
        """Test incrementing dashboard access count"""
        dashboard = Dashboard.objects.create(
            name='Test Dashboard',
            configuration={'layout': {}, 'widgets': []},
            owner=self.user
        )
        
        initial_count = dashboard.access_count
        dashboard.increment_access()
        dashboard.refresh_from_db()
        
        self.assertEqual(dashboard.access_count, initial_count + 1)
        self.assertIsNotNone(dashboard.last_accessed)
    
    def test_create_from_template(self):
        """Test creating dashboard from template"""
        dashboard = Dashboard()
        dashboard = dashboard.create_from_template(
            template=self.template,
            user=self.user,
            name='Dashboard from Template'
        )
        
        self.assertEqual(dashboard.name, 'Dashboard from Template')
        self.assertEqual(dashboard.template, self.template)
        self.assertEqual(dashboard.template_version, self.template.version)
        self.assertEqual(dashboard.owner, self.user)
        
        # Check template usage was incremented
        self.template.refresh_from_db()
        self.assertEqual(self.template.usage_count, 1)
    
    def test_can_user_access_dashboard(self):
        """Test user access to dashboards"""
        dashboard = Dashboard.objects.create(
            name='Test Dashboard',
            configuration={'layout': {}, 'widgets': []},
            owner=self.user
        )
        
        # Owner can access
        self.assertTrue(dashboard.can_user_access(self.user))
        
        # Other users cannot access
        self.assertFalse(dashboard.can_user_access(self.other_user))
    
    def test_can_user_edit_dashboard(self):
        """Test user edit permissions for dashboards"""
        dashboard = Dashboard.objects.create(
            name='Test Dashboard',
            configuration={'layout': {}, 'widgets': []},
            owner=self.user
        )
        
        # Owner can edit
        self.assertTrue(dashboard.can_user_edit(self.user))
        
        # Other users cannot edit
        self.assertFalse(dashboard.can_user_edit(self.other_user))
    
    def test_share_dashboard_with_user(self):
        """Test sharing a dashboard with another user"""
        dashboard = Dashboard.objects.create(
            name='Shared Dashboard',
            configuration={'layout': {}, 'widgets': []},
            owner=self.user
        )
        
        share = dashboard.share_with_user(self.other_user, 'edit')
        
        self.assertEqual(share.dashboard, dashboard)
        self.assertEqual(share.user, self.other_user)
        self.assertEqual(share.permission_level, 'edit')
        self.assertTrue(dashboard.can_user_access(self.other_user))
        self.assertTrue(dashboard.can_user_edit(self.other_user))
        
        # Dashboard should be marked as shared
        dashboard.refresh_from_db()
        self.assertTrue(dashboard.is_shared)


class DashboardWidgetModelTest(TestCase):
    """Test cases for DashboardWidget model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.dashboard = Dashboard.objects.create(
            name='Test Dashboard',
            configuration={'layout': {}, 'widgets': []},
            owner=self.user
        )
    
    def test_create_dashboard_widget(self):
        """Test creating a dashboard widget"""
        widget = DashboardWidget.objects.create(
            dashboard=self.dashboard,
            widget_type='chart',
            title='Test Chart',
            position_x=0,
            position_y=0,
            width=2,
            height=2,
            config={'chart_type': 'line'}
        )
        
        self.assertEqual(widget.title, 'Test Chart')
        self.assertEqual(widget.widget_type, 'chart')
        self.assertEqual(widget.dashboard, self.dashboard)
        self.assertTrue(widget.is_visible)
    
    def test_widget_validation_chart_type_required(self):
        """Test widget validation requires chart_type for chart widgets"""
        widget = DashboardWidget(
            dashboard=self.dashboard,
            widget_type='chart',
            title='Invalid Chart',
            position_x=0,
            position_y=0,
            width=2,
            height=2,
            config={}  # Missing chart_type
        )
        
        with self.assertRaises(ValidationError):
            widget.full_clean()
    
    def test_widget_validation_metric_source_required(self):
        """Test widget validation requires metric_source for metric widgets"""
        widget = DashboardWidget(
            dashboard=self.dashboard,
            widget_type='metric',
            title='Invalid Metric',
            position_x=0,
            position_y=0,
            width=1,
            height=1,
            config={}  # Missing metric_source
        )
        
        with self.assertRaises(ValidationError):
            widget.full_clean()
    
    def test_widget_validation_position_overlap(self):
        """Test widget validation prevents position overlap"""
        # Create first widget
        DashboardWidget.objects.create(
            dashboard=self.dashboard,
            widget_type='chart',
            title='First Widget',
            position_x=0,
            position_y=0,
            width=2,
            height=2,
            config={'chart_type': 'line'}
        )
        
        # Try to create overlapping widget
        widget2 = DashboardWidget(
            dashboard=self.dashboard,
            widget_type='chart',
            title='Overlapping Widget',
            position_x=1,
            position_y=1,
            width=2,
            height=2,
            config={'chart_type': 'bar'}
        )
        
        with self.assertRaises(ValidationError):
            widget2.full_clean()


class DashboardTemplateViewTest(TestCase):
    """Test cases for dashboard template views"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            email='other@example.com',
            username='otheruser',
            password='testpass123'
        )
        
        self.template = DashboardTemplate.objects.create(
            name='Test Template',
            description='A test template',
            layout_config={'grid_columns': 12, 'grid_rows': 8},
            widget_configs=[
                {
                    'type': 'chart',
                    'position': {'x': 0, 'y': 0},
                    'config': {'chart_type': 'line'}
                }
            ],
            version='1.0.0',
            category='monitoring',
            tags=['test'],
            created_by=self.user
        )
        
        self.public_template = DashboardTemplate.objects.create(
            name='Public Template',
            layout_config={'grid_columns': 12, 'grid_rows': 8},
            widget_configs=[],
            is_public=True,
            created_by=self.other_user
        )
    
    def test_list_templates_anonymous(self):
        """Test listing templates as anonymous user"""
        response = self.client.get(reverse('template_dashboards:list_templates'))
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Should only see public templates
        self.assertEqual(len(data['templates']), 1)
        self.assertEqual(data['templates'][0]['name'], 'Public Template')
    
    def test_list_templates_authenticated(self):
        """Test listing templates as authenticated user"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('template_dashboards:list_templates'))
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Should see public templates and own templates
        self.assertEqual(len(data['templates']), 2)
        template_names = [t['name'] for t in data['templates']]
        self.assertIn('Test Template', template_names)
        self.assertIn('Public Template', template_names)
    
    def test_list_templates_with_search(self):
        """Test listing templates with search filter"""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse('template_dashboards:list_templates'),
            {'search': 'Test'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertEqual(len(data['templates']), 1)
        self.assertEqual(data['templates'][0]['name'], 'Test Template')
    
    def test_list_templates_with_category_filter(self):
        """Test listing templates with category filter"""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse('template_dashboards:list_templates'),
            {'category': 'monitoring'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertEqual(len(data['templates']), 1)
        self.assertEqual(data['templates'][0]['name'], 'Test Template')
    
    def test_get_template_success(self):
        """Test getting template details"""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse('template_dashboards:get_template', args=[self.template.id])
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertEqual(data['name'], 'Test Template')
        self.assertEqual(data['version'], '1.0.0')
        self.assertTrue(data['is_owner'])
        self.assertTrue(data['can_edit'])
    
    def test_get_template_access_denied(self):
        """Test getting template with no access"""
        self.client.force_login(self.other_user)
        response = self.client.get(
            reverse('template_dashboards:get_template', args=[self.template.id])
        )
        
        self.assertEqual(response.status_code, 403)
    
    def test_create_template_success(self):
        """Test creating a new template"""
        self.client.force_login(self.user)
        
        template_data = {
            'name': 'New Template',
            'description': 'A new template',
            'layout_config': {'grid_columns': 12, 'grid_rows': 8},
            'widget_configs': [],
            'version': '1.0.0',
            'category': 'analytics',
            'tags': ['new', 'test']
        }
        
        response = self.client.post(
            reverse('template_dashboards:create_template'),
            data=json.dumps(template_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        
        self.assertEqual(data['name'], 'New Template')
        self.assertEqual(data['version'], '1.0.0')
        
        # Verify template was created in database
        template = DashboardTemplate.objects.get(id=data['id'])
        self.assertEqual(template.name, 'New Template')
        self.assertEqual(template.created_by, self.user)
    
    def test_create_template_unauthenticated(self):
        """Test creating template without authentication"""
        template_data = {
            'name': 'New Template',
            'layout_config': {'grid_columns': 12, 'grid_rows': 8},
            'widget_configs': []
        }
        
        response = self.client.post(
            reverse('template_dashboards:create_template'),
            data=json.dumps(template_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_update_template_success(self):
        """Test updating a template"""
        self.client.force_login(self.user)
        
        update_data = {
            'name': 'Updated Template',
            'description': 'Updated description'
        }
        
        response = self.client.put(
            reverse('template_dashboards:update_template', args=[self.template.id]),
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify template was updated
        self.template.refresh_from_db()
        self.assertEqual(self.template.name, 'Updated Template')
        self.assertEqual(self.template.description, 'Updated description')
    
    def test_update_template_permission_denied(self):
        """Test updating template without permission"""
        self.client.force_login(self.other_user)
        
        update_data = {'name': 'Hacked Template'}
        
        response = self.client.put(
            reverse('template_dashboards:update_template', args=[self.template.id]),
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 403)
    
    def test_delete_template_success(self):
        """Test deleting a template"""
        self.client.force_login(self.user)
        
        response = self.client.delete(
            reverse('template_dashboards:delete_template', args=[self.template.id])
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify template was deleted
        self.assertFalse(
            DashboardTemplate.objects.filter(id=self.template.id).exists()
        )
    
    def test_delete_template_permission_denied(self):
        """Test deleting template without permission"""
        self.client.force_login(self.other_user)
        
        response = self.client.delete(
            reverse('template_dashboards:delete_template', args=[self.template.id])
        )
        
        self.assertEqual(response.status_code, 403)
    
    def test_create_template_version(self):
        """Test creating a new version of a template"""
        self.client.force_login(self.user)
        
        version_data = {
            'version': '1.1.0',
            'description': 'Updated version',
            'layout_config': {'grid_columns': 16, 'grid_rows': 10}
        }
        
        response = self.client.post(
            reverse('template_dashboards:create_template_version', args=[self.template.id]),
            data=json.dumps(version_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        
        self.assertEqual(data['version'], '1.1.0')
        
        # Verify new version was created
        new_template = DashboardTemplate.objects.get(id=data['id'])
        self.assertEqual(new_template.version, '1.1.0')
        self.assertEqual(new_template.parent_template, self.template)
    
    def test_share_template(self):
        """Test sharing a template with another user"""
        self.client.force_login(self.user)
        
        share_data = {
            'user_email': self.other_user.email,
            'permission_level': 'edit'
        }
        
        response = self.client.post(
            reverse('template_dashboards:share_template', args=[self.template.id]),
            data=json.dumps(share_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify template was shared
        share = TemplateShare.objects.get(
            template=self.template,
            user=self.other_user
        )
        self.assertEqual(share.permission_level, 'edit')
        self.assertTrue(self.template.can_user_access(self.other_user))


class DashboardViewTest(TestCase):
    """Test cases for dashboard views"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            email='other@example.com',
            username='otheruser',
            password='testpass123'
        )
        
        self.template = DashboardTemplate.objects.create(
            name='Test Template',
            layout_config={'grid_columns': 12, 'grid_rows': 8},
            widget_configs=[],
            created_by=self.user
        )
        
        self.dashboard = Dashboard.objects.create(
            name='Test Dashboard',
            description='A test dashboard',
            configuration={'layout': {}, 'widgets': []},
            owner=self.user
        )
    
    def test_list_dashboards(self):
        """Test listing user's dashboards"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('template_dashboards:list_dashboards'))
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertEqual(len(data['dashboards']), 1)
        self.assertEqual(data['dashboards'][0]['name'], 'Test Dashboard')
        self.assertTrue(data['dashboards'][0]['is_owner'])
    
    def test_get_dashboard_success(self):
        """Test getting dashboard details"""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse('template_dashboards:get_dashboard', args=[self.dashboard.id])
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertEqual(data['name'], 'Test Dashboard')
        self.assertTrue(data['is_owner'])
        self.assertTrue(data['can_edit'])
        
        # Verify access count was incremented
        self.dashboard.refresh_from_db()
        self.assertEqual(self.dashboard.access_count, 1)
    
    def test_get_dashboard_access_denied(self):
        """Test getting dashboard with no access"""
        self.client.force_login(self.other_user)
        response = self.client.get(
            reverse('template_dashboards:get_dashboard', args=[self.dashboard.id])
        )
        
        self.assertEqual(response.status_code, 403)
    
    def test_create_dashboard_from_scratch(self):
        """Test creating a dashboard from scratch"""
        self.client.force_login(self.user)
        
        dashboard_data = {
            'name': 'New Dashboard',
            'description': 'A new dashboard',
            'configuration': {'layout': {}, 'widgets': []},
            'is_favorite': True
        }
        
        response = self.client.post(
            reverse('template_dashboards:create_dashboard'),
            data=json.dumps(dashboard_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        
        self.assertEqual(data['name'], 'New Dashboard')
        
        # Verify dashboard was created
        dashboard = Dashboard.objects.get(id=data['id'])
        self.assertEqual(dashboard.name, 'New Dashboard')
        self.assertEqual(dashboard.owner, self.user)
        self.assertTrue(dashboard.is_favorite)
    
    def test_create_dashboard_from_template(self):
        """Test creating a dashboard from a template"""
        self.client.force_login(self.user)
        
        dashboard_data = {
            'name': 'Dashboard from Template',
            'template_id': str(self.template.id)
        }
        
        response = self.client.post(
            reverse('template_dashboards:create_dashboard'),
            data=json.dumps(dashboard_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        
        # Verify dashboard was created from template
        dashboard = Dashboard.objects.get(id=data['id'])
        self.assertEqual(dashboard.template, self.template)
        self.assertEqual(dashboard.template_version, self.template.version)
        
        # Verify template usage was incremented
        self.template.refresh_from_db()
        self.assertEqual(self.template.usage_count, 1)
    
    def test_update_dashboard_success(self):
        """Test updating a dashboard"""
        self.client.force_login(self.user)
        
        update_data = {
            'name': 'Updated Dashboard',
            'is_favorite': True
        }
        
        response = self.client.put(
            reverse('template_dashboards:update_dashboard', args=[self.dashboard.id]),
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify dashboard was updated
        self.dashboard.refresh_from_db()
        self.assertEqual(self.dashboard.name, 'Updated Dashboard')
        self.assertTrue(self.dashboard.is_favorite)
    
    def test_delete_dashboard_success(self):
        """Test deleting a dashboard"""
        self.client.force_login(self.user)
        
        response = self.client.delete(
            reverse('template_dashboards:delete_dashboard', args=[self.dashboard.id])
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify dashboard was deleted
        self.assertFalse(
            Dashboard.objects.filter(id=self.dashboard.id).exists()
        )
    
    def test_share_dashboard(self):
        """Test sharing a dashboard with another user"""
        self.client.force_login(self.user)
        
        share_data = {
            'user_email': self.other_user.email,
            'permission_level': 'view'
        }
        
        response = self.client.post(
            reverse('template_dashboards:share_dashboard', args=[self.dashboard.id]),
            data=json.dumps(share_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify dashboard was shared
        share = DashboardShare.objects.get(
            dashboard=self.dashboard,
            user=self.other_user
        )
        self.assertEqual(share.permission_level, 'view')
        self.assertTrue(self.dashboard.can_user_access(self.other_user))


class StatisticsViewTest(TestCase):
    """Test cases for statistics and analytics views"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        
        # Create templates with different categories
        DashboardTemplate.objects.create(
            name='Monitoring Template',
            layout_config={'grid_columns': 12, 'grid_rows': 8},
            widget_configs=[],
            category='monitoring',
            is_public=True,
            created_by=self.user
        )
        
        DashboardTemplate.objects.create(
            name='Analytics Template',
            layout_config={'grid_columns': 12, 'grid_rows': 8},
            widget_configs=[],
            category='analytics',
            is_public=True,
            created_by=self.user
        )
        
        # Create dashboards
        Dashboard.objects.create(
            name='Dashboard 1',
            configuration={'layout': {}, 'widgets': []},
            owner=self.user,
            is_favorite=True,
            access_count=10
        )
        
        Dashboard.objects.create(
            name='Dashboard 2',
            configuration={'layout': {}, 'widgets': []},
            owner=self.user,
            access_count=5
        )
    
    def test_get_template_categories(self):
        """Test getting template categories with counts"""
        response = self.client.get(reverse('template_dashboards:get_template_categories'))
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertEqual(len(data['categories']), 2)
        
        categories = {cat['category']: cat['count'] for cat in data['categories']}
        self.assertEqual(categories['monitoring'], 1)
        self.assertEqual(categories['analytics'], 1)
    
    def test_get_dashboard_stats(self):
        """Test getting dashboard statistics for user"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('template_dashboards:get_dashboard_stats'))
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertEqual(data['total_dashboards'], 2)
        self.assertEqual(data['favorite_dashboards'], 1)
        self.assertEqual(data['templates_created'], 2)
        self.assertEqual(data['most_accessed_dashboard']['name'], 'Dashboard 1')
        self.assertEqual(data['most_accessed_dashboard']['access_count'], 10)
    
    def test_get_dashboard_stats_unauthenticated(self):
        """Test getting dashboard stats without authentication"""
        response = self.client.get(reverse('template_dashboards:get_dashboard_stats'))
        
        self.assertEqual(response.status_code, 302)  # Redirect to login
