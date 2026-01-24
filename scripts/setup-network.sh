#!/bin/bash

# Observer-Eye Platform - Docker Network Setup Script
# Creates and configures Docker networks for service communication

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Network configuration
NETWORK_NAME="observer-eye-network"
MONITORING_NETWORK="observer-eye-monitoring"
SUBNET="172.20.0.0/16"
MONITORING_SUBNET="172.21.0.0/16"

log_info "Setting up Observer-Eye Docker networks..."

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    log_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Create main application network
if docker network ls | grep -q "$NETWORK_NAME"; then
    log_warning "Network '$NETWORK_NAME' already exists. Skipping creation."
else
    log_info "Creating main application network: $NETWORK_NAME"
    docker network create \
        --driver bridge \
        --subnet="$SUBNET" \
        --opt com.docker.network.bridge.name=observer-eye-br0 \
        --opt com.docker.network.bridge.enable_icc=true \
        --opt com.docker.network.bridge.enable_ip_masquerade=true \
        --opt com.docker.network.driver.mtu=1500 \
        "$NETWORK_NAME"
    log_success "Created network: $NETWORK_NAME"
fi

# Create monitoring network (internal)
if docker network ls | grep -q "$MONITORING_NETWORK"; then
    log_warning "Network '$MONITORING_NETWORK' already exists. Skipping creation."
else
    log_info "Creating monitoring network: $MONITORING_NETWORK"
    docker network create \
        --driver bridge \
        --subnet="$MONITORING_SUBNET" \
        --internal \
        --opt com.docker.network.bridge.name=observer-eye-mon \
        "$MONITORING_NETWORK"
    log_success "Created internal monitoring network: $MONITORING_NETWORK"
fi

# Display network information
log_info "Network configuration:"
echo "┌─────────────────────────────────────────────────────────────┐"
echo "│ Observer-Eye Docker Networks                                │"
echo "├─────────────────────────────────────────────────────────────┤"
echo "│ Main Network: $NETWORK_NAME                     │"
echo "│ Subnet: $SUBNET                                      │"
echo "│ Purpose: Inter-service communication                        │"
echo "├─────────────────────────────────────────────────────────────┤"
echo "│ Monitoring Network: $MONITORING_NETWORK           │"
echo "│ Subnet: $MONITORING_SUBNET                                      │"
echo "│ Purpose: Internal monitoring (Prometheus, Grafana)          │"
echo "└─────────────────────────────────────────────────────────────┘"

# Verify networks
log_info "Verifying network creation..."
if docker network inspect "$NETWORK_NAME" >/dev/null 2>&1; then
    log_success "Main network verified: $NETWORK_NAME"
else
    log_error "Failed to create main network: $NETWORK_NAME"
    exit 1
fi

if docker network inspect "$MONITORING_NETWORK" >/dev/null 2>&1; then
    log_success "Monitoring network verified: $MONITORING_NETWORK"
else
    log_error "Failed to create monitoring network: $MONITORING_NETWORK"
    exit 1
fi

log_success "Docker networks setup completed successfully!"

# Display next steps
echo ""
log_info "Next steps:"
echo "1. Run 'docker-compose up -d' to start the development environment"
echo "2. Run 'docker-compose -f docker-compose.prod.yml up -d' for production"
echo "3. Use 'docker network ls' to view all networks"
echo "4. Use 'docker network inspect $NETWORK_NAME' for detailed network info"