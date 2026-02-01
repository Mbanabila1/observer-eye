# Observer Eye Platform - Configuration Guide

## Configuration Overview

The Observer Eye Platform uses environment-based configuration across all three layers. Configuration is managed through environment variables, configuration files, and runtime settings.

## Environment Variables

### Global Configuration

**Root `.env` file:**
```env
# Environment
ENVIRONMENT=development  # development, staging, production
DEBUG=true              # Enable debug mode
LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Database Configuration
POSTGRES_DB=observer_eye
POSTGRES_USER=observer_user
POSTGRES_PASSWORD=secure_password_here
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
DATABASE_URL=postgresql://observer_user:secure_password_here@postgres:5432/observer_eye

# Redis Configuration
REDIS_URL=redis://redis:6379/0
REDIS_PASSWORD=redis_password_here

# Service URLs
DJANGO_URL=http://backend:8000
FASTAPI_URL=http://middleware:8400
FRONTEND_URL=http://dashboard:80

# Security
SECRET_KEY=your-secret-key-here-minimum-50-characters-long
JWT_SECRET=your-jwt-secret-here-minimum-32-characters-long
JWT_EXPIRATION_HOURS=24

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:80,http://localhost:4200,http://localhost:3000
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# SSL/TLS
SECURE_SSL_REDIRECT=false  # Set to true in production
SECURE_HSTS_SECONDS=0      # Set to 31536000 in production
```

### Backend Configuration (Django)

**`backend/.env` file:**
```env
# Django Settings
SECRET_KEY=your-django-secret-key-minimum-50-characters-long
DEBUG=false
ALLOWED_HOSTS=localhost,127.0.0.1,backend,your-domain.com

# Database
DATABASE_URL=postgresql://observer_user:secure_password_here@postgres:5432/observer_eye
DATABASE_CONN_MAX_AGE=600
DATABASE_CONN_HEALTH_CHECKS=true

# Cache
CACHE_URL=redis://redis:6379/1
CACHE_TIMEOUT=3600
CACHE_KEY_PREFIX=observer_eye

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# OAuth Configuration
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GITLAB_CLIENT_ID=your-gitlab-client-id
GITLAB_CLIENT_SECRET=your-gitlab-client-secret
MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret

# Monitoring
SENTRY_DSN=your-sentry-dsn
OPENTELEMETRY_ENDPOINT=http://jaeger:14268/api/traces
OPENTELEMETRY_SERVICE_NAME=observer-eye-backend

# File Storage
MEDIA_ROOT=/app/media
STATIC_ROOT=/app/static
DEFAULT_FILE_STORAGE=django.core.files.storage.FileSystemStorage

# Logging
LOG_LEVEL=INFO
LOG_FILE=/app/logs/observer.log
LOG_MAX_SIZE=10485760  # 10MB
LOG_BACKUP_COUNT=5

# Security
SECURE_BROWSER_XSS_FILTER=true
SECURE_CONTENT_TYPE_NOSNIFF=true
X_FRAME_OPTIONS=DENY
SECURE_HSTS_INCLUDE_SUBDOMAINS=true
SECURE_HSTS_PRELOAD=true

# Session Configuration
SESSION_COOKIE_SECURE=true  # Set to true in production with HTTPS
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Lax
SESSION_COOKIE_AGE=86400  # 24 hours

# CSRF Protection
CSRF_COOKIE_SECURE=true  # Set to true in production with HTTPS
CSRF_COOKIE_HTTPONLY=true
CSRF_COOKIE_SAMESITE=Lax
```

### Middleware Configuration (FastAPI)

**`middleware/.env` file:**
```env
# FastAPI Settings
DJANGO_BACKEND_URL=http://backend:8000
REDIS_URL=redis://redis:6379/0
ENVIRONMENT=production
DEBUG=false

# Performance
WORKER_PROCESSES=4
MAX_CONNECTIONS=1000
KEEPALIVE_TIMEOUT=5
REQUEST_TIMEOUT=30

# Data Processing
BATCH_SIZE=1000
MAX_BATCH_SIZE=10000
PROCESSING_TIMEOUT=60
VALIDATION_LEVEL=moderate  # strict, moderate, lenient

# Caching
CACHE_DEFAULT_TTL=3600
CACHE_MAX_SIZE=1000000
CACHE_COMPRESSION=true
CACHE_METRICS=true

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW=3600  # 1 hour

# Monitoring
OPENTELEMETRY_ENDPOINT=http://jaeger:14268/api/traces
OPENTELEMETRY_SERVICE_NAME=observer-eye-middleware
METRICS_ENABLED=true
HEALTH_CHECK_INTERVAL=30

# Data Ingestion
INGESTION_BUFFER_SIZE=1000
INGESTION_FLUSH_INTERVAL=5
INGESTION_MAX_RETRIES=3
INGESTION_QUALITY_THRESHOLD=0.95

# Streaming
WEBSOCKET_MAX_CONNECTIONS=1000
WEBSOCKET_HEARTBEAT_INTERVAL=30
STREAMING_BUFFER_SIZE=10000
BACKPRESSURE_THRESHOLD=0.8

# Security
CORS_ALLOW_CREDENTIALS=true
CORS_MAX_AGE=86400
TRUSTED_HOSTS=localhost,127.0.0.1,middleware,your-domain.com

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/app/logs/middleware.log
```

### Frontend Configuration (Angular)

**`dashboard/.env` file:**
```env
# Angular Environment
NODE_ENV=production
ENVIRONMENT=production

# API Configuration
API_BASE_URL=http://localhost:8400
BACKEND_URL=http://localhost:8000
WEBSOCKET_URL=ws://localhost:8400/ws

# Authentication
AUTH_TOKEN_KEY=observer_eye_token
AUTH_REFRESH_KEY=observer_eye_refresh
AUTH_TOKEN_EXPIRY=86400  # 24 hours

# OAuth Providers
OAUTH_GITHUB_ENABLED=true
OAUTH_GOOGLE_ENABLED=true
OAUTH_GITLAB_ENABLED=true
OAUTH_MICROSOFT_ENABLED=true

# UI Configuration
DEFAULT_THEME=light  # light, dark, auto
DEFAULT_LANGUAGE=en
TIMEZONE=UTC
DATE_FORMAT=YYYY-MM-DD
TIME_FORMAT=HH:mm:ss

# Dashboard Settings
DASHBOARD_REFRESH_INTERVAL=30000  # 30 seconds
CHART_ANIMATION_DURATION=300
MAX_DASHBOARD_WIDGETS=20
AUTO_SAVE_INTERVAL=60000  # 1 minute

# Performance
ENABLE_SERVICE_WORKER=true
CACHE_STRATEGY=stale-while-revalidate
BUNDLE_ANALYZER=false
SOURCE_MAPS=false

# Monitoring
SENTRY_DSN=your-frontend-sentry-dsn
ANALYTICS_ENABLED=true
ERROR_REPORTING=true

# Feature Flags
FEATURE_REAL_TIME_UPDATES=true
FEATURE_ADVANCED_ANALYTICS=true
FEATURE_CUSTOM_DASHBOARDS=true
FEATURE_EXPORT_DATA=true
```

## Application-Specific Configuration

### Django Settings

**`backend/observer/observer/settings.py`:**
```python
import os
from pathlib import Path

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost').split(',')

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB'),
        'USER': os.getenv('POSTGRES_USER'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
        'HOST': os.getenv('POSTGRES_HOST'),
        'PORT': os.getenv('POSTGRES_PORT'),
        'OPTIONS': {
            'sslmode': 'require' if os.getenv('ENVIRONMENT') == 'production' else 'prefer',
        },
        'CONN_MAX_AGE': int(os.getenv('DATABASE_CONN_MAX_AGE', '600')),
        'CONN_HEALTH_CHECKS': os.getenv('DATABASE_CONN_HEALTH_CHECKS', 'True').lower() == 'true',
    }
}

# Cache
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('CACHE_URL', 'redis://redis:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'CONNECTION_POOL_KWARGS': {'max_connections': 50},
        },
        'TIMEOUT': int(os.getenv('CACHE_TIMEOUT', '3600')),
        'KEY_PREFIX': os.getenv('CACHE_KEY_PREFIX', 'observer_eye'),
    }
}

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.getenv('STATIC_ROOT', BASE_DIR / 'static')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.getenv('MEDIA_ROOT', BASE_DIR / 'media')

# Security settings
if os.getenv('ENVIRONMENT') == 'production':
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# CORS settings
CORS_ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', '').split(',')
CORS_ALLOW_CREDENTIALS = True

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
    },
    'handlers': {
        'file': {
            'level': os.getenv('LOG_LEVEL', 'INFO'),
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.getenv('LOG_FILE', 'observer.log'),
            'maxBytes': int(os.getenv('LOG_MAX_SIZE', '10485760')),
            'backupCount': int(os.getenv('LOG_BACKUP_COUNT', '5')),
            'formatter': 'json',
        },
        'console': {
            'level': os.getenv('LOG_LEVEL', 'INFO'),
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': os.getenv('LOG_LEVEL', 'INFO'),
    },
}
```

### FastAPI Configuration

**`middleware/config.py`:**
```python
import os
from typing import List
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Service URLs
    django_backend_url: str = os.getenv("DJANGO_BACKEND_URL", "http://localhost:8000")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Performance
    worker_processes: int = int(os.getenv("WORKER_PROCESSES", "1"))
    max_connections: int = int(os.getenv("MAX_CONNECTIONS", "100"))
    keepalive_timeout: int = int(os.getenv("KEEPALIVE_TIMEOUT", "5"))
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    
    # Data Processing
    batch_size: int = int(os.getenv("BATCH_SIZE", "1000"))
    max_batch_size: int = int(os.getenv("MAX_BATCH_SIZE", "10000"))
    processing_timeout: int = int(os.getenv("PROCESSING_TIMEOUT", "60"))
    validation_level: str = os.getenv("VALIDATION_LEVEL", "moderate")
    
    # Caching
    cache_default_ttl: int = int(os.getenv("CACHE_DEFAULT_TTL", "3600"))
    cache_max_size: int = int(os.getenv("CACHE_MAX_SIZE", "1000000"))
    cache_compression: bool = os.getenv("CACHE_COMPRESSION", "True").lower() == "true"
    cache_metrics: bool = os.getenv("CACHE_METRICS", "True").lower() == "true"
    
    # Rate Limiting
    rate_limit_enabled: bool = os.getenv("RATE_LIMIT_ENABLED", "True").lower() == "true"
    rate_limit_requests: int = int(os.getenv("RATE_LIMIT_REQUESTS", "1000"))
    rate_limit_window: int = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))
    
    # Security
    cors_allow_credentials: bool = os.getenv("CORS_ALLOW_CREDENTIALS", "True").lower() == "true"
    cors_max_age: int = int(os.getenv("CORS_MAX_AGE", "86400"))
    trusted_hosts: List[str] = os.getenv("TRUSTED_HOSTS", "localhost").split(",")
    
    # Monitoring
    opentelemetry_endpoint: str = os.getenv("OPENTELEMETRY_ENDPOINT", "")
    opentelemetry_service_name: str = os.getenv("OPENTELEMETRY_SERVICE_NAME", "observer-eye-middleware")
    metrics_enabled: bool = os.getenv("METRICS_ENABLED", "True").lower() == "true"
    health_check_interval: int = int(os.getenv("HEALTH_CHECK_INTERVAL", "30"))
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_format: str = os.getenv("LOG_FORMAT", "json")
    log_file: str = os.getenv("LOG_FILE", "middleware.log")

    class Config:
        env_file = ".env"

settings = Settings()
```

### Angular Configuration

**`dashboard/src/environments/environment.prod.ts`:**
```typescript
export const environment = {
  production: true,
  apiBaseUrl: process.env['API_BASE_URL'] || 'http://localhost:8400',
  backendUrl: process.env['BACKEND_URL'] || 'http://localhost:8000',
  websocketUrl: process.env['WEBSOCKET_URL'] || 'ws://localhost:8400/ws',
  
  // Authentication
  auth: {
    tokenKey: process.env['AUTH_TOKEN_KEY'] || 'observer_eye_token',
    refreshKey: process.env['AUTH_REFRESH_KEY'] || 'observer_eye_refresh',
    tokenExpiry: parseInt(process.env['AUTH_TOKEN_EXPIRY'] || '86400'),
  },
  
  // OAuth Providers
  oauth: {
    github: process.env['OAUTH_GITHUB_ENABLED'] === 'true',
    google: process.env['OAUTH_GOOGLE_ENABLED'] === 'true',
    gitlab: process.env['OAUTH_GITLAB_ENABLED'] === 'true',
    microsoft: process.env['OAUTH_MICROSOFT_ENABLED'] === 'true',
  },
  
  // UI Configuration
  ui: {
    defaultTheme: process.env['DEFAULT_THEME'] || 'light',
    defaultLanguage: process.env['DEFAULT_LANGUAGE'] || 'en',
    timezone: process.env['TIMEZONE'] || 'UTC',
    dateFormat: process.env['DATE_FORMAT'] || 'YYYY-MM-DD',
    timeFormat: process.env['TIME_FORMAT'] || 'HH:mm:ss',
  },
  
  // Dashboard Settings
  dashboard: {
    refreshInterval: parseInt(process.env['DASHBOARD_REFRESH_INTERVAL'] || '30000'),
    chartAnimationDuration: parseInt(process.env['CHART_ANIMATION_DURATION'] || '300'),
    maxWidgets: parseInt(process.env['MAX_DASHBOARD_WIDGETS'] || '20'),
    autoSaveInterval: parseInt(process.env['AUTO_SAVE_INTERVAL'] || '60000'),
  },
  
  // Feature Flags
  features: {
    realTimeUpdates: process.env['FEATURE_REAL_TIME_UPDATES'] === 'true',
    advancedAnalytics: process.env['FEATURE_ADVANCED_ANALYTICS'] === 'true',
    customDashboards: process.env['FEATURE_CUSTOM_DASHBOARDS'] === 'true',
    exportData: process.env['FEATURE_EXPORT_DATA'] === 'true',
  },
  
  // Monitoring
  monitoring: {
    sentryDsn: process.env['SENTRY_DSN'] || '',
    analyticsEnabled: process.env['ANALYTICS_ENABLED'] === 'true',
    errorReporting: process.env['ERROR_REPORTING'] === 'true',
  },
};
```

## Docker Configuration

### Docker Compose Configuration

**`docker-compose.yml`:**
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init-db.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=${DEBUG}
      - ENVIRONMENT=${ENVIRONMENT}
    volumes:
      - ./backend/logs:/app/logs
      - ./backend/media:/app/media
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 10s
      retries: 3

  middleware:
    build:
      context: ./middleware
      dockerfile: Dockerfile
    environment:
      - DJANGO_BACKEND_URL=http://backend:8000
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - ENVIRONMENT=${ENVIRONMENT}
      - DEBUG=${DEBUG}
    volumes:
      - ./middleware/logs:/app/logs
    ports:
      - "8400:8400"
    depends_on:
      backend:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8400/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  dashboard:
    build:
      context: ./dashboard
      dockerfile: Dockerfile
    environment:
      - API_BASE_URL=http://localhost:8400
      - ENVIRONMENT=${ENVIRONMENT}
    ports:
      - "80:80"
    depends_on:
      middleware:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:80/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:
  redis_data:

networks:
  default:
    driver: bridge
```

### Production Docker Compose

**`docker-compose.prod.yml`:**
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD} --maxmemory 1gb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=false
      - ENVIRONMENT=production
    volumes:
      - ./logs:/app/logs
      - ./media:/app/media
    restart: unless-stopped
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 2G
          cpus: '1.0'

  middleware:
    build:
      context: ./middleware
      dockerfile: Dockerfile
    environment:
      - DJANGO_BACKEND_URL=http://backend:8000
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - ENVIRONMENT=production
      - DEBUG=false
      - WORKER_PROCESSES=4
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 1G
          cpus: '1.0'

  dashboard:
    build:
      context: ./dashboard
      dockerfile: Dockerfile
    environment:
      - API_BASE_URL=https://your-domain.com/api
      - ENVIRONMENT=production
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'

  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - dashboard
      - middleware
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

## Monitoring Configuration

### OpenTelemetry Configuration

**`otel-config.yaml`:**
```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 1s
    send_batch_size: 1024
  memory_limiter:
    limit_mib: 512

exporters:
  jaeger:
    endpoint: jaeger:14250
    tls:
      insecure: true
  prometheus:
    endpoint: "0.0.0.0:8889"

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [jaeger]
    metrics:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [prometheus]
```

### Prometheus Configuration

**`prometheus.yml`:**
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

scrape_configs:
  - job_name: 'observer-eye-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'observer-eye-middleware'
    static_configs:
      - targets: ['middleware:8400']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']
    scrape_interval: 30s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
    scrape_interval: 30s

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

## Security Configuration

### SSL/TLS Configuration

**Nginx SSL Configuration:**
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/certificate.crt;
    ssl_certificate_key /etc/nginx/ssl/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' ws: wss:;" always;

    location / {
        proxy_pass http://dashboard:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://middleware:8400/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

### Firewall Configuration

**UFW Rules (Ubuntu):**
```bash
# Allow SSH
ufw allow 22/tcp

# Allow HTTP and HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Allow specific application ports (if needed)
ufw allow from 10.0.0.0/8 to any port 5432  # PostgreSQL
ufw allow from 10.0.0.0/8 to any port 6379  # Redis

# Enable firewall
ufw enable
```

## Backup Configuration

### Database Backup Script

**`scripts/backup-db.sh`:**
```bash
#!/bin/bash

# Configuration
DB_NAME=${POSTGRES_DB}
DB_USER=${POSTGRES_USER}
DB_PASSWORD=${POSTGRES_PASSWORD}
DB_HOST=${POSTGRES_HOST:-localhost}
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/observer_eye_${DATE}.sql"

# Create backup directory
mkdir -p ${BACKUP_DIR}

# Create backup
PGPASSWORD=${DB_PASSWORD} pg_dump -h ${DB_HOST} -U ${DB_USER} -d ${DB_NAME} > ${BACKUP_FILE}

# Compress backup
gzip ${BACKUP_FILE}

# Remove backups older than 7 days
find ${BACKUP_DIR} -name "observer_eye_*.sql.gz" -mtime +7 -delete

echo "Backup completed: ${BACKUP_FILE}.gz"
```

### Automated Backup with Cron

**Crontab entry:**
```bash
# Daily backup at 2 AM
0 2 * * * /path/to/scripts/backup-db.sh >> /var/log/backup.log 2>&1

# Weekly full system backup
0 3 * * 0 /path/to/scripts/full-backup.sh >> /var/log/backup.log 2>&1
```

## Performance Tuning

### PostgreSQL Configuration

**`postgresql.conf` optimizations:**
```ini
# Memory settings
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

# Checkpoint settings
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100

# Connection settings
max_connections = 200
```

### Redis Configuration

**`redis.conf` optimizations:**
```ini
# Memory management
maxmemory 1gb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000

# Network
tcp-keepalive 300
timeout 0

# Logging
loglevel notice
logfile /var/log/redis/redis-server.log
```

## Troubleshooting Configuration

### Common Configuration Issues

1. **Database Connection Issues**
   - Check `DATABASE_URL` format
   - Verify PostgreSQL is running
   - Check firewall rules
   - Verify credentials

2. **Redis Connection Issues**
   - Check `REDIS_URL` format
   - Verify Redis password
   - Check Redis memory limits
   - Verify network connectivity

3. **CORS Issues**
   - Check `ALLOWED_ORIGINS` settings
   - Verify frontend URL configuration
   - Check CORS middleware order

4. **SSL/TLS Issues**
   - Verify certificate paths
   - Check certificate validity
   - Verify SSL redirect settings
   - Check security headers

### Configuration Validation

**Validation script:**
```bash
#!/bin/bash

echo "Validating Observer Eye Configuration..."

# Check environment variables
required_vars=("SECRET_KEY" "POSTGRES_DB" "POSTGRES_USER" "POSTGRES_PASSWORD" "REDIS_URL")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "ERROR: $var is not set"
        exit 1
    fi
done

# Check database connectivity
if ! pg_isready -h ${POSTGRES_HOST} -p ${POSTGRES_PORT} -U ${POSTGRES_USER}; then
    echo "ERROR: Cannot connect to PostgreSQL"
    exit 1
fi

# Check Redis connectivity
if ! redis-cli -u ${REDIS_URL} ping > /dev/null; then
    echo "ERROR: Cannot connect to Redis"
    exit 1
fi

echo "Configuration validation passed!"
```

For more detailed configuration examples and troubleshooting, see the [Installation Guide](installation.md) and [API Documentation](api.md).