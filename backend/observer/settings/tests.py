from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse
import json
import uuid

from .models import (
    ConfigurationCategory,
    ConfigurationSetting,
    ConfigurationProfile,
    ConfigurationProfileSetting,
    ConfigurationDeployment,
    ConfigurationChangeLog,
    ConfigurationValidationRule
)

User = get_user_model()


class ConfigurationCategoryModelTest(TestCase):
    """Test ConfigurationCategory model."""
    
    def setUp(self):
        self.category_data = {
            'name': 'test_category',
            'display_name': 'Test Category',
            'description': 'A test category',
            'icon': 'test-icon',
            'sort_order': 10
        }
    
    def test_create_category(self):
        """Test creating a configuration category."""
        category = ConfigurationCategory.objects.create(**self.category_data)
        
        self.assertEqual(category.name, 'test_category')
        self.assertEqual(category.display_name, 'Test Category')
        self.assertEqual(str(category), 'Test Category')
        self.assertTrue(category.is_active)
    
    def test_category_ordering(self):
        """Test category ordering by sort_order and name."""
        cat1 = ConfigurationCategory.objects.create(
            name='z_category', display_name='Z Category', sort_order=20
        )
        cat2 = ConfigurationCategory.objects.create(
            name='a_category', display_name='A Category', sort_order=10
        )
        
        categories = list(ConfigurationCategory.objects.all())
        self.assertEqual(categories[0], cat2)  # Lower sort_order first
        self.assertEqual(categories[1], cat1)


class ConfigurationSettingModelTest(TestCase):
    """Test ConfigurationSetting model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser'
        )
        
        self.category = ConfigurationCategory.objects.create(
            name='test_category',
            display_name='Test Category'
        )
        
        self.setting_data = {
            'category': self.category,
            'key': 'test.setting',
            'display_name': 'Test Setting',
            'description': 'A test setting',
            'setting_type': 'string',
            'default_value': 'default_value',
            'is_required': True
        }
    
    def test_create_setting(self):
        """Test creating a configuration setting."""
        setting = ConfigurationSetting.objects.create(**self.setting_data)
        
        self.assertEqual(setting.key, 'test.setting')
        self.assertEqual(setting.get_value(), 'default_value')
        self.assertEqual(str(setting), 'test_category.test.setting')
    
    def test_setting_value_validation(self):
        """Test setting value validation."""
        setting = ConfigurationSetting.objects.create(**self.setting_data)
        
        # Valid string value
        setting.set_value('new_value', self.user)
        self.assertEqual(setting.get_value(), 'new_value')
        
        # Test integer setting
        int_setting = ConfigurationSetting.objects.create(
            category=self.category,
            key='test.int_setting',
            display_name='Int Setting',
            description='An integer setting',
            setting_type='integer',
            default_value=10
        )
        
        int_setting.set_value(20, self.user)
        self.assertEqual(int_setting.get_value(), 20)
        
        # Invalid type should raise ValidationError
        with self.assertRaises(ValidationError):
            int_setting.set_value('not_an_integer', self.user)
    
    def test_readonly_setting(self):
        """Test that readonly settings cannot be updated."""
        setting_data = self.setting_data.copy()
        setting_data['is_readonly'] = True
        setting = ConfigurationSetting.objects.create(**setting_data)
        
        with self.assertRaises(ValidationError):
            setting.set_value('new_value', self.user)
    
    def test_validation_rules(self):
        """Test custom validation rules."""
        setting_data = self.setting_data.copy()
        setting_data['validation_rules'] = {
            'min_length': 5,
            'max_length': 20
        }
        setting = ConfigurationSetting.objects.create(**setting_data)
        
        # Valid length
        setting.set_value('valid_value', self.user)
        
        # Too short
        with self.assertRaises(ValidationError):
            setting.set_value('abc', self.user)
        
        # Too long
        with self.assertRaises(ValidationError):
            setting.set_value('a' * 25, self.user)
    
    def test_choice_setting(self):
        """Test choice type settings."""
        setting_data = self.setting_data.copy()
        setting_data.update({
            'setting_type': 'choice',
            'choices': [
                {'value': 'option1', 'label': 'Option 1'},
                {'value': 'option2', 'label': 'Option 2'}
            ],
            'default_value': 'option1'
        })
        setting = ConfigurationSetting.objects.create(**setting_data)
        
        # Valid choice
        setting.set_value('option2', self.user)
        self.assertEqual(setting.get_value(), 'option2')
        
        # Invalid choice
        with self.assertRaises(ValidationError):
            setting.set_value('invalid_option', self.user)


class ConfigurationProfileModelTest(TestCase):
    """Test ConfigurationProfile model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser'
        )
    
    def test_create_profile(self):
        """Test creating a configuration profile."""
        profile = ConfigurationProfile.objects.create(
            name='test_profile',
            display_name='Test Profile',
            description='A test profile',
            created_by=self.user
        )
        
        self.assertEqual(profile.name, 'test_profile')
        self.assertEqual(str(profile), 'Test Profile')
        self.assertFalse(profile.is_default)
    
    def test_default_profile_uniqueness(self):
        """Test that only one profile can be default."""
        profile1 = ConfigurationProfile.objects.create(
            name='profile1',
            display_name='Profile 1',
            is_default=True,
            created_by=self.user
        )
        
        profile2 = ConfigurationProfile.objects.create(
            name='profile2',
            display_name='Profile 2',
            is_default=True,
            created_by=self.user
        )
        
        # Refresh from database
        profile1.refresh_from_db()
        profile2.refresh_from_db()
        
        # Only profile2 should be default now
        self.assertFalse(profile1.is_default)
        self.assertTrue(profile2.is_default)


class SettingsViewsTest(TestCase):
    """Test settings app views."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpassword123'
        )
        
        self.category = ConfigurationCategory.objects.create(
            name='test_category',
            display_name='Test Category'
        )
        
        self.setting = ConfigurationSetting.objects.create(
            category=self.category,
            key='test.setting',
            display_name='Test Setting',
            description='A test setting',
            setting_type='string',
            default_value='default_value'
        )
    
    def test_get_categories(self):
        """Test getting configuration categories."""
        response = self.client.get('/api/v1/settings/categories/')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']), 1)
        self.assertEqual(data['data'][0]['name'], 'test_category')
    
    def test_get_settings(self):
        """Test getting configuration settings."""
        response = self.client.get('/api/v1/settings/settings/')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']), 1)
        self.assertEqual(data['data'][0]['key'], 'test.setting')
    
    def test_get_settings_by_category(self):
        """Test getting settings filtered by category."""
        response = self.client.get(f'/api/v1/settings/settings/?category_id={self.category.id}')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']), 1)
    
    def test_update_setting_requires_login(self):
        """Test that updating settings requires authentication."""
        response = self.client.post(
            f'/api/v1/settings/settings/{self.setting.id}/update/',
            data=json.dumps({'value': 'new_value'}),
            content_type='application/json'
        )
        
        # Should redirect to login or return 401/403
        self.assertIn(response.status_code, [302, 401, 403])
    
    def test_update_setting_authenticated(self):
        """Test updating a setting when authenticated."""
        self.client.login(email='test@example.com', password='testpassword123')
        
        response = self.client.post(
            f'/api/v1/settings/settings/{self.setting.id}/update/',
            data=json.dumps({'value': 'new_value', 'reason': 'Test update'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        
        # Verify setting was updated
        self.setting.refresh_from_db()
        self.assertEqual(self.setting.current_value, 'new_value')
        
        # Verify change log was created
        change_log = ConfigurationChangeLog.objects.filter(setting=self.setting).first()
        self.assertIsNotNone(change_log)
        self.assertEqual(change_log.new_value, 'new_value')
        self.assertEqual(change_log.changed_by, self.user)
    
    def test_validate_settings(self):
        """Test settings validation endpoint."""
        self.client.login(email='test@example.com', password='testpassword123')
        
        response = self.client.post(
            '/api/v1/settings/settings/validate/',
            data=json.dumps({
                'settings': [
                    {'id': str(self.setting.id), 'value': 'valid_value'}
                ]
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        self.assertTrue(data['all_valid'])
        self.assertEqual(len(data['results']), 1)
        self.assertTrue(data['results'][0]['valid'])
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = self.client.get('/api/v1/settings/health/')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        self.assertEqual(data['service'], 'settings')
        self.assertEqual(data['status'], 'healthy')


class ConfigurationDeploymentTest(TestCase):
    """Test configuration deployment functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpassword123'
        )
        
        self.category = ConfigurationCategory.objects.create(
            name='test_category',
            display_name='Test Category'
        )
        
        self.setting = ConfigurationSetting.objects.create(
            category=self.category,
            key='test.setting',
            display_name='Test Setting',
            description='A test setting',
            setting_type='string',
            default_value='default_value'
        )
        
        self.profile = ConfigurationProfile.objects.create(
            name='test_profile',
            display_name='Test Profile',
            description='A test profile',
            created_by=self.user
        )
        
        # Add setting to profile
        ConfigurationProfileSetting.objects.create(
            profile=self.profile,
            setting=self.setting,
            value='profile_value'
        )
    
    def test_deploy_profile(self):
        """Test deploying a configuration profile."""
        self.client = Client()
        self.client.login(email='test@example.com', password='testpassword123')
        
        response = self.client.post(
            f'/api/v1/settings/profiles/{self.profile.id}/deploy/',
            data=json.dumps({'notes': 'Test deployment'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['applied_settings'], 1)
        
        # Verify setting was updated
        self.setting.refresh_from_db()
        self.assertEqual(self.setting.current_value, 'profile_value')
        
        # Verify deployment record was created
        deployment = ConfigurationDeployment.objects.filter(profile=self.profile).first()
        self.assertIsNotNone(deployment)
        self.assertEqual(deployment.status, 'completed')
        self.assertEqual(deployment.deployed_by, self.user)


class ConfigurationValidationRuleTest(TestCase):
    """Test configuration validation rules."""
    
    def setUp(self):
        self.category = ConfigurationCategory.objects.create(
            name='test_category',
            display_name='Test Category'
        )
        
        self.setting = ConfigurationSetting.objects.create(
            category=self.category,
            key='test.setting',
            display_name='Test Setting',
            description='A test setting',
            setting_type='string',
            default_value='default_value'
        )
    
    def test_regex_validation_rule(self):
        """Test regex validation rule."""
        rule = ConfigurationValidationRule.objects.create(
            name='email_pattern',
            description='Email pattern validation',
            rule_type='regex',
            rule_config={'pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'},
            error_message='Invalid email format'
        )
        
        # Valid email
        self.assertTrue(rule.validate_value('test@example.com', self.setting))
        
        # Invalid email
        self.assertFalse(rule.validate_value('invalid-email', self.setting))
    
    def test_range_validation_rule(self):
        """Test range validation rule."""
        rule = ConfigurationValidationRule.objects.create(
            name='number_range',
            description='Number range validation',
            rule_type='range',
            rule_config={'min': 1, 'max': 100},
            error_message='Value must be between 1 and 100'
        )
        
        # Valid range
        self.assertTrue(rule.validate_value(50, self.setting))
        
        # Below minimum
        self.assertFalse(rule.validate_value(0, self.setting))
        
        # Above maximum
        self.assertFalse(rule.validate_value(101, self.setting))
    
    def test_length_validation_rule(self):
        """Test length validation rule."""
        rule = ConfigurationValidationRule.objects.create(
            name='string_length',
            description='String length validation',
            rule_type='length',
            rule_config={'min_length': 5, 'max_length': 20},
            error_message='String must be between 5 and 20 characters'
        )
        
        # Valid length
        self.assertTrue(rule.validate_value('valid_string', self.setting))
        
        # Too short
        self.assertFalse(rule.validate_value('abc', self.setting))
        
        # Too long
        self.assertFalse(rule.validate_value('a' * 25, self.setting))
