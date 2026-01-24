#!/bin/bash

# Health Check Test Script for Observer-Eye Platform
# Tests all health endpoints and validates responses
# Usage: ./health-check-test.sh [base-url]

set -e

# Configuration
BASE_URL="${1:-http://localhost:4200}"
TIMEOUT=10
VERBOSE=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED_TESTS++))
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAILED_TESTS++))
}

# Test function
test_endpoint() {
    local endpoint="$1"
    local expected_status="$2"
    local description="$3"
    local url="${BASE_URL}${endpoint}"
    
    ((TOTAL_TESTS++))
    
    log_info "Testing: $description"
    log_info "URL: $url"
    
    # Make HTTP request
    local response
    local status_code
    local response_time
    
    if response=$(curl -s -w "\n%{http_code}\n%{time_total}" --max-time "$TIMEOUT" "$url" 2>/dev/null); then
        # Parse response
        local body=$(echo "$response" | head -n -2)
        status_code=$(echo "$response" | tail -n 2 | head -n 1)
        response_time=$(echo "$response" | tail -n 1)
        
        # Check status code
        if [[ "$status_code" == "$expected_status" ]]; then
            log_success "$description - Status: $status_code, Time: ${response_time}s"
            
            # Additional validation based on endpoint
            case "$endpoint" in
                "/health")
                    if [[ "$body" == "healthy" ]]; then
                        log_success "  ✓ Response body is correct"
                    else
                        log_warning "  ⚠ Unexpected response body: $body"
                    fi
                    ;;
                "/health/ready"|"/health/live")
                    if echo "$body" | jq -e '.ready // .alive' >/dev/null 2>&1; then
                        local status_field=$(echo "$body" | jq -r '.ready // .alive')
                        log_success "  ✓ JSON response with status: $status_field"
                    else
                        log_warning "  ⚠ Invalid JSON response or missing status field"
                    fi
                    ;;
                "/metrics")
                    if echo "$body" | grep -q "dashboard_status"; then
                        log_success "  ✓ Prometheus metrics format detected"
                        local metric_count=$(echo "$body" | grep -c "^[a-zA-Z]" || true)
                        log_info "  📊 Found $metric_count metrics"
                    else
                        log_warning "  ⚠ Metrics format not recognized"
                    fi
                    ;;
                "/health/deep-system")
                    if echo "$body" | jq -e '.kernel // .payload // .hardware' >/dev/null 2>&1; then
                        log_success "  ✓ Deep system metrics detected"
                    else
                        log_warning "  ⚠ Deep system metrics not found"
                    fi
                    ;;
            esac
            
        else
            log_error "$description - Expected: $expected_status, Got: $status_code"
            if [[ "$VERBOSE" == "true" ]]; then
                log_info "Response body: $body"
            fi
        fi
        
    else
        log_error "$description - Request failed (timeout or connection error)"
    fi
    
    echo
}

# Test JSON endpoint
test_json_endpoint() {
    local endpoint="$1"
    local expected_status="$2"
    local description="$3"
    local required_fields="$4"
    local url="${BASE_URL}${endpoint}"
    
    ((TOTAL_TESTS++))
    
    log_info "Testing: $description"
    log_info "URL: $url"
    
    local response
    local status_code
    local response_time
    
    if response=$(curl -s -w "\n%{http_code}\n%{time_total}" --max-time "$TIMEOUT" -H "Accept: application/json" "$url" 2>/dev/null); then
        local body=$(echo "$response" | head -n -2)
        status_code=$(echo "$response" | tail -n 2 | head -n 1)
        response_time=$(echo "$response" | tail -n 1)
        
        if [[ "$status_code" == "$expected_status" ]]; then
            log_success "$description - Status: $status_code, Time: ${response_time}s"
            
            # Validate JSON structure
            if echo "$body" | jq . >/dev/null 2>&1; then
                log_success "  ✓ Valid JSON response"
                
                # Check required fields
                IFS=',' read -ra FIELDS <<< "$required_fields"
                for field in "${FIELDS[@]}"; do
                    if echo "$body" | jq -e ".$field" >/dev/null 2>&1; then
                        local value=$(echo "$body" | jq -r ".$field")
                        log_success "  ✓ Field '$field': $value"
                    else
                        log_warning "  ⚠ Missing required field: $field"
                    fi
                done
                
            else
                log_error "  ✗ Invalid JSON response"
                if [[ "$VERBOSE" == "true" ]]; then
                    log_info "Response body: $body"
                fi
            fi
            
        else
            log_error "$description - Expected: $expected_status, Got: $status_code"
        fi
        
    else
        log_error "$description - Request failed"
    fi
    
    echo
}

# Performance test
performance_test() {
    local endpoint="$1"
    local description="$2"
    local iterations=5
    local url="${BASE_URL}${endpoint}"
    
    log_info "Performance test: $description ($iterations iterations)"
    
    local total_time=0
    local successful_requests=0
    
    for ((i=1; i<=iterations; i++)); do
        local response_time
        if response_time=$(curl -s -w "%{time_total}" --max-time "$TIMEOUT" -o /dev/null "$url" 2>/dev/null); then
            total_time=$(echo "$total_time + $response_time" | bc -l)
            ((successful_requests++))
        fi
    done
    
    if [[ $successful_requests -gt 0 ]]; then
        local avg_time=$(echo "scale=3; $total_time / $successful_requests" | bc -l)
        log_success "  📈 Average response time: ${avg_time}s ($successful_requests/$iterations successful)"
        
        # Performance thresholds
        if (( $(echo "$avg_time < 0.1" | bc -l) )); then
            log_success "  ⚡ Excellent performance (< 100ms)"
        elif (( $(echo "$avg_time < 0.5" | bc -l) )); then
            log_success "  ✓ Good performance (< 500ms)"
        elif (( $(echo "$avg_time < 1.0" | bc -l) )); then
            log_warning "  ⚠ Acceptable performance (< 1s)"
        else
            log_error "  ✗ Poor performance (> 1s)"
        fi
    else
        log_error "  ✗ All requests failed"
    fi
    
    echo
}

# Main test execution
main() {
    echo "=============================================="
    echo "Observer-Eye Platform Health Check Test Suite"
    echo "=============================================="
    echo "Base URL: $BASE_URL"
    echo "Timeout: ${TIMEOUT}s"
    echo
    
    # Check if curl and jq are available
    if ! command -v curl &> /dev/null; then
        log_error "curl is required but not installed"
        exit 1
    fi
    
    if ! command -v jq &> /dev/null; then
        log_warning "jq is not installed - JSON validation will be limited"
    fi
    
    if ! command -v bc &> /dev/null; then
        log_warning "bc is not installed - performance calculations will be limited"
    fi
    
    # Test basic health endpoint
    test_endpoint "/health" "200" "Basic health check"
    
    # Test Kubernetes probes
    test_json_endpoint "/health/ready" "200" "Kubernetes readiness probe" "ready,timestamp"
    test_json_endpoint "/health/live" "200" "Kubernetes liveness probe" "alive,timestamp,uptime"
    
    # Test detailed health status
    test_json_endpoint "/health/status" "200" "Detailed health status" "status,timestamp,checks"
    
    # Test metrics endpoint
    test_endpoint "/metrics" "200" "Prometheus metrics endpoint"
    
    # Test deep system monitoring
    test_json_endpoint "/health/deep-system" "200" "Deep system monitoring" "status,timestamp"
    
    # Performance tests
    log_info "Running performance tests..."
    performance_test "/health" "Basic health endpoint performance"
    performance_test "/health/ready" "Readiness probe performance"
    performance_test "/health/live" "Liveness probe performance"
    
    # Test error scenarios
    log_info "Testing error scenarios..."
    test_endpoint "/health/nonexistent" "404" "Non-existent health endpoint (should return 404)"
    
    # Summary
    echo "=============================================="
    echo "Test Summary"
    echo "=============================================="
    echo "Total tests: $TOTAL_TESTS"
    echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
    echo -e "Failed: ${RED}$FAILED_TESTS${NC}"
    
    if [[ $FAILED_TESTS -eq 0 ]]; then
        echo -e "${GREEN}✅ All tests passed!${NC}"
        exit 0
    else
        echo -e "${RED}❌ Some tests failed!${NC}"
        exit 1
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -t|--timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS] [BASE_URL]"
            echo "Options:"
            echo "  -v, --verbose    Enable verbose output"
            echo "  -t, --timeout    Set request timeout (default: 10s)"
            echo "  -h, --help       Show this help message"
            echo
            echo "Examples:"
            echo "  $0                                    # Test localhost:4200"
            echo "  $0 http://dashboard.observer-eye.local # Test custom URL"
            echo "  $0 -v -t 30 http://localhost:8080    # Verbose with 30s timeout"
            exit 0
            ;;
        *)
            BASE_URL="$1"
            shift
            ;;
    esac
done

# Run main function
main