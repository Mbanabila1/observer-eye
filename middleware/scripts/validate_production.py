#!/usr/bin/env python3
"""
Production Build Validation Script for FastAPI Middleware

This script validates that the FastAPI middleware is properly configured for production
and contains no mock, seed, or sample data.
"""

import os
import sys
import re
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add the middleware project to the path
sys.path.insert(0, os.path.dirname(__file__).parent)


class MiddlewareProductionValidator:
    """Validates FastAPI middleware for production readiness."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.project_root = Path(__file__).parent.parent
        
    def validate_all(self) -> Dict[str, Any]:
        """Run all validation checks."""
        print("🔍 Starting production validation for FastAPI middleware...")
        
        # Configuration validation
        self.validate_environment_config()
        
        # Code validation
        self.validate_no_mock_data()
        self.validate_no_seed_data()
        self.validate_no_debug_code()
        
        # Security validation
        self.validate_security_settings()
        
        # Performance validation
        self.validate_performance_config()
        
        return {
            "status": "PASS" if not self.errors else "FAIL",
            "errors": self.errors,
            "warnings": self.warnings,
            "checks_performed": [
                "Environment configuration check",
                "Mock data detection",
                "Seed data detection", 
                "Debug code detection",
                "Security settings validation",
                "Performance configuration check"
            ]
        }
    
    def validate_environment_config(self):
        """Validate environment configuration."""
        print("  ✓ Validating environment configuration...")
        
        # Check environment variables
        required_vars = [
            'DATABASE_URL',
            'REDIS_URL',
            'DJANGO_BACKEND_URL'
        ]
        
        for var in required_vars:
            if not os.getenv(var):
                self.warnings.append(f"Environment variable {var} is not set")
        
        # Check FASTAPI_ENV
        fastapi_env = os.getenv('FASTAPI_ENV', 'development')
        if fastapi_env != 'production':
            self.warnings.append(f"FASTAPI_ENV is set to '{fastapi_env}', should be 'production'")
        
        # Check LOG_LEVEL
        log_level = os.getenv('LOG_LEVEL', 'debug')
        if log_level.lower() in ['debug', 'trace']:
            self.warnings.append(f"LOG_LEVEL is set to '{log_level}', consider 'info' or 'warning' for production")
    
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
            r'DummyData',
            r'Mock\w+\(',
            r'@mock\.',
            r'unittest\.mock'
        ]
        
        self._scan_files_for_patterns(mock_patterns, "mock data")
    
    def validate_no_seed_data(self):
        """Check for seed data in the codebase."""
        print("  ✓ Checking for seed data...")
        
        seed_patterns = [
            r'seed_data',
            r'SeedData',
            r'initial_data',
            r'InitialData',
            r'bootstrap_data',
            r'BootstrapData',
            r'sample_.*_data',
            r'example_.*_data'
        ]
        
        self._scan_files_for_patterns(seed_patterns, "seed data")
        
        # Check for data files that might contain seed data
        data_files = list(self.project_root.glob('**/*.json')) + \
                    list(self.project_root.glob('**/*.yaml')) + \
                    list(self.project_root.glob('**/*.yml'))
        
        for data_file in data_files:
            # Skip configuration files and package files
            if data_file.name in ['package.json', 'pyproject.toml', 'requirements.txt']:
                continue
            
            # Skip files in excluded directories
            excluded_dirs = {'__pycache__', '.git', 'venv', 'env', 'node_modules', '.pytest_cache'}
            if any(excluded_dir in data_file.parts for excluded_dir in excluded_dirs):
                continue
            
            self.warnings.append(f"Found data file that might contain seed data: {data_file}")
    
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
            r'XXX:',
            r'logger\.debug\(',
            r'logging\.DEBUG'
        ]
        
        self._scan_files_for_patterns(debug_patterns, "debug code", is_warning=True)
    
    def validate_security_settings(self):
        """Validate security-related settings."""
        print("  ✓ Validating security settings...")
        
        # Check main.py for security configurations
        main_file = self.project_root / 'main.py'
        if main_file.exists():
            try:
                with open(main_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for CORS configuration
                if 'CORSMiddleware' in content:
                    if 'allow_origins=["*"]' in content:
                        self.errors.append("CORS is configured to allow all origins (*) - security risk")
                    if 'allow_credentials=True' in content and 'allow_origins=["*"]' in content:
                        self.errors.append("CORS allows credentials with wildcard origins - security risk")
                
                # Check for docs in production
                if 'docs_url=' not in content or 'docs_url=None' not in content:
                    self.warnings.append("API documentation might be exposed in production")
                
            except Exception as e:
                self.warnings.append(f"Could not analyze main.py: {str(e)}")
    
    def validate_performance_config(self):
        """Validate performance-related configuration."""
        print("  ✓ Validating performance configuration...")
        
        # Check for performance monitoring
        performance_files = list(self.project_root.glob('**/performance/*.py'))
        if not performance_files:
            self.warnings.append("No performance monitoring modules found")
        
        # Check for caching configuration
        cache_files = list(self.project_root.glob('**/caching/*.py'))
        if not cache_files:
            self.warnings.append("No caching modules found")
        
        # Check Redis configuration
        redis_url = os.getenv('REDIS_URL')
        if not redis_url:
            self.warnings.append("Redis URL not configured - caching may not work")
    
    def _scan_files_for_patterns(self, patterns: List[str], description: str, is_warning: bool = False):
        """Scan Python files for specific patterns."""
        python_files = list(self.project_root.rglob('*.py'))
        
        # Exclude certain directories
        excluded_dirs = {'__pycache__', '.git', 'venv', 'env', 'node_modules', 'tests', 'testing', '.pytest_cache'}
        
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
    validator = MiddlewareProductionValidator()
    results = validator.validate_all()
    
    print("\n" + "="*60)
    print("🏁 MIDDLEWARE PRODUCTION VALIDATION RESULTS")
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