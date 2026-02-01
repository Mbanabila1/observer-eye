#!/bin/bash

# Master Production Validation Script for Observer Eye Platform
# This script runs validation checks across all three layers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_header() {
    echo -e "${BLUE}$1${NC}"
}

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Initialize counters
TOTAL_ERRORS=0
TOTAL_WARNINGS=0
VALIDATION_RESULTS=()

# Function to run validation and capture results
run_validation() {
    local component=$1
    local script_path=$2
    local description=$3
    
    print_header "🔍 Validating $description..."
    
    if [ ! -f "$script_path" ]; then
        print_error "Validation script not found: $script_path"
        TOTAL_ERRORS=$((TOTAL_ERRORS + 1))
        VALIDATION_RESULTS+=("$component: SCRIPT_NOT_FOUND")
        return 1
    fi
    
    # Make script executable
    chmod +x "$script_path"
    
    # Run validation and capture output
    if output=$($script_path 2>&1); then
        print_status "✅ $description validation passed"
        VALIDATION_RESULTS+=("$component: PASS")
    else
        exit_code=$?
        print_error "❌ $description validation failed (exit code: $exit_code)"
        VALIDATION_RESULTS+=("$component: FAIL")
        TOTAL_ERRORS=$((TOTAL_ERRORS + 1))
        
        # Print the output for debugging
        echo "$output"
    fi
}

# Main validation function
main() {
    print_header "🚀 Observer Eye Platform - Production Validation Suite"
    print_header "============================================================"
    
    # Get the script directory
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
    
    print_status "Project root: $PROJECT_ROOT"
    print_status "Starting comprehensive production validation..."
    echo
    
    # Validate Django Backend
    run_validation "BACKEND" "$PROJECT_ROOT/backend/scripts/validate_production.py" "Django Backend"
    echo
    
    # Validate FastAPI Middleware
    run_validation "MIDDLEWARE" "$PROJECT_ROOT/middleware/scripts/validate_production.py" "FastAPI Middleware"
    echo
    
    # Validate Angular Frontend
    run_validation "FRONTEND" "$PROJECT_ROOT/dashboard/scripts/validate_production.js" "Angular Frontend"
    echo
    
    # Additional system-level validations
    print_header "🔧 System-level validations..."
    
    # Check Docker files
    print_status "Checking Docker configurations..."
    
    docker_files=(
        "$PROJECT_ROOT/backend/Dockerfile"
        "$PROJECT_ROOT/middleware/Dockerfile"
        "$PROJECT_ROOT/dashboard/Dockerfile"
        "$PROJECT_ROOT/docker-compose.yml"
    )
    
    for docker_file in "${docker_files[@]}"; do
        if [ ! -f "$docker_file" ]; then
            print_error "Docker file missing: $docker_file"
            TOTAL_ERRORS=$((TOTAL_ERRORS + 1))
        else
            print_status "✅ Found: $(basename "$docker_file")"
        fi
    done
    
    # Check environment configuration
    print_status "Checking environment configuration..."
    
    if [ ! -f "$PROJECT_ROOT/.env.example" ]; then
        print_warning "Environment template (.env.example) not found"
        TOTAL_WARNINGS=$((TOTAL_WARNINGS + 1))
    else
        print_status "✅ Environment template found"
    fi
    
    if [ -f "$PROJECT_ROOT/.env" ]; then
        # Check for default/insecure values in .env
        if grep -q "your_secure_.*_password_here" "$PROJECT_ROOT/.env" 2>/dev/null; then
            print_warning "Default password values found in .env file"
            TOTAL_WARNINGS=$((TOTAL_WARNINGS + 1))
        fi
        
        if grep -q "your_very_long_and_secure_django_secret_key_here" "$PROJECT_ROOT/.env" 2>/dev/null; then
            print_error "Default Django secret key found in .env file"
            TOTAL_ERRORS=$((TOTAL_ERRORS + 1))
        fi
    fi
    
    # Check for sensitive files that shouldn't be in production
    print_status "Checking for sensitive files..."
    
    sensitive_patterns=(
        "*.key"
        "*.pem"
        "*.p12"
        "*.pfx"
        ".env"
        "secrets.json"
        "credentials.json"
    )
    
    for pattern in "${sensitive_patterns[@]}"; do
        if find "$PROJECT_ROOT" -name "$pattern" -not -path "*/node_modules/*" -not -path "*/.git/*" | grep -q .; then
            print_warning "Found potentially sensitive files matching pattern: $pattern"
            TOTAL_WARNINGS=$((TOTAL_WARNINGS + 1))
        fi
    done
    
    echo
    print_header "📊 VALIDATION SUMMARY"
    print_header "====================="
    
    # Print component results
    for result in "${VALIDATION_RESULTS[@]}"; do
        component=$(echo "$result" | cut -d: -f1)
        status=$(echo "$result" | cut -d: -f2)
        
        case $status in
            "PASS")
                print_status "✅ $component: PASSED"
                ;;
            "FAIL")
                print_error "❌ $component: FAILED"
                ;;
            "SCRIPT_NOT_FOUND")
                print_error "❌ $component: VALIDATION SCRIPT NOT FOUND"
                ;;
        esac
    done
    
    echo
    print_status "Total errors: $TOTAL_ERRORS"
    print_status "Total warnings: $TOTAL_WARNINGS"
    
    # Overall status
    if [ $TOTAL_ERRORS -eq 0 ]; then
        print_header "🎉 OVERALL STATUS: PASS"
        if [ $TOTAL_WARNINGS -gt 0 ]; then
            print_warning "Note: There are $TOTAL_WARNINGS warnings that should be addressed"
        fi
        echo
        print_status "✅ Observer Eye Platform is ready for production deployment!"
    else
        print_header "❌ OVERALL STATUS: FAIL"
        print_error "Found $TOTAL_ERRORS critical issues that must be fixed before production deployment"
        echo
        exit 1
    fi
    
    # Save summary results
    results_file="$PROJECT_ROOT/validation_summary.json"
    cat > "$results_file" << EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "overall_status": "$([ $TOTAL_ERRORS -eq 0 ] && echo "PASS" || echo "FAIL")",
  "total_errors": $TOTAL_ERRORS,
  "total_warnings": $TOTAL_WARNINGS,
  "component_results": {
$(IFS=$'\n'; for result in "${VALIDATION_RESULTS[@]}"; do
    component=$(echo "$result" | cut -d: -f1 | tr '[:upper:]' '[:lower:]')
    status=$(echo "$result" | cut -d: -f2 | xargs)
    echo "    \"$component\": \"$status\","
done | sed '$ s/,$//')
  }
}
EOF
    
    print_status "📄 Summary results saved to: $results_file"
}

# Check dependencies
check_dependencies() {
    # Check if Python is available for backend validation
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required for backend validation"
        exit 1
    fi
    
    # Check if Node.js is available for frontend validation
    if ! command -v node &> /dev/null; then
        print_error "Node.js is required for frontend validation"
        exit 1
    fi
}

# Run dependency check and main validation
check_dependencies
main "$@"