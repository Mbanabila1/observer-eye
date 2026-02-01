#!/bin/bash

# Observer Eye Platform Stop Script

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

# Parse command line arguments
REMOVE_VOLUMES=${1:-false}

print_status "Stopping Observer Eye Platform..."

# Stop and remove containers
docker-compose down

if [ "$REMOVE_VOLUMES" = "clean" ] || [ "$REMOVE_VOLUMES" = "--clean" ]; then
    print_warning "Removing volumes (this will delete all data)..."
    docker-compose down -v
    docker system prune -f
    print_status "All containers, networks, and volumes removed."
else
    print_status "Containers stopped. Data volumes preserved."
    print_status "To remove all data, run: ./stop.sh clean"
fi

print_status "Observer Eye Platform stopped successfully."