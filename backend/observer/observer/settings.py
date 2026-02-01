"""
Django settings for Observer Eye Platform.

Production-ready configuration with security best practices.
Environment-specific settings are loaded from environment variables.
"""

import os
import sys
from pathlib import Path
from django.core.management.utils import get_random_secret_key

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Environment detection
ENVIRONMENT = os.getenv('DJANGO_ENVIRONMENT', 'development')
IS_PRODUCTION = ENVIRONMENT == 'production'
IS_TESTING = 'test' in sys.argv or 'pytest' in sys.modules

# Security settings
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    if IS_PRODUCTION:
        raise ValueError("DJANGO_SECRET_KEY environment variable is required in production")
    else:
        # Generate a random secret key for development
        SECRET_KEY = get_random_secret_key()

DEBUG = os.getenv('DJANGO_DEBUG', 'False').lower() == 'true' and not IS_PRODUCTION

ALLOWED_HOSTS = []
if IS_PRODUCTION:
    allowed_hosts_env = os.getenv('DJANGO_ALLOWED_HOSTS', '')
    ALLOWED_HOSTS = [host.strip() for host in allowed_hosts_env.split(',') if host.strip()]
else:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']


# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
]

THIRD_PARTY_APPS = [
    'corsheaders',
]

OBSERVER_EYE_APPS = [
    'core',
    'analytics',
    'analytics_performance_monitoring',
    'application_performance_monitoring',
    'appmetrics',
    'grailobserver',
    'identity_performance_monitoring',
    'integration',
    'netmetrics',
    'notification',
    'security_performance_monitoring',
    'securitymetrics',
    'settings',
    'sysmetrics',
    'system_performance_monitoring',
    'template_dashboards',
    'traffic_performance_monitoring',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + OBSERVER_EYE_APPS

# Custom user model
AUTH_USER_MODEL = 'core.User'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'core.middleware.SecurityHeadersMiddleware',
    'core.middleware.RateLimitingMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'core.middleware.SessionAuthenticationMiddleware',
    'core.middleware.RequestLoggingMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# CORS settings for frontend integration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:80",
    "http://127.0.0.1:80",
    "http://localhost:4200",  # Angular dev server
    "http://127.0.0.1:4200",
]

if IS_PRODUCTION:
    cors_origins_env = os.getenv('CORS_ALLOWED_ORIGINS', '')
    if cors_origins_env:
        CORS_ALLOWED_ORIGINS = [origin.strip() for origin in cors_origins_env.split(',') if origin.strip()]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False  # Security: Never allow all origins in production

ROOT_URLCONF = 'observer.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'observer.wsgi.application'


# Database configuration
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

if IS_PRODUCTION:
    # Production database configuration (PostgreSQL)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'observer_eye'),
            'USER': os.getenv('DB_USER', 'observer'),
            'PASSWORD': os.getenv('DB_PASSWORD'),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
            'OPTIONS': {
                'sslmode': os.getenv('DB_SSLMODE', 'require'),
            },
            'CONN_MAX_AGE': 60,  # Connection pooling
        }
    }
    
    # Ensure required database environment variables are set
    if not os.getenv('DB_PASSWORD'):
        raise ValueError("DB_PASSWORD environment variable is required in production")
        
elif IS_TESTING:
    # Test database configuration (in-memory SQLite)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
else:
    # Development database configuration (SQLite)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Database connection settings
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Password validation with Observer Eye Platform requirements
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 16,  # Observer Eye Platform requirement
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Custom password validation
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/6.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Logging configuration with structlog integration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'observer.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'json' if IS_PRODUCTION else 'verbose',
        },
        'console': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'error.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'json' if IS_PRODUCTION else 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'observer_eye': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}

# Ensure logs directory exists
(BASE_DIR / 'logs').mkdir(exist_ok=True)

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Production security settings
if IS_PRODUCTION:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
else:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

# Session configuration
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# CSRF configuration
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS

# Cache configuration
if IS_PRODUCTION:
    # Redis cache for production
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            },
            'KEY_PREFIX': 'observer_eye',
            'TIMEOUT': 300,  # 5 minutes default
        }
    }
elif IS_TESTING:
    # Dummy cache for testing
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }
else:
    # Local memory cache for development
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'observer-cache',
            'TIMEOUT': 300,
            'OPTIONS': {
                'MAX_ENTRIES': 1000,
            }
        }
    }

# Observer Eye Platform specific settings
OBSERVER_EYE_SETTINGS = {
    'PASSWORD_MIN_LENGTH': 16,
    'SESSION_TIMEOUT_HOURS': 24,
    'MAX_LOGIN_ATTEMPTS': 5,
    'LOGIN_ATTEMPT_TIMEOUT_MINUTES': 15,
    'AUDIT_LOG_RETENTION_DAYS': 90,
    'METRICS_RETENTION_DAYS': 365,
    'ENABLE_TELEMETRY': os.getenv('ENABLE_TELEMETRY', 'true').lower() == 'true',
    'TELEMETRY_SAMPLE_RATE': float(os.getenv('TELEMETRY_SAMPLE_RATE', '0.1')),
}

# OAuth Provider Settings
OAUTH_PROVIDERS = {
    'github': {
        'client_id': os.getenv('GITHUB_CLIENT_ID'),
        'client_secret': os.getenv('GITHUB_CLIENT_SECRET'),
        'enabled': bool(os.getenv('GITHUB_CLIENT_ID')),
    },
    'gitlab': {
        'client_id': os.getenv('GITLAB_CLIENT_ID'),
        'client_secret': os.getenv('GITLAB_CLIENT_SECRET'),
        'enabled': bool(os.getenv('GITLAB_CLIENT_ID')),
    },
    'google': {
        'client_id': os.getenv('GOOGLE_CLIENT_ID'),
        'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
        'enabled': bool(os.getenv('GOOGLE_CLIENT_ID')),
    },
    'microsoft': {
        'client_id': os.getenv('MICROSOFT_CLIENT_ID'),
        'client_secret': os.getenv('MICROSOFT_CLIENT_SECRET'),
        'enabled': bool(os.getenv('MICROSOFT_CLIENT_ID')),
    },
}

# OpenTelemetry configuration
if OBSERVER_EYE_SETTINGS['ENABLE_TELEMETRY']:
    INSTALLED_APPS += [
        'opentelemetry.instrumentation.django',
    ]

# Email configuration (for notifications)
if IS_PRODUCTION:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.getenv('EMAIL_HOST')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
    EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'true').lower() == 'true'
    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
    DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@observer-eye.com')
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Data validation settings
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

# API Rate limiting (if using django-ratelimit)
RATELIMIT_ENABLE = IS_PRODUCTION
RATELIMIT_USE_CACHE = 'default'
