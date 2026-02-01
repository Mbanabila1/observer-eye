#!/bin/bash

# Observer Eye Platform Development Setup Script
# This script sets up and validates the development environment for all three layers

set -e

echo "🚀 Observer Eye Platform Development Setup"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check if we're in the right directory
if [ ! -d "dashboard" ] || [ ! -d "middleware" ] || [ ! -d "backend" ]; then
    print_error "Please run this script from the observer-eye directory"
    exit 1
fi

print_info "Validating development environment..."

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
if [[ $(echo "$python_version" | cut -d'.' -f1) -ge 3 ]] && [[ $(echo "$python_version" | cut -d'.' -f2) -ge 10 ]]; then
    print_status "Python $python_version (✓ >= 3.10)"
else
    print_error "Python 3.10+ required, found $python_version"
    exit 1
fi

# Check Node.js version
node_version=$(node --version 2>&1 | cut -d'v' -f2)
if [[ $(echo "$node_version" | cut -d'.' -f1) -ge 18 ]]; then
    print_status "Node.js $node_version (✓ >= 18)"
else
    print_error "Node.js 18+ required, found $node_version"
    exit 1
fi

echo ""
print_info "Setting up Backend (Django)..."

# Backend setup
cd backend
if [ ! -d "venv1" ]; then
    print_info "Creating Python virtual environment for backend..."
    python3 -m venv venv1
fi

source venv1/bin/activate
pip install -q -r requirements.txt
print_status "Backend dependencies installed"

# Run Django migrations
cd observer
python manage.py migrate --verbosity=0
print_status "Django migrations applied"

# Test Django setup
cd ..
python test_setup.py > /dev/null 2>&1
if [ $? -eq 0 ]; then
    print_status "Django backend validation passed"
else
    print_error "Django backend validation failed"
    exit 1
fi

cd ..

echo ""
print_info "Setting up Middleware (FastAPI)..."

# Middleware setup
cd middleware
if [ ! -d "venv0" ]; then
    print_info "Creating Python virtual environment for middleware..."
    python3 -m venv venv0
fi

source venv0/bin/activate
pip install -q -r requirements.txt
print_status "Middleware dependencies installed"

# Test FastAPI setup
python test_setup.py > /dev/null 2>&1
if [ $? -eq 0 ]; then
    print_status "FastAPI middleware validation passed"
else
    print_error "FastAPI middleware validation failed"
    exit 1
fi

cd ..

echo ""
print_info "Setting up Frontend (Angular 21)..."

# Frontend setup
cd dashboard
npm install --silent
print_status "Angular dependencies installed"

# Test Angular build
npm run build > /dev/null 2>&1
if [ $? -eq 0 ]; then
    print_status "Angular build validation passed"
else
    print_error "Angular build validation failed"
    exit 1
fi

cd ..

echo ""
print_status "Development environment setup complete!"
echo ""
print_info "Quick start commands:"
echo "  Backend:    cd backend && source venv1/bin/activate && cd observer && python manage.py runserver"
echo "  Middleware: cd middleware && source venv0/bin/activate && python main.py"
echo "  Frontend:   cd dashboard && npm start"
echo ""
print_info "Development URLs:"
echo "  Frontend:   http://localhost:4200 (Angular dev server)"
echo "  Middleware: http://localhost:8400 (FastAPI)"
echo "  Backend:    http://localhost:8000 (Django)"
echo ""
print_warning "Note: Start services in separate terminal windows/tabs"