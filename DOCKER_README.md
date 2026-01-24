# Observer-Eye Platform - Docker Infrastructure

This document provides comprehensive information about the Docker containerization setup for the Observer-Eye observability platform.

## 🏗️ Architecture Overview

The Observer-Eye platform follows a **Internet → Dashboards → Middleware → Backend** flow with the following containerized services:

### Tier 1: Entry Point (Internet-Facing)
- **Nginx Reverse Proxy**: Load balancing and SSL termination
- **Angular Frontend**: 3D visualization dashboards and BI reporting interfaces

### Tier 2: Processing Layer
- **FastAPI Middleware**: Real-time processing and analytics engines
- **Authentication Service**: JWT-based authentication and authorization
- **Stream Processing**: Real-time data correlation and processing

### Tier 3: Data and Analytics Layer
- **Django Backend**: Observability domain apps and BI data models
- **BI Analytics Container**: Business intelligence processing and report generation
- **Deep System Container**: eBPF-based kernel monitoring and payload inspection

### Tier 4: Storage Layer
- **PostgreSQL**: Operational data storage
- **ClickHouse**: Analytics data warehouse
- **Redis**: Cache and session management
- **TimescaleDB**: Time-series data storage

## 🚀 Quick Start

### Prerequisites

- Docker 20.10+ and Docker Compose 2.0+
- 8GB+ RAM (16GB recommended)
- 20GB+ free disk space
- Linux/macOS/Windows with WSL2

### 1. Clone and Setup

```bash
# Navigate to the Observer-Eye directory
cd observer-eye

# Run the automated setup script
./scripts/setup-infrastructure.sh
```

### 2. Manual Setup (Alternative)

```bash
# Create environment file
cp .env.example .env

# Edit environment variables (optional)
nano .env

# Setup Docker networks
./scripts/setup-network.sh

# Start all services
docker-compose up -d

# Check service status
docker-compose ps
```

### 3. Access the Platform

- **Frontend Dashboard**: http://localhost:4200
- **API Documentation**: http://localhost:8000/docs
- **Admin Interface**: http://localhost:8001/admin
- **Grafana Monitoring**: http://localhost:3000 (admin/admin)
- **Prometheus Metrics**: http://localhost:9090

## 📁 Directory Structure

```
observer-eye/
├── docker-compose.yml              # Development environment
├── docker-compose.prod.yml         # Production environment
├── .env.example                    # Environment template
├── .env.prod.example              # Production environment template
├── .dockerignore                  # Global Docker ignore
├── docker/                        # Docker configurations
│   ├── base/                      # Base images with security hardening
│   └── nginx/                     # Nginx configurations
├── database/                      # Database initialization
│   ├── postgres/init/             # PostgreSQL setup scripts
│   ├── clickhouse/               # ClickHouse configuration
│   ├── redis/                    # Redis configuration
│   └── timescaledb/init/         # TimescaleDB setup scripts
├── monitoring/                    # Monitoring configuration
│   ├── prometheus/               # Prometheus configuration
│   └── grafana/                  # Grafana provisioning
├── scripts/                      # Setup and utility scripts
├── data/                         # Persistent data (created at runtime)
├── logs/                         # Service logs (created at runtime)
└── backups/                      # Database backups (created at runtime)
```

## 🔧 Configuration

### Environment Variables

Key environment variables in `.env`:

```bash
# Application Environment
ENVIRONMENT=development
NODE_ENV=development

# Database Configuration
DATABASE_URL=postgresql://observer:observer_pass@postgres:5432/observability
WAREHOUSE_URL=clickhouse://analytics:analytics_pass@clickhouse:8123/warehouse
REDIS_URL=redis://redis:6379/0

# Security (Change in production!)
JWT_SECRET_KEY=your-super-secret-jwt-key
DJANGO_SECRET_KEY=your-django-secret-key
```

### Service Ports

| Service | Port | Description |
|---------|------|-------------|
| Nginx | 80, 443 | Reverse proxy and SSL termination |
| Frontend | 4200 | Angular development server |
| Middleware | 8000 | FastAPI application |
| Backend | 8001 | Django application |
| BI Analytics | 8002 | Business intelligence service |
| Deep System | 8003 | eBPF monitoring service |
| Auth Service | 8004 | Authentication service |
| PostgreSQL | 5432 | Operational database |
| ClickHouse | 8123, 9000 | Analytics warehouse |
| Redis | 6379 | Cache and sessions |
| TimescaleDB | 5433 | Time-series database |
| Grafana | 3000 | Monitoring dashboards |
| Prometheus | 9090 | Metrics collection |
| Jupyter | 8888 | Data science notebooks |

## 🐳 Docker Commands

### Basic Operations

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View service status
docker-compose ps

# View logs for all services
docker-compose logs -f

# View logs for specific service
docker-compose logs -f middleware

# Restart a specific service
docker-compose restart middleware

# Rebuild and restart a service
docker-compose up -d --build middleware
```

### Development Workflow

```bash
# Start only infrastructure services
docker-compose up -d postgres redis clickhouse timescaledb

# Start application services for development
docker-compose up -d middleware backend bi-analytics

# Watch logs during development
docker-compose logs -f middleware backend
```

### Production Deployment

```bash
# Use production configuration
docker-compose -f docker-compose.prod.yml up -d

# Scale services (production)
docker-compose -f docker-compose.prod.yml up -d --scale middleware=3 --scale backend=2
```

## 🔍 Monitoring and Observability

### Built-in Monitoring

The platform includes comprehensive monitoring:

- **Prometheus**: Metrics collection from all services
- **Grafana**: Pre-configured dashboards for infrastructure and application monitoring
- **Health Checks**: All services include health check endpoints
- **Log Aggregation**: Centralized logging with structured output

### Key Metrics

- Service availability and response times
- Database performance and connection pools
- Cache hit rates and memory usage
- Deep system metrics (eBPF data)
- Business intelligence processing metrics

### Alerting

Pre-configured alerts for:
- Service downtime
- High error rates
- Resource exhaustion
- Security events
- Data quality issues

## 🔒 Security

### Security Features

- **Non-root containers**: All services run as non-root users
- **Network isolation**: Services communicate through dedicated networks
- **Secrets management**: Sensitive data handled through Docker secrets
- **Security headers**: Comprehensive HTTP security headers via Nginx
- **Image scanning**: Base images with security hardening

### Security Best Practices

1. **Change default passwords** in production
2. **Use Docker secrets** for sensitive data
3. **Enable SSL/TLS** for external access
4. **Regular security updates** for base images
5. **Network segmentation** between tiers

## 🚀 Production Deployment

### Production Checklist

- [ ] Update all passwords and secrets
- [ ] Configure SSL certificates
- [ ] Set up external load balancer
- [ ] Configure backup strategies
- [ ] Set up log aggregation
- [ ] Configure monitoring alerts
- [ ] Test disaster recovery procedures

### Production Configuration

```bash
# Copy production environment template
cp .env.prod.example .env.prod

# Update production secrets
nano .env.prod

# Deploy with production configuration
docker-compose -f docker-compose.prod.yml up -d
```

### Scaling

```bash
# Scale middleware instances
docker-compose -f docker-compose.prod.yml up -d --scale middleware=5

# Scale backend instances
docker-compose -f docker-compose.prod.yml up -d --scale backend=3

# Scale BI analytics instances
docker-compose -f docker-compose.prod.yml up -d --scale bi-analytics=2
```

## 🔧 Troubleshooting

### Common Issues

#### Services Won't Start

```bash
# Check Docker daemon
docker info

# Check available resources
docker system df
docker system prune  # Clean up if needed

# Check service logs
docker-compose logs [service-name]
```

#### Database Connection Issues

```bash
# Check database status
docker-compose exec postgres pg_isready -U observer
docker-compose exec redis redis-cli ping
docker-compose exec clickhouse clickhouse-client --query "SELECT 1"

# Reset database containers
docker-compose down
docker volume prune  # WARNING: This removes all data
docker-compose up -d
```

#### Performance Issues

```bash
# Check resource usage
docker stats

# Check service health
curl http://localhost:8000/health
curl http://localhost:8001/health

# Monitor logs for errors
docker-compose logs -f --tail=100
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
docker-compose up -d

# Run services in foreground for debugging
docker-compose up middleware backend
```

## 📊 Data Management

### Backup and Restore

```bash
# Backup PostgreSQL
docker-compose exec postgres pg_dump -U observer observability > backup.sql

# Backup ClickHouse
docker-compose exec clickhouse clickhouse-client --query "BACKUP DATABASE warehouse TO Disk('backups', 'warehouse_backup')"

# Restore PostgreSQL
docker-compose exec -T postgres psql -U observer observability < backup.sql
```

### Data Volumes

Persistent data is stored in Docker volumes:

- `postgres_data`: PostgreSQL database files
- `clickhouse_data`: ClickHouse database files
- `redis_data`: Redis persistence files
- `timescale_data`: TimescaleDB files
- `grafana_data`: Grafana dashboards and settings
- `prometheus_data`: Prometheus metrics storage

## 🔄 Updates and Maintenance

### Updating Services

```bash
# Pull latest images
docker-compose pull

# Restart with new images
docker-compose up -d

# Clean up old images
docker image prune
```

### Database Migrations

```bash
# Run Django migrations
docker-compose exec backend python manage.py migrate

# Check migration status
docker-compose exec backend python manage.py showmigrations
```

## 📚 Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Observer-Eye API Documentation](http://localhost:8000/docs)
- [Grafana Dashboard Documentation](http://localhost:3000)
- [Prometheus Query Documentation](http://localhost:9090)

## 🆘 Support

For issues and questions:

1. Check the troubleshooting section above
2. Review service logs: `docker-compose logs -f [service]`
3. Check service health endpoints
4. Consult the monitoring dashboards in Grafana

## 📝 License

This Docker infrastructure is part of the Observer-Eye observability platform.