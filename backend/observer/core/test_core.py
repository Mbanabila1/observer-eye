"""
Basic test to validate Django testing setup
"""
from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class CoreTestCase(TestCase):
    """Test core functionality"""
    
    def test_django_setup(self):
        """Test that Django is properly configured"""
        self.assertTrue(True)
    
    def test_user_creation(self):
        """Test basic user creation"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpassword123'))
    
    def test_database_connection(self):
        """Test database connectivity"""
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            self.assertEqual(result[0], 1)