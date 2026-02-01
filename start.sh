#!/bin/bash

# Observer Eye Platform Startup Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating from .env.example..."
    cp .env.example .env
    print_warning "Please edit .env file with your configuration before running again."
    exit 1
fi

# Parse command line arguments
ENVIRONMENT=${1:-development}
COMPOSE_FILE="docker-compose.yml"

case $ENVIRONMENT in
    "development"|"dev")
        print_status "Starting in development mode..."
        COMPOSE_FILE="docker-compose.yml:docker-compose.override.yml"
        ;;
    "production"|"prod")
        print_status "Starting in production mode..."
        COMPOSE_FILE="docker-compose.yml:docker-compose.prod.yml"
        ;;
    *)
        print_error "Invalid environment. Use 'development' or 'production'"
        exit 1
        ;;
esac

# Export environment variables
export COMPOSE_FILE

print_status "Building and starting Observer Eye Platform..."

# Build and start services
docker-compose -f docker-compose.yml $([ "$ENVIRONMENT" = "production" ] && echo "-f docker-compose.prod.yml" || echo "-f docker-compose.override.yml") up --build -d

# Wait for services to be healthy
print_status "Waiting for services to be healthy..."
sleep 30

# Check service health
print_status "Checking service health..."

# Check database
if docker-compose exec postgres pg_isready -U observer_user -d observer_eye > /dev/null 2>&1; then
    print_status "✓ Database is healthy"
else
    print_error "✗ Database is not healthy"
fi

# Check backend
if curl -f http://localhost:8000/health/ > /dev/null 2>&1; then
    print_status "✓ Backend is healthy"
else
    print_error "✗ Backend is not healthy"
fi

# Check middleware
if curl -f http://localhost:8400/health > /dev/null 2>&1; then
    print_status "✓ Middleware is healthy"
else
    print_error "✗ Middleware is not healthy"
fi

# Check frontend
if curl -f http://localhost:80/health > /dev/null 2>&1; then
    print_status "✓ Frontend is healthy"
else
    print_error "✗ Frontend is not healthy"
fi

print_status "Observer Eye Platform is running!"
print_status "Frontend: http://localhost"
print_status "Backend API: http://localhost:8000"
print_status "Middleware API: http://localhost:8400"

print_status "To stop the platform, run: docker-compose down"
print_status "To view logs, run: docker-compose logs -f"