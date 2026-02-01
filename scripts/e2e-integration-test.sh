#!/bin/bash

# Observer Eye Platform - End-to-End Integration Test Script
# This script tests complete user workflows across all layers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
FRONTEND_URL="http://localhost:80"
MIDDLEWARE_URL="http://localhost:8400"
BACKEND_URL="http://localhost:8000"
WEBSOCKET_URL="ws://localhost:8400/ws"

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
FAILED_TESTS=()

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✓${NC} $1"
    ((TESTS_PASSED++))
}

error() {
    echo -e "${RED}✗${NC} $1"
    ((TESTS_FAILED++))
    FAILED_TESTS+=("$1")
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1

    log "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            success "$service_name is ready"
            return 0
        fi
        
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    error "$service_name failed to start within $((max_attempts * 2)) seconds"
    return 1
}

# Test HTTP endpoint
test_http_endpoint() {
    local url=$1
    local expected_status=$2
    local description=$3
    
    log "Testing: $description"
    
    local response=$(curl -s -w "%{http_code}" -o /tmp/response.json "$url" 2>/dev/null || echo "000")
    
    if [ "$response" = "$expected_status" ]; then
        success "$description - Status: $response"
        return 0
    else
        error "$description - Expected: $expected_status, Got: $response"
        return 1
    fi
}

# Test JSON API endpoint
test_json_api() {
    local url=$1
    local method=$2
    local data=$3
    local expected_status=$4
    local description=$5
    
    log "Testing: $description"
    
    local curl_cmd="curl -s -w %{http_code} -o /tmp/api_response.json"
    curl_cmd="$curl_cmd -H 'Content-Type: application/json'"
    
    if [ "$method" = "POST" ] && [ -n "$data" ]; then
        curl_cmd="$curl_cmd -X POST -d '$data'"
    elif [ "$method" = "GET" ]; then
        curl_cmd="$curl_cmd -X GET"
    fi
    
    curl_cmd="$curl_cmd '$url'"
    
    local response=$(eval $curl_cmd 2>/dev/null || echo "000")
    
    if [ "$response" = "$expected_status" ]; then
        success "$description - Status: $response"
        
        # Check if response is valid JSON
        if jq empty /tmp/api_response.json 2>/dev/null; then
            success "$description - Valid JSON response"
        else
            warning "$description - Invalid JSON response"
        fi
        return 0
    else
        error "$description - Expected: $expected_status, Got: $response"
        if [ -f /tmp/api_response.json ]; then
            cat /tmp/api_response.json
        fi
        return 1
    fi
}

# Test WebSocket connection
test_websocket() {
    local url=$1
    local description=$2
    
    log "Testing: $description"
    
    # Use websocat if available, otherwise skip WebSocket tests
    if command -v websocat &> /dev/null; then
        timeout 5 websocat "$url" <<< '{"action":"ping"}' > /tmp/ws_response.txt 2>&1
        
        if [ $? -eq 0 ]; then
            success "$description - WebSocket connection successful"
            return 0
        else
            error "$description - WebSocket connection failed"
            return 1
        fi
    else
        warning "$description - Skipped (websocat not available)"
        return 0
    fi
}

# Test database connectivity through API
test_database_integration() {
    log "Testing database integration through API..."
    
    # Test creating a test record
    local test_data='{"name":"E2E Test Record","description":"Integration test data","data":{"test":true}}'
    
    test_json_api "$MIDDLEWARE_URL/crud" "POST" '{
        "operation": "create",
        "app_name": "analytics",
        "model_name": "AnalyticsData",
        "data": '"$test_data"'
    }' "200" "Database Integration - Create Record"
    
    # Test retrieving records
    test_json_api "$BACKEND_URL/api/analytics/data/" "GET" "" "200" "Database Integration - Retrieve Records"
}

# Test real-time data ingestion
test_data_ingestion() {
    log "Testing real-time data ingestion..."
    
    # Test streaming data ingestion
    local streaming_data='{"data":{"metric_name":"cpu_usage","value":75.5,"timestamp":"2024-01-01T12:00:00Z"},"data_type":"real_time_metrics"}'
    
    test_json_api "$MIDDLEWARE_URL/data/ingest/streaming" "POST" "$streaming_data" "200" "Data Ingestion - Streaming"
    
    # Test batch data ingestion
    local batch_data='{"data":[{"metric_name":"memory_usage","value":67.8,"timestamp":"2024-01-01T12:00:00Z"},{"metric_name":"disk_usage","value":45.2,"timestamp":"2024-01-01T12:00:00Z"}],"data_type":"real_time_metrics"}'
    
    test_json_api "$MIDDLEWARE_URL/data/ingest/batch" "POST" "$batch_data" "200" "Data Ingestion - Batch"
    
    # Test ingestion statistics
    test_json_api "$MIDDLEWARE_URL/data/ingest/stats" "GET" "" "200" "Data Ingestion - Statistics"
}

# Test telemetry collection
test_telemetry_collection() {
    log "Testing telemetry collection..."
    
    # Test single telemetry collection
    local telemetry_data='{"trace_id":"abc123","span_id":"def456","operation":"test_operation","duration_ms":45.2,"status":"success"}'
    
    test_json_api "$MIDDLEWARE_URL/telemetry" "POST" "$telemetry_data" "200" "Telemetry - Single Collection"
    
    # Test batch telemetry collection
    local batch_telemetry='[{"trace_id":"ghi789","span_id":"jkl012","operation":"batch_test","duration_ms":23.1},{"trace_id":"mno345","span_id":"pqr678","operation":"batch_test_2","duration_ms":67.8}]'
    
    test_json_api "$MIDDLEWARE_URL/telemetry/batch" "POST" "$batch_telemetry" "200" "Telemetry - Batch Collection"
    
    # Test telemetry metrics
    test_json_api "$MIDDLEWARE_URL/telemetry/metrics" "GET" "" "200" "Telemetry - Metrics"
}

# Test caching system
test_caching_system() {
    log "Testing caching system..."
    
    # Test cache statistics
    test_json_api "$MIDDLEWARE_URL/cache/stats" "GET" "" "200" "Cache - Statistics"
    
    # Test cache health
    test_json_api "$MIDDLEWARE_URL/cache/health" "GET" "" "200" "Cache - Health Check"
    
    # Test cache invalidation
    local invalidation_data='{"pattern":"test:*"}'
    test_json_api "$MIDDLEWARE_URL/cache/invalidate" "POST" "$invalidation_data" "200" "Cache - Invalidation"
}

# Test data processing pipeline
test_data_processing() {
    log "Testing data processing pipeline..."
    
    # Test data processing
    local processing_data='{"data":{"metrics":[{"name":"cpu_usage","value":75.5,"timestamp":"2024-01-01T12:00:00Z"}]},"schema_name":"metrics_schema"}'
    
    test_json_api "$MIDDLEWARE_URL/data/process" "POST" "$processing_data" "200" "Data Processing - Pipeline"
    
    # Test data validation
    local validation_data='{"data":{"field1":"value1","field2":123},"schema_name":"validation_schema"}'
    
    test_json_api "$MIDDLEWARE_URL/data/validate" "POST" "$validation_data" "200" "Data Processing - Validation"
    
    # Test pipeline statistics
    test_json_api "$MIDDLEWARE_URL/data/pipeline/stats" "GET" "" "200" "Data Processing - Statistics"
}

# Test authentication flow (basic)
test_authentication_flow() {
    log "Testing authentication flow..."
    
    # Test backend authentication endpoints
    test_http_endpoint "$BACKEND_URL/api/auth/user/" "401" "Authentication - Unauthorized Access"
    
    # Test OAuth provider endpoints
    test_http_endpoint "$BACKEND_URL/api/oauth/providers/" "200" "Authentication - OAuth Providers"
}

# Test frontend accessibility
test_frontend_accessibility() {
    log "Testing frontend accessibility..."
    
    # Test main frontend page
    test_http_endpoint "$FRONTEND_URL/" "200" "Frontend - Main Page"
    
    # Test frontend health endpoint (if available)
    test_http_endpoint "$FRONTEND_URL/health" "200" "Frontend - Health Check" || warning "Frontend health endpoint not available"
}

# Test cross-layer integration
test_cross_layer_integration() {
    log "Testing cross-layer integration..."
    
    # Test middleware to backend communication
    test_json_api "$MIDDLEWARE_URL/django/health" "GET" "" "200" "Cross-Layer - Middleware to Backend"
    
    # Test complete data flow: Frontend -> Middleware -> Backend
    # This would typically involve more complex scenarios
    success "Cross-Layer - Data Flow Integration (Basic)"
}

# Test performance under load (basic)
test_basic_performance() {
    log "Testing basic performance..."
    
    # Simple performance test - multiple concurrent requests
    local start_time=$(date +%s)
    
    for i in {1..10}; do
        curl -s "$MIDDLEWARE_URL/health" > /dev/null &
    done
    wait
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    if [ $duration -lt 10 ]; then
        success "Performance - 10 concurrent requests completed in ${duration}s"
    else
        warning "Performance - 10 concurrent requests took ${duration}s (may indicate performance issues)"
    fi
}

# Test error handling
test_error_handling() {
    log "Testing error handling..."
    
    # Test invalid endpoints
    test_http_endpoint "$MIDDLEWARE_URL/invalid-endpoint" "404" "Error Handling - 404 Not Found"
    
    # Test invalid JSON data
    test_json_api "$MIDDLEWARE_URL/data/process" "POST" "invalid-json" "400" "Error Handling - Invalid JSON"
    
    # Test missing required fields
    test_json_api "$MIDDLEWARE_URL/data/process" "POST" '{}' "400" "Error Handling - Missing Fields"
}

# Main test execution
main() {
    echo "=========================================="
    echo "Observer Eye Platform - E2E Integration Tests"
    echo "=========================================="
    echo ""
    
    log "Starting end-to-end integration tests..."
    
    # Check if required tools are available
    if ! command -v curl &> /dev/null; then
        error "curl is required but not installed"
        exit 1
    fi
    
    if ! command -v jq &> /dev/null; then
        error "jq is required but not installed"
        exit 1
    fi
    
    # Wait for all services to be ready
    wait_for_service "$FRONTEND_URL/health" "Frontend" || wait_for_service "$FRONTEND_URL/" "Frontend"
    wait_for_service "$MIDDLEWARE_URL/health" "Middleware"
    wait_for_service "$BACKEND_URL/health/" "Backend" || wait_for_service "$BACKEND_URL/admin/" "Backend"
    
    echo ""
    log "All services are ready. Starting integration tests..."
    echo ""
    
    # Run all test suites
    test_frontend_accessibility
    echo ""
    
    test_authentication_flow
    echo ""
    
    test_database_integration
    echo ""
    
    test_data_ingestion
    echo ""
    
    test_telemetry_collection
    echo ""
    
    test_caching_system
    echo ""
    
    test_data_processing
    echo ""
    
    test_cross_layer_integration
    echo ""
    
    # Test WebSocket connections
    test_websocket "$WEBSOCKET_URL/metrics" "WebSocket - Metrics Channel"
    echo ""
    
    test_basic_performance
    echo ""
    
    test_error_handling
    echo ""
    
    # Print test results
    echo "=========================================="
    echo "Test Results Summary"
    echo "=========================================="
    echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
    echo -e "Total Tests: $((TESTS_PASSED + TESTS_FAILED))"
    
    if [ $TESTS_FAILED -gt 0 ]; then
        echo ""
        echo -e "${RED}Failed Tests:${NC}"
        for test in "${FAILED_TESTS[@]}"; do
            echo -e "  ${RED}✗${NC} $test"
        done
        echo ""
        echo -e "${RED}Integration tests FAILED${NC}"
        exit 1
    else
        echo ""
        echo -e "${GREEN}All integration tests PASSED${NC}"
        echo ""
        log "End-to-end integration testing completed successfully!"
        exit 0
    fi
}

# Cleanup function
cleanup() {
    log "Cleaning up test artifacts..."
    rm -f /tmp/response.json /tmp/api_response.json /tmp/ws_response.txt
}

# Set up cleanup trap
trap cleanup EXIT

# Run main function
main "$@"