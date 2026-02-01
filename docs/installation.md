# Observer Eye Platform - Installation Guide

## Prerequisites

### System Requirements

**Minimum Requirements:**
- CPU: 2 cores
- RAM: 4GB
- Storage: 10GB free space
- Network: Internet connection for package downloads

**Recommended Requirements:**
- CPU: 4+ cores
- RAM: 8GB+
- Storage: 20GB+ free space
- Network: High-speed internet connection

### Software Dependencies

**Required:**
- Docker 20.10+ and Docker Compose 2.0+
- Git for source code management

**Optional (for development):**
- Node.js 18+ and npm (for frontend development)
- Python 3.11+ (for backend development)
- PostgreSQL 13+ (for production database)
- Redis 6+ (for caching)

## Quick Start with Docker Compose

### 1. Clone the Repository

```bash
git clone <repository-url>
cd observer-eye
```

### 2. Environment Configuration

Create environment files for each layer:

```bash
# Copy example environment files
cp .env.example .env
cp backend/.env.example backend/.env
cp middleware/.env.example middleware/.env
cp dashboard/.env.example dashboard/.env
```

### 3. Configure Environment Variables

Edit the `.env` files with your specific configuration:

**Root `.env`:**
```env
# Database Configuration
POSTGRES_DB=observer_eye
POSTGRES_USER=observer_user
POSTGRES_PASSWORD=secure_password_here
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Service URLs
DJANGO_URL=http://backend:8000
FASTAPI_URL=http://middleware:8400
FRONTEND_URL=http://dashboard:80

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here

# Environment
ENVIRONMENT=production
DEBUG=false
```

**Backend `backend/.env`:**
```env
# Django Configuration
SECRET_KEY=your-django-secret-key
DEBUG=false
ALLOWED_HOSTS=localhost,127.0.0.1,backend

# Database
DATABASE_URL=postgresql://observer_user:secure_password_here@postgres:5432/observer_eye

# OAuth Configuration (optional)
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

**Middleware `middleware/.env`:**
```env
# FastAPI Configuration
DJANGO_BACKEND_URL=http://backend:8000
REDIS_URL=redis://redis:6379/0
ENVIRONMENT=production

# Performance
WORKER_PROCESSES=4
MAX_CONNECTIONS=1000
```

**Dashboard `dashboard/.env`:**
```env
# Angular Configuration
API_BASE_URL=http://localhost:8400
ENVIRONMENT=production
```

### 4. Deploy with Docker Compose

```bash
# Build and start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### 5. Initialize the Database

```bash
# Run Django migrations
docker-compose exec backend python manage.py migrate

# Create superuser (optional)
docker-compose exec backend python manage.py createsuperuser

# Initialize settings
docker-compose exec backend python manage.py initialize_settings
```

### 6. Verify Installation

Open your browser and navigate to:
- **Frontend Dashboard**: http://localhost:80
- **FastAPI Documentation**: http://localhost:8400/docs
- **Django Admin**: http://localhost:8000/admin

## Development Setup

### Frontend Development (Angular)

```bash
cd dashboard

# Install dependencies
npm install

# Start development server
npm start

# Run tests
npm test

# Build for production
npm run build
```

**Development Commands:**
```bash
# Lint code
npm run lint

# Format code
npm run format

# Serve SSR build
npm run serve:ssr:dashboard

# Analyze bundle
npm run analyze
```

### Middleware Development (FastAPI)

```bash
cd middleware

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start development server
python main.py

# Run tests
pytest

# Run with hot reload
uvicorn main:app --reload --host 0.0.0.0 --port 8400
```

### Backend Development (Django)

```bash
cd backend/observer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver 0.0.0.0:8000

# Run tests
python manage.py test
# or
pytest
```

**Django Management Commands:**
```bash
# Create migrations
python manage.py makemigrations

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic

# Initialize OAuth providers
python manage.py setup_oauth_providers

# Initialize default settings
python manage.py initialize_settings
```

## Production Deployment

### Docker Production Configuration

Use the production Docker Compose file:

```bash
# Deploy with production configuration
docker-compose -f docker-compose.prod.yml up -d

# Scale services
docker-compose -f docker-compose.prod.yml up -d --scale middleware=3
```

### Environment-Specific Configuration

**Production Environment Variables:**
```env
# Security
DEBUG=false
ENVIRONMENT=production
SECURE_SSL_REDIRECT=true
SECURE_HSTS_SECONDS=31536000

# Database
DATABASE_URL=postgresql://user:password@prod-db-host:5432/observer_eye

# Caching
REDIS_URL=redis://prod-redis-host:6379/0

# Monitoring
SENTRY_DSN=your-sentry-dsn
OPENTELEMETRY_ENDPOINT=your-otel-endpoint
```

### SSL/TLS Configuration

**Nginx Configuration (for frontend):**
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;

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
    }
}
```

### Database Setup

**PostgreSQL Production Setup:**
```sql
-- Create database and user
CREATE DATABASE observer_eye;
CREATE USER observer_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE observer_eye TO observer_user;

-- Configure for production
ALTER DATABASE observer_eye SET timezone TO 'UTC';
```

**Database Optimization:**
```sql
-- Create indexes for performance
CREATE INDEX idx_analytics_timestamp ON analytics_analyticsdata(timestamp);
CREATE INDEX idx_metrics_source ON appmetrics_applicationmetric(source);
CREATE INDEX idx_logs_level ON core_auditlog(level);
```

## Configuration

### Application Configuration

**Django Settings:**
```python
# settings/production.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB'),
        'USER': os.getenv('POSTGRES_USER'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
        'HOST': os.getenv('POSTGRES_HOST'),
        'PORT': os.getenv('POSTGRES_PORT'),
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

**FastAPI Configuration:**
```python
# middleware/config.py
class Settings:
    django_backend_url: str = os.getenv("DJANGO_BACKEND_URL")
    redis_url: str = os.getenv("REDIS_URL")
    environment: str = os.getenv("ENVIRONMENT", "development")
    worker_processes: int = int(os.getenv("WORKER_PROCESSES", "1"))
    max_connections: int = int(os.getenv("MAX_CONNECTIONS", "100"))
```

### Monitoring Configuration

**OpenTelemetry Setup:**
```python
# Configure OpenTelemetry
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

otlp_exporter = OTLPSpanExporter(
    endpoint=os.getenv("OPENTELEMETRY_ENDPOINT"),
    headers={"api-key": os.getenv("OPENTELEMETRY_API_KEY")}
)

span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)
```

## Troubleshooting

### Common Issues

**1. Container Build Failures**
```bash
# Clear Docker cache
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache

# Check build logs
docker-compose logs <service-name>
```

**2. Database Connection Issues**
```bash
# Check database container
docker-compose exec postgres psql -U observer_user -d observer_eye

# Verify environment variables
docker-compose exec backend env | grep DATABASE

# Check network connectivity
docker-compose exec backend ping postgres
```

**3. Permission Issues**
```bash
# Fix file permissions
sudo chown -R $USER:$USER .

# Check container user
docker-compose exec backend whoami
```

**4. Port Conflicts**
```bash
# Check port usage
netstat -tulpn | grep :80
netstat -tulpn | grep :8000
netstat -tulpn | grep :8400

# Stop conflicting services
sudo systemctl stop apache2  # or nginx
```

### Performance Tuning

**Database Optimization:**
```sql
-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM analytics_analyticsdata WHERE timestamp > NOW() - INTERVAL '1 hour';

-- Update table statistics
ANALYZE;

-- Vacuum tables
VACUUM ANALYZE;
```

**Redis Optimization:**
```bash
# Monitor Redis performance
docker-compose exec redis redis-cli monitor

# Check memory usage
docker-compose exec redis redis-cli info memory

# Configure Redis
# Add to redis.conf:
maxmemory 2gb
maxmemory-policy allkeys-lru
```

**Application Performance:**
```bash
# Monitor container resources
docker stats

# Check application logs
docker-compose logs -f --tail=100 middleware

# Profile Python applications
pip install py-spy
py-spy top --pid <process-id>
```

### Backup and Recovery

**Database Backup:**
```bash
# Create backup
docker-compose exec postgres pg_dump -U observer_user observer_eye > backup.sql

# Restore backup
docker-compose exec -T postgres psql -U observer_user observer_eye < backup.sql
```

**Full System Backup:**
```bash
# Backup volumes
docker run --rm -v observer-eye_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data

# Backup configuration
tar czf config_backup.tar.gz .env backend/.env middleware/.env dashboard/.env
```

## Security Considerations

### Production Security Checklist

- [ ] Change all default passwords and secrets
- [ ] Enable HTTPS with valid SSL certificates
- [ ] Configure firewall rules to restrict access
- [ ] Enable database SSL connections
- [ ] Set up regular security updates
- [ ] Configure log monitoring and alerting
- [ ] Implement backup and disaster recovery
- [ ] Review and audit user permissions
- [ ] Enable container security scanning
- [ ] Configure intrusion detection

### Security Headers

**Nginx Security Configuration:**
```nginx
# Security headers
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header X-XSS-Protection "1; mode=block";
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';";
```

## Support and Maintenance

### Log Locations

- **Frontend Logs**: `docker-compose logs dashboard`
- **Middleware Logs**: `docker-compose logs middleware`
- **Backend Logs**: `docker-compose logs backend`
- **Database Logs**: `docker-compose logs postgres`
- **Redis Logs**: `docker-compose logs redis`

### Health Checks

```bash
# Check service health
curl http://localhost:80/health
curl http://localhost:8400/health
curl http://localhost:8000/health

# Detailed health check
curl http://localhost:8400/health/detailed
```

### Updates and Upgrades

```bash
# Update to latest version
git pull origin main

# Rebuild and restart services
docker-compose down
docker-compose build
docker-compose up -d

# Run database migrations
docker-compose exec backend python manage.py migrate
```

For additional support, please refer to the [API Documentation](api.md) and [Configuration Guide](configuration.md).