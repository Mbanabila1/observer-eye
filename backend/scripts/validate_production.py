#!/usr/bin/env python3
"""
Production Build Validation Script for Django Backend

This script validates that the Django backend is properly configured for production
and contains no mock, seed, or sample data.
"""

import os
import sys
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add the Django project to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'observer'))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'observer.settings')

import django
django.setup()

from django.conf import settings
from django.core.management import execute_from_command_line
from django.db import connection


class ProductionValidator:
    """Validates Django backend for production readiness."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.project_root = Path(__file__).parent.parent
        
    def validate_all(self) -> Dict[str, Any]:
        """Run all validation checks."""
        print("🔍 Starting production validation for Django backend...")
        
        # Configuration validation
        self.validate_django_settings()
        self.validate_environment_variables()
        
        # Code validation
        self.validate_no_mock_data()
        self.validate_no_seed_data()
        self.validate_no_debug_code()
        
        # Security validation
        self.validate_security_settings()
        
        # Database validation
        self.validate_database_config()
        
        return {
            "status": "PASS" if not self.errors else "FAIL",
            "errors": self.errors,
            "warnings": self.warnings,
            "checks_performed": [
                "Django settings validation",
                "Environment variables check",
                "Mock data detection",
                "Seed data detection", 
                "Debug code detection",
                "Security settings validation",
                "Database configuration check"
            ]
        }
    
    def validate_django_settings(self):
        """Validate Django settings for production."""
        print("  ✓ Validating Django settings...")
        
        # Check DEBUG setting
        if getattr(settings, 'DEBUG', True):
            self.errors.append("DEBUG is enabled in production settings")
        
        # Check SECRET_KEY
        secret_key = getattr(settings, 'SECRET_KEY', '')
        if not secret_key or len(secret_key) < 50:
            self.errors.append("SECRET_KEY is missing or too short for production")
        
        if secret_key in ['your-secret-key-here', 'django-insecure-key']:
            self.errors.append("SECRET_KEY appears to be a default/example value")
        
        # Check ALLOWED_HOSTS
        allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', [])
        if not allowed_hosts or allowed_hosts == ['*']:
            self.warnings.append("ALLOWED_HOSTS should be configured with specific domains")
        
        # Check database configuration
        databases = getattr(settings, 'DATABASES', {})
        default_db = databases.get('default', {})
        if default_db.get('ENGINE') == 'django.db.backends.sqlite3':
            self.warnings.append("Using SQLite in production - consider PostgreSQL")
    
    def validate_environment_variables(self):
        """Validate required environment variables."""
        print("  ✓ Validating environment variables...")
        
        required_vars = [
            'DJANGO_SECRET_KEY',
            'DATABASE_URL',
        ]
        
        for var in required_vars:
            if not os.getenv(var):
                self.warnings.append(f"Environment variable {var} is not set")
    
    def validate_no_mock_data(self):
        """Check for mock data in the codebase."""
        print("  ✓ Checking for mock data...")
        
        mock_patterns = [
            r'mock_data',
            r'MockData',
            r'MOCK_.*=',
            r'fake_data',
            r'FakeData',
            r'test_data.*=',
            r'sample_data',
            r'SampleData',
            r'dummy_data',
            r'DummyData'
        ]
        
        self._scan_files_for_patterns(mock_patterns, "mock data")
    
    def validate_no_seed_data(self):
        """Check for seed data in the codebase."""
        print("  ✓ Checking for seed data...")
        
        seed_patterns = [
            r'seed_data',
            r'SeedData',
            r'fixtures.*=',
            r'initial_data',
            r'InitialData',
            r'bootstrap_data',
            r'BootstrapData'
        ]
        
        self._scan_files_for_patterns(seed_patterns, "seed data")
        
        # Check for Django fixtures
        fixture_dirs = [
            self.project_root / 'observer' / 'fixtures',
            self.project_root / 'fixtures'
        ]
        
        for fixture_dir in fixture_dirs:
            if fixture_dir.exists():
                fixtures = list(fixture_dir.glob('*.json')) + list(fixture_dir.glob('*.yaml'))
                if fixtures:
                    self.warnings.append(f"Found fixture files in {fixture_dir}: {[f.name for f in fixtures]}")
    
    def validate_no_debug_code(self):
        """Check for debug code that shouldn't be in production."""
        print("  ✓ Checking for debug code...")
        
        debug_patterns = [
            r'print\s*\(',
            r'pdb\.set_trace\(\)',
            r'breakpoint\(\)',
            r'import\s+pdb',
            r'console\.log\(',
            r'debugger;',
            r'TODO:',
            r'FIXME:',
            r'XXX:'
        ]
        
        self._scan_files_for_patterns(debug_patterns, "debug code", is_warning=True)
    
    def validate_security_settings(self):
        """Validate security-related settings."""
        print("  ✓ Validating security settings...")
        
        # Check SECURE_SSL_REDIRECT
        if not getattr(settings, 'SECURE_SSL_REDIRECT', False):
            self.warnings.append("SECURE_SSL_REDIRECT is not enabled")
        
        # Check SECURE_HSTS_SECONDS
        if not getattr(settings, 'SECURE_HSTS_SECONDS', 0):
            self.warnings.append("SECURE_HSTS_SECONDS is not configured")
        
        # Check SESSION_COOKIE_SECURE
        if not getattr(settings, 'SESSION_COOKIE_SECURE', False):
            self.warnings.append("SESSION_COOKIE_SECURE is not enabled")
        
        # Check CSRF_COOKIE_SECURE
        if not getattr(settings, 'CSRF_COOKIE_SECURE', False):
            self.warnings.append("CSRF_COOKIE_SECURE is not enabled")
    
    def validate_database_config(self):
        """Validate database configuration."""
        print("  ✓ Validating database configuration...")
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                print("    ✓ Database connection successful")
        except Exception as e:
            self.errors.append(f"Database connection failed: {str(e)}")
    
    def _scan_files_for_patterns(self, patterns: List[str], description: str, is_warning: bool = False):
        """Scan Python files for specific patterns."""
        python_files = list(self.project_root.rglob('*.py'))
        
        # Exclude certain directories
        excluded_dirs = {'__pycache__', '.git', 'venv', 'env', 'node_modules', 'migrations', 'tests'}
        
        for file_path in python_files:
            # Skip files in excluded directories
            if any(excluded_dir in file_path.parts for excluded_dir in excluded_dirs):
                continue
            
            # Skip this validation script itself
            if file_path.name == 'validate_production.py':
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for pattern in patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        message = f"Found {description} in {file_path}:{line_num} - '{match.group()}'"
                        
                        if is_warning:
                            self.warnings.append(message)
                        else:
                            self.errors.append(message)
                            
            except Exception as e:
                self.warnings.append(f"Could not scan {file_path}: {str(e)}")


def main():
    """Main validation function."""
    validator = ProductionValidator()
    results = validator.validate_all()
    
    print("\n" + "="*60)
    print("🏁 PRODUCTION VALIDATION RESULTS")
    print("="*60)
    
    print(f"\n📊 Status: {results['status']}")
    print(f"🔍 Checks performed: {len(results['checks_performed'])}")
    
    if results['errors']:
        print(f"\n❌ Errors ({len(results['errors'])}):")
        for error in results['errors']:
            print(f"  • {error}")
    
    if results['warnings']:
        print(f"\n⚠️  Warnings ({len(results['warnings'])}):")
        for warning in results['warnings']:
            print(f"  • {warning}")
    
    if not results['errors'] and not results['warnings']:
        print("\n✅ All validation checks passed!")
    
    # Save results to file
    results_file = Path(__file__).parent / 'validation_results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: {results_file}")
    
    # Exit with appropriate code
    sys.exit(0 if results['status'] == 'PASS' else 1)


if __name__ == '__main__':
    main()