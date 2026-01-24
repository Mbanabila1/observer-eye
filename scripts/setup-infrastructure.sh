#!/bin/bash

# Observer-Eye Platform - Complete Infrastructure Setup Script
# Sets up the entire Docker infrastructure for the observability platform

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"

# Function to check prerequisites
check_prerequisites() {
    log_step "Checking prerequisites..."
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker and try again."
        exit 1
    fi
    
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    
    # Check if Docker Compose is available
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not available. Please install Docker Compose and try again."
        exit 1
    fi
    
    # Check available disk space (minimum 10GB)
    available_space=$(df "$PROJECT_ROOT" | awk 'NR==2 {print $4}')
    if [ "$available_space" -lt 10485760 ]; then  # 10GB in KB
        log_warning "Less than 10GB of disk space available. Observer-Eye may require more space."
    fi
    
    # Check available memory (minimum 8GB recommended)
    available_memory=$(free -m | awk 'NR==2{printf "%.0f", $7}')
    if [ "$available_memory" -lt 8192 ]; then  # 8GB in MB
        log_warning "Less than 8GB of available memory. Performance may be impacted."
    fi
    
    log_success "Prerequisites check completed"
}

# Function to setup environment
setup_environment() {
    log_step "Setting up environment configuration..."
    
    if [ ! -f "$ENV_FILE" ]; then
        log_info "Creating .env file from template..."
        cp "$PROJECT_ROOT/.env.example" "$ENV_FILE"
        
        # Generate secure secrets
        JWT_SECRET=$(openssl rand -base64 32 2>/dev/null || head -c 32 /dev/urandom | base64)
        DJANGO_SECRET=$(openssl rand -base64 50 2>/dev/null || head -c 50 /dev/urandom | base64)
        MFA_SECRET=$(openssl rand -base64 32 2>/dev/null || head -c 32 /dev/urandom | base64)
        GRAFANA_SECRET=$(openssl rand -base64 32 2>/dev/null || head -c 32 /dev/urandom | base64)
        
        # Update secrets in .env file
        sed -i.bak "s/your-super-secret-jwt-key-change-this-in-production/$JWT_SECRET/g" "$ENV_FILE"
        sed -i.bak "s/your-django-secret-key-change-this-in-production/$DJANGO_SECRET/g" "$ENV_FILE"
        sed -i.bak "s/your-mfa-secret-key-change-this-in-production/$MFA_SECRET/g" "$ENV_FILE"
        sed -i.bak "s/your-grafana-secret-key/$GRAFANA_SECRET/g" "$ENV_FILE"
        
        # Clean up backup file
        rm -f "$ENV_FILE.bak"
        
        log_success "Environment file created with secure secrets"
    else
        log_info "Environment file already exists"
    fi
}

# Function to create necessary directories
create_directories() {
    log_step "Creating necessary directories..."
    
    # Create data directories
    mkdir -p "$PROJECT_ROOT/data/postgres"
    mkdir -p "$PROJECT_ROOT/data/clickhouse"
    mkdir -p "$PROJECT_ROOT/data/redis"
    mkdir -p "$PROJECT_ROOT/data/timescaledb"
    mkdir -p "$PROJECT_ROOT/data/grafana"
    mkdir -p "$PROJECT_ROOT/data/prometheus"
    
    # Create log directories
    mkdir -p "$PROJECT_ROOT/logs/nginx"
    mkdir -p "$PROJECT_ROOT/logs/postgres"
    mkdir -p "$PROJECT_ROOT/logs/clickhouse"
    mkdir -p "$PROJECT_ROOT/logs/redis"
    
    # Create SSL directory
    mkdir -p "$PROJECT_ROOT/ssl/certs"
    mkdir -p "$PROJECT_ROOT/ssl/private"
    
    # Create backup directories
    mkdir -p "$PROJECT_ROOT/backups/postgres"
    mkdir -p "$PROJECT_ROOT/backups/clickhouse"
    mkdir -p "$PROJECT_ROOT/backups/timescaledb"
    
    # Create notebooks directory for Jupyter
    mkdir -p "$PROJECT_ROOT/notebooks"
    
    # Create monitoring dashboard directories
    mkdir -p "$PROJECT_ROOT/monitoring/grafana/provisioning/dashboards/services"
    mkdir -p "$PROJECT_ROOT/monitoring/grafana/provisioning/dashboards/infrastructure"
    mkdir -p "$PROJECT_ROOT/monitoring/grafana/provisioning/dashboards/bi"
    mkdir -p "$PROJECT_ROOT/monitoring/grafana/provisioning/dashboards/security"
    mkdir -p "$PROJECT_ROOT/monitoring/grafana/provisioning/dashboards/deep-system"
    mkdir -p "$PROJECT_ROOT/monitoring/grafana/provisioning/dashboards/apm"
    mkdir -p "$PROJECT_ROOT/monitoring/grafana/provisioning/dashboards/executive"
    
    log_success "Directories created successfully"
}

# Function to setup Docker networks
setup_networks() {
    log_step "Setting up Docker networks..."
    
    # Run the network setup script
    if [ -f "$PROJECT_ROOT/scripts/setup-network.sh" ]; then
        bash "$PROJECT_ROOT/scripts/setup-network.sh"
    else
        log_warning "Network setup script not found, creating networks manually..."
        
        # Create main network
        if ! docker network ls | grep -q "observer-eye-network"; then
            docker network create \
                --driver bridge \
                --subnet=172.20.0.0/16 \
                observer-eye-network
            log_success "Created observer-eye-network"
        fi
        
        # Create monitoring network
        if ! docker network ls | grep -q "observer-eye-monitoring"; then
            docker network create \
                --driver bridge \
                --subnet=172.21.0.0/16 \
                --internal \
                observer-eye-monitoring
            log_success "Created observer-eye-monitoring network"
        fi
    fi
}

# Function to validate configuration files
validate_configuration() {
    log_step "Validating configuration files..."
    
    # Check Docker Compose file
    if [ -f "$COMPOSE_FILE" ]; then
        if docker-compose -f "$COMPOSE_FILE" config >/dev/null 2>&1 || docker compose -f "$COMPOSE_FILE" config >/dev/null 2>&1; then
            log_success "Docker Compose configuration is valid"
        else
            log_error "Docker Compose configuration is invalid"
            exit 1
        fi
    else
        log_error "Docker Compose file not found: $COMPOSE_FILE"
        exit 1
    fi
    
    # Check nginx configuration
    if [ -f "$PROJECT_ROOT/docker/nginx/nginx.conf" ]; then
        log_success "Nginx configuration found"
    else
        log_warning "Nginx configuration not found"
    fi
    
    # Check database initialization scripts
    if [ -f "$PROJECT_ROOT/database/postgres/init/01-init-databases.sql" ]; then
        log_success "PostgreSQL initialization script found"
    else
        log_warning "PostgreSQL initialization script not found"
    fi
    
    if [ -f "$PROJECT_ROOT/database/clickhouse/init/01-create-warehouse.sql" ]; then
        log_success "ClickHouse initialization script found"
    else
        log_warning "ClickHouse initialization script not found"
    fi
}

# Function to pull Docker images
pull_images() {
    log_step "Pulling Docker images..."
    
    # Use docker-compose to pull images
    if command -v docker-compose &> /dev/null; then
        docker-compose -f "$COMPOSE_FILE" pull
    else
        docker compose -f "$COMPOSE_FILE" pull
    fi
    
    log_success "Docker images pulled successfully"
}

# Function to start services
start_services() {
    log_step "Starting Observer-Eye services..."
    
    # Start services in dependency order
    log_info "Starting infrastructure services..."
    if command -v docker-compose &> /dev/null; then
        docker-compose -f "$COMPOSE_FILE" up -d postgres redis clickhouse timescaledb
    else
        docker compose -f "$COMPOSE_FILE" up -d postgres redis clickhouse timescaledb
    fi
    
    # Wait for databases to be ready
    log_info "Waiting for databases to be ready..."
    sleep 30
    
    # Start application services
    log_info "Starting application services..."
    if command -v docker-compose &> /dev/null; then
        docker-compose -f "$COMPOSE_FILE" up -d
    else
        docker compose -f "$COMPOSE_FILE" up -d
    fi
    
    log_success "All services started successfully"
}

# Function to verify services
verify_services() {
    log_step "Verifying service health..."
    
    # Wait for services to be ready
    sleep 60
    
    # Check service health
    services=("postgres" "redis" "clickhouse" "timescaledb")
    
    for service in "${services[@]}"; do
        if docker ps --filter "name=observer-eye-$service" --filter "status=running" | grep -q "$service"; then
            log_success "$service is running"
        else
            log_error "$service is not running"
        fi
    done
    
    # Check if ports are accessible
    ports=("5432" "6379" "8123" "5433")
    for port in "${ports[@]}"; do
        if nc -z localhost "$port" 2>/dev/null; then
            log_success "Port $port is accessible"
        else
            log_warning "Port $port is not accessible"
        fi
    done
}

# Function to display access information
display_access_info() {
    log_step "Setup completed! Access information:"
    
    echo ""
    echo "┌─────────────────────────────────────────────────────────────┐"
    echo "│                    Observer-Eye Platform                    │"
    echo "├─────────────────────────────────────────────────────────────┤"
    echo "│ Service Access URLs:                                        │"
    echo "│                                                             │"
    echo "│ 🌐 Frontend (Angular):     http://localhost:4200           │"
    echo "│ 🔧 API (FastAPI):          http://localhost:8000           │"
    echo "│ 🗄️  Admin (Django):        http://localhost:8001/admin     │"
    echo "│ 📊 BI Analytics:           http://localhost:8002           │"
    echo "│ 🔍 Deep System Monitor:    http://localhost:8003           │"
    echo "│ 🔐 Authentication:         http://localhost:8004           │"
    echo "│                                                             │"
    echo "│ Infrastructure Services:                                    │"
    echo "│                                                             │"
    echo "│ 📈 Grafana:                http://localhost:3000           │"
    echo "│    Username: admin / Password: admin                        │"
    echo "│                                                             │"
    echo "│ 📊 Prometheus:             http://localhost:9090           │"
    echo "│ 📓 Jupyter:                http://localhost:8888           │"
    echo "│                                                             │"
    echo "│ Database Connections:                                       │"
    echo "│                                                             │"
    echo "│ 🐘 PostgreSQL:             localhost:5432                  │"
    echo "│ 🏠 ClickHouse:             localhost:8123                  │"
    echo "│ ⏰ TimescaleDB:            localhost:5433                  │"
    echo "│ 🔴 Redis:                  localhost:6379                  │"
    echo "└─────────────────────────────────────────────────────────────┘"
    echo ""
    
    log_info "Next steps:"
    echo "1. Visit http://localhost:4200 to access the Observer-Eye dashboard"
    echo "2. Visit http://localhost:3000 to access Grafana monitoring"
    echo "3. Check service logs: docker-compose logs -f [service-name]"
    echo "4. Stop services: docker-compose down"
    echo "5. View this help: docker-compose ps"
    echo ""
    
    log_info "Configuration files:"
    echo "- Environment: $ENV_FILE"
    echo "- Docker Compose: $COMPOSE_FILE"
    echo "- Logs directory: $PROJECT_ROOT/logs/"
    echo "- Data directory: $PROJECT_ROOT/data/"
}

# Function to handle cleanup on error
cleanup_on_error() {
    log_error "Setup failed. Cleaning up..."
    
    # Stop any running containers
    if command -v docker-compose &> /dev/null; then
        docker-compose -f "$COMPOSE_FILE" down 2>/dev/null || true
    else
        docker compose -f "$COMPOSE_FILE" down 2>/dev/null || true
    fi
    
    exit 1
}

# Main execution
main() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║              Observer-Eye Infrastructure Setup                ║"
    echo "║                                                               ║"
    echo "║  This script will set up the complete Docker infrastructure   ║"
    echo "║  for the Observer-Eye observability platform.                ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""
    
    # Set up error handling
    trap cleanup_on_error ERR
    
    # Execute setup steps
    check_prerequisites
    setup_environment
    create_directories
    setup_networks
    validate_configuration
    pull_images
    start_services
    verify_services
    display_access_info
    
    log_success "Observer-Eye infrastructure setup completed successfully!"
}

# Parse command line arguments
case "${1:-}" in
    --help|-h)
        echo "Observer-Eye Infrastructure Setup Script"
        echo ""
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --check        Check prerequisites only"
        echo "  --env          Setup environment only"
        echo "  --pull         Pull Docker images only"
        echo "  --start        Start services only"
        echo "  --stop         Stop all services"
        echo "  --status       Show service status"
        echo "  --logs         Show service logs"
        echo ""
        exit 0
        ;;
    --check)
        check_prerequisites
        exit 0
        ;;
    --env)
        setup_environment
        exit 0
        ;;
    --pull)
        pull_images
        exit 0
        ;;
    --start)
        start_services
        exit 0
        ;;
    --stop)
        log_info "Stopping Observer-Eye services..."
        if command -v docker-compose &> /dev/null; then
            docker-compose -f "$COMPOSE_FILE" down
        else
            docker compose -f "$COMPOSE_FILE" down
        fi
        log_success "Services stopped"
        exit 0
        ;;
    --status)
        if command -v docker-compose &> /dev/null; then
            docker-compose -f "$COMPOSE_FILE" ps
        else
            docker compose -f "$COMPOSE_FILE" ps
        fi
        exit 0
        ;;
    --logs)
        if command -v docker-compose &> /dev/null; then
            docker-compose -f "$COMPOSE_FILE" logs -f
        else
            docker compose -f "$COMPOSE_FILE" logs -f
        fi
        exit 0
        ;;
    "")
        main
        ;;
    *)
        log_error "Unknown option: $1"
        echo "Use --help for usage information"
        exit 1
        ;;
esac