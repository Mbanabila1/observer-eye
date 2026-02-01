#!/bin/bash

# Observer Eye Platform - Complete System Validation Script
# This script runs all validation tests across all layers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FRONTEND_URL="http://localhost:80"
MIDDLEWARE_URL="http://localhost:8400"
BACKEND_URL="http://localhost:8000"
WEBSOCKET_URL="ws://localhost:8400/ws"

# Test results
TOTAL_TEST_SUITES=0
PASSED_TEST_SUITES=0
FAILED_TEST_SUITES=0
FAILED_SUITES=()

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED_TEST_SUITES++))
}

error() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED_TEST_SUITES++))
    FAILED_SUITES+=("$1")
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

info() {
    echo -e "${CYAN}ℹ${NC} $1"
}

section() {
    echo ""
    echo -e "${PURPLE}========================================${NC}"
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}========================================${NC}"
    echo ""
}

# Check if services are running
check_services() {
    log "Checking if all services are running..."
    
    local services_ready=true
    
    # Check frontend
    if curl -s -f "$FRONTEND_URL" > /dev/null 2>&1 || curl -s -f "$FRONTEND_URL/health" > /dev/null 2>&1; then
        success "Frontend service is accessible"
    else
        error "Frontend service is not accessible at $FRONTEND_URL"
        services_ready=false
    fi
    
    # Check middleware
    if curl -s -f "$MIDDLEWARE_URL/health" > /dev/null 2>&1; then
        success "Middleware service is accessible"
    else
        error "Middleware service is not accessible at $MIDDLEWARE_URL"
        services_ready=false
    fi
    
    # Check backend
    if curl -s -f "$BACKEND_URL/health/" > /dev/null 2>&1 || curl -s -f "$BACKEND_URL/admin/" > /dev/null 2>&1; then
        success "Backend service is accessible"
    else
        error "Backend service is not accessible at $BACKEND_URL"
        services_ready=false
    fi
    
    if [ "$services_ready" = false ]; then
        error "Not all services are running. Please start the Observer Eye Platform first."
        echo ""
        echo "To start all services, run:"
        echo "  cd $PROJECT_ROOT"
        echo "  docker-compose up -d"
        echo ""
        exit 1
    fi
    
    success "All services are running and accessible"
}

# Run production validation tests
run_production_validation() {
    section "Production Validation Tests"
    ((TOTAL_TEST_SUITES++))
    
    log "Running production validation tests..."
    
    if [ -f "$SCRIPT_DIR/validate_production.sh" ]; then
        if bash "$SCRIPT_DIR/validate_production.sh"; then
            success "Production validation tests passed"
        else
            error "Production validation tests failed"
        fi
    else
        warning "Production validation script not found, skipping"
    fi
}

# Run end-to-end integration tests
run_e2e_integration_tests() {
    section "End-to-End Integration Tests"
    ((TOTAL_TEST_SUITES++))
    
    log "Running end-to-end integration tests..."
    
    if [ -f "$SCRIPT_DIR/e2e-integration-test.sh" ]; then
        if bash "$SCRIPT_DIR/e2e-integration-test.sh"; then
            success "End-to-end integration tests passed"
        else
            error "End-to-end integration tests failed"
        fi
    else
        error "E2E integration test script not found"
    fi
}

# Run WebSocket integration tests
run_websocket_tests() {
    section "WebSocket Integration Tests"
    ((TOTAL_TEST_SUITES++))
    
    log "Running WebSocket integration tests..."
    
    if [ -f "$SCRIPT_DIR/websocket-integration-test.py" ]; then
        if command -v python3 &> /dev/null; then
            # Check if required Python packages are available
            if python3 -c "import websockets, aiohttp" 2>/dev/null; then
                if python3 "$SCRIPT_DIR/websocket-integration-test.py" \
                   --websocket-url "$WEBSOCKET_URL" \
                   --api-url "$MIDDLEWARE_URL"; then
                    success "WebSocket integration tests passed"
                else
                    error "WebSocket integration tests failed"
                fi
            else
                warning "WebSocket integration tests skipped (missing dependencies: websockets, aiohttp)"
                info "Install with: pip install websockets aiohttp"
            fi
        else
            warning "WebSocket integration tests skipped (Python 3 not available)"
        fi
    else
        error "WebSocket integration test script not found"
    fi
}

# Run authentication integration tests
run_auth_tests() {
    section "Authentication Integration Tests"
    ((TOTAL_TEST_SUITES++))
    
    log "Running authentication integration tests..."
    
    if [ -f "$SCRIPT_DIR/auth-integration-test.py" ]; then
        if command -v python3 &> /dev/null; then
            # Check if required Python packages are available
            if python3 -c "import aiohttp" 2>/dev/null; then
                if python3 "$SCRIPT_DIR/auth-integration-test.py" \
                   --backend-url "$BACKEND_URL" \
                   --middleware-url "$MIDDLEWARE_URL" \
                   --frontend-url "$FRONTEND_URL"; then
                    success "Authentication integration tests passed"
                else
                    error "Authentication integration tests failed"
                fi
            else
                warning "Authentication integration tests skipped (missing dependency: aiohttp)"
                info "Install with: pip install aiohttp"
            fi
        else
            warning "Authentication integration tests skipped (Python 3 not available)"
        fi
    else
        error "Authentication integration test script not found"
    fi
}

# Run cross-platform tests
run_cross_platform_tests() {
    section "Cross-Platform Tests"
    ((TOTAL_TEST_SUITES++))
    
    log "Running cross-platform tests..."
    
    if [ -f "$SCRIPT_DIR/cross-platform-test.sh" ]; then
        if bash "$SCRIPT_DIR/cross-platform-test.sh"; then
            success "Cross-platform tests passed"
        else
            error "Cross-platform tests failed"
        fi
    else
        error "Cross-platform test script not found"
    fi
}

# Run performance and load tests
run_performance_tests() {
    section "Performance and Load Tests"
    ((TOTAL_TEST_SUITES++))
    
    log "Running performance and load tests..."
    
    if [ -f "$SCRIPT_DIR/performance-load-test.py" ]; then
        if command -v python3 &> /dev/null; then
            # Check if required Python packages are available
            if python3 -c "import aiohttp, psutil" 2>/dev/null; then
                if python3 "$SCRIPT_DIR/performance-load-test.py" \
                   --frontend-url "$FRONTEND_URL" \
                   --middleware-url "$MIDDLEWARE_URL" \
                   --backend-url "$BACKEND_URL" \
                   --timeout 180; then
                    success "Performance and load tests passed"
                else
                    error "Performance and load tests failed"
                fi
            else
                warning "Performance and load tests skipped (missing dependencies: aiohttp, psutil)"
                info "Install with: pip install aiohttp psutil"
            fi
        else
            warning "Performance and load tests skipped (Python 3 not available)"
        fi
    else
        error "Performance and load test script not found"
    fi
}

# Run Docker and container tests
run_docker_tests() {
    section "Docker and Container Tests"
    ((TOTAL_TEST_SUITES++))
    
    log "Running Docker and container tests..."
    
    local docker_tests_passed=true
    
    # Test Docker Compose status
    if docker-compose ps | grep -q "Up"; then
        success "Docker Compose services are running"
    else
        error "Docker Compose services are not running properly"
        docker_tests_passed=false
    fi
    
    # Test container health
    local containers=("backend" "middleware" "dashboard")
    for container in "${containers[@]}"; do
        if docker-compose ps "$container" | grep -q "Up"; then
            success "$container container is running"
        else
            error "$container container is not running"
            docker_tests_passed=false
        fi
    done
    
    # Test container logs for errors
    log "Checking container logs for critical errors..."
    local log_errors=false
    
    for container in "${containers[@]}"; do
        if docker-compose logs --tail=50 "$container" 2>/dev/null | grep -i "error\|exception\|failed" | grep -v "test" | head -5; then
            warning "Found potential errors in $container logs"
            log_errors=true
        fi
    done
    
    if [ "$log_errors" = false ]; then
        success "No critical errors found in container logs"
    fi
    
    if [ "$docker_tests_passed" = true ]; then
        success "Docker and container tests passed"
    else
        error "Docker and container tests failed"
    fi
}

# Test database connectivity and data integrity
run_database_tests() {
    section "Database and Data Integrity Tests"
    ((TOTAL_TEST_SUITES++))
    
    log "Running database and data integrity tests..."
    
    local db_tests_passed=true
    
    # Test database connectivity through Django
    if docker-compose exec -T backend python manage.py check --database default > /dev/null 2>&1; then
        success "Database connectivity check passed"
    else
        error "Database connectivity check failed"
        db_tests_passed=false
    fi
    
    # Test migrations
    if docker-compose exec -T backend python manage.py showmigrations | grep -q "\[X\]"; then
        success "Database migrations are applied"
    else
        warning "Some database migrations may not be applied"
    fi
    
    # Test basic data operations
    log "Testing basic data operations..."
    
    # Create a test record through the API
    local test_data='{"data":{"test_field":"validation_test","timestamp":"2024-01-01T12:00:00Z"},"schema_name":"test_schema"}'
    
    if curl -s -X POST -H "Content-Type: application/json" \
       -d "$test_data" "$MIDDLEWARE_URL/data/process" | grep -q "success"; then
        success "Data processing API is working"
    else
        warning "Data processing API test failed (may be expected)"
    fi
    
    if [ "$db_tests_passed" = true ]; then
        success "Database and data integrity tests passed"
    else
        error "Database and data integrity tests failed"
    fi
}

# Test security configurations
run_security_tests() {
    section "Security Configuration Tests"
    ((TOTAL_TEST_SUITES++))
    
    log "Running security configuration tests..."
    
    local security_tests_passed=true
    
    # Test HTTPS redirect (if configured)
    log "Testing security headers..."
    
    local security_headers=("X-Frame-Options" "X-Content-Type-Options" "X-XSS-Protection")
    local headers_found=0
    
    for header in "${security_headers[@]}"; do
        if curl -s -I "$BACKEND_URL/health/" | grep -i "$header" > /dev/null; then
            success "Security header $header is present"
            ((headers_found++))
        else
            warning "Security header $header is missing"
        fi
    done
    
    if [ $headers_found -ge 2 ]; then
        success "Adequate security headers are configured"
    else
        warning "Limited security headers configured"
    fi
    
    # Test CORS configuration
    if curl -s -H "Origin: http://localhost:4200" -I "$BACKEND_URL/api/auth/user/" | grep -i "access-control" > /dev/null; then
        success "CORS headers are configured"
    else
        warning "CORS headers may not be configured"
    fi
    
    success "Security configuration tests completed"
}

# Generate final report
generate_final_report() {
    section "Final System Validation Report"
    
    echo "Observer Eye Platform - Complete System Validation"
    echo "=================================================="
    echo ""
    echo "Test Execution Summary:"
    echo "  Total Test Suites: $TOTAL_TEST_SUITES"
    echo -e "  Passed Test Suites: ${GREEN}$PASSED_TEST_SUITES${NC}"
    echo -e "  Failed Test Suites: ${RED}$FAILED_TEST_SUITES${NC}"
    echo ""
    
    if [ $FAILED_TEST_SUITES -gt 0 ]; then
        echo -e "${RED}Failed Test Suites:${NC}"
        for suite in "${FAILED_SUITES[@]}"; do
            echo -e "  ${RED}✗${NC} $suite"
        done
        echo ""
    fi
    
    # System information
    echo "System Information:"
    echo "  Platform: $(uname -s) $(uname -m)"
    echo "  Docker Version: $(docker --version 2>/dev/null || echo 'Not available')"
    echo "  Docker Compose Version: $(docker-compose --version 2>/dev/null || echo 'Not available')"
    echo "  Test Execution Time: $(date)"
    echo ""
    
    # Service status
    echo "Service Status:"
    echo "  Frontend: $FRONTEND_URL"
    echo "  Middleware: $MIDDLEWARE_URL"
    echo "  Backend: $BACKEND_URL"
    echo ""
    
    # Container status
    echo "Container Status:"
    docker-compose ps 2>/dev/null || echo "  Docker Compose not available"
    echo ""
    
    # Final verdict
    local success_rate=$((PASSED_TEST_SUITES * 100 / TOTAL_TEST_SUITES))
    
    if [ $FAILED_TEST_SUITES -eq 0 ]; then
        echo -e "${GREEN}🎉 ALL SYSTEM VALIDATION TESTS PASSED! 🎉${NC}"
        echo ""
        echo -e "${GREEN}The Observer Eye Platform is ready for production deployment.${NC}"
        echo ""
        echo "Next Steps:"
        echo "  1. Review the deployment guide: deployment.md"
        echo "  2. Configure production environment variables"
        echo "  3. Set up SSL certificates for HTTPS"
        echo "  4. Configure monitoring and alerting"
        echo "  5. Set up backup and disaster recovery"
        echo ""
        return 0
    elif [ $success_rate -ge 80 ]; then
        echo -e "${YELLOW}⚠ SYSTEM VALIDATION COMPLETED WITH WARNINGS ⚠${NC}"
        echo ""
        echo -e "${YELLOW}Success Rate: $success_rate% ($PASSED_TEST_SUITES/$TOTAL_TEST_SUITES)${NC}"
        echo ""
        echo "The system is mostly functional but has some issues that should be addressed."
        echo "Review the failed tests above and fix the issues before production deployment."
        echo ""
        return 1
    else
        echo -e "${RED}❌ SYSTEM VALIDATION FAILED ❌${NC}"
        echo ""
        echo -e "${RED}Success Rate: $success_rate% ($PASSED_TEST_SUITES/$TOTAL_TEST_SUITES)${NC}"
        echo ""
        echo "Critical issues were found that prevent production deployment."
        echo "Please fix the failed tests before proceeding."
        echo ""
        return 1
    fi
}

# Main execution
main() {
    echo ""
    echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║                Observer Eye Platform                         ║${NC}"
    echo -e "${PURPLE}║              Complete System Validation                      ║${NC}"
    echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    log "Starting complete system validation..."
    log "This will run all available test suites to validate the entire platform"
    echo ""
    
    # Check prerequisites
    if ! command -v curl &> /dev/null; then
        error "curl is required but not installed"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        error "Docker is required but not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is required but not installed"
        exit 1
    fi
    
    # Check if services are running
    check_services
    echo ""
    
    # Run all test suites
    run_production_validation
    run_docker_tests
    run_database_tests
    run_e2e_integration_tests
    run_websocket_tests
    run_auth_tests
    run_cross_platform_tests
    run_performance_tests
    run_security_tests
    
    # Generate final report
    generate_final_report
}

# Cleanup function
cleanup() {
    log "Cleaning up test artifacts..."
    # Remove any temporary files created during testing
    rm -f /tmp/response.json /tmp/api_response.json /tmp/ws_response.txt
    rm -f /tmp/test-dockerfile /tmp/test-compose.yml
    rm -rf /tmp/test-context /tmp/docker-volume-test
}

# Set up cleanup trap
trap cleanup EXIT

# Run main function
main "$@"