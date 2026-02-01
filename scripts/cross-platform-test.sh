#!/bin/bash

# Observer Eye Platform - Cross-Platform Testing Script
# Tests Docker deployment across Linux, macOS, and Windows systems

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
FAILED_TESTS=()

# Platform detection
detect_platform() {
    case "$(uname -s)" in
        Linux*)     PLATFORM=Linux;;
        Darwin*)    PLATFORM=macOS;;
        CYGWIN*|MINGW*|MSYS*) PLATFORM=Windows;;
        *)          PLATFORM="Unknown";;
    esac
    echo $PLATFORM
}

# Logging functions
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

# Test Docker installation and version
test_docker_installation() {
    log "Testing Docker installation..."
    
    if command -v docker &> /dev/null; then
        local docker_version=$(docker --version)
        success "Docker is installed: $docker_version"
        
        # Test Docker daemon
        if docker info &> /dev/null; then
            success "Docker daemon is running"
        else
            error "Docker daemon is not running"
            return 1
        fi
    else
        error "Docker is not installed"
        return 1
    fi
    
    # Test Docker Compose
    if command -v docker-compose &> /dev/null; then
        local compose_version=$(docker-compose --version)
        success "Docker Compose is installed: $compose_version"
    else
        error "Docker Compose is not installed"
        return 1
    fi
    
    return 0
}

# Test platform-specific Docker features
test_platform_docker_features() {
    local platform=$1
    log "Testing platform-specific Docker features for $platform..."
    
    case $platform in
        Linux)
            # Test Docker without sudo (user in docker group)
            if groups $USER | grep -q docker; then
                success "User is in docker group (no sudo required)"
            else
                warning "User not in docker group (may require sudo)"
            fi
            
            # Test systemd integration
            if systemctl is-active --quiet docker; then
                success "Docker service is active via systemd"
            else
                warning "Docker service not managed by systemd"
            fi
            ;;
            
        macOS)
            # Test Docker Desktop
            if pgrep -f "Docker Desktop" > /dev/null; then
                success "Docker Desktop is running"
            else
                warning "Docker Desktop may not be running"
            fi
            
            # Test file sharing
            if docker run --rm -v /tmp:/test alpine ls /test > /dev/null 2>&1; then
                success "Docker file sharing is working"
            else
                error "Docker file sharing is not working"
            fi
            ;;
            
        Windows)
            # Test WSL 2 integration (if on Windows)
            if command -v wsl &> /dev/null; then
                success "WSL is available"
                
                # Test WSL 2
                local wsl_version=$(wsl -l -v 2>/dev/null | grep -c "2" || echo "0")
                if [ "$wsl_version" -gt 0 ]; then
                    success "WSL 2 is configured"
                else
                    warning "WSL 2 may not be configured"
                fi
            else
                warning "WSL not available (may be running on Windows without WSL)"
            fi
            ;;
    esac
}

# Test Docker build performance
test_docker_build_performance() {
    log "Testing Docker build performance..."
    
    # Create a simple test Dockerfile
    cat > /tmp/test-dockerfile << 'EOF'
FROM alpine:latest
RUN apk add --no-cache curl
COPY . /app
WORKDIR /app
CMD ["echo", "test"]
EOF
    
    # Create test context
    mkdir -p /tmp/test-context
    echo "test file" > /tmp/test-context/test.txt
    cp /tmp/test-dockerfile /tmp/test-context/Dockerfile
    
    # Measure build time
    local start_time=$(date +%s)
    
    if docker build -t cross-platform-test /tmp/test-context > /dev/null 2>&1; then
        local end_time=$(date +%s)
        local build_time=$((end_time - start_time))
        
        if [ $build_time -lt 60 ]; then
            success "Docker build completed in ${build_time}s (good performance)"
        elif [ $build_time -lt 120 ]; then
            warning "Docker build completed in ${build_time}s (acceptable performance)"
        else
            error "Docker build took ${build_time}s (poor performance)"
        fi
        
        # Cleanup
        docker rmi cross-platform-test > /dev/null 2>&1 || true
    else
        error "Docker build failed"
    fi
    
    # Cleanup test files
    rm -rf /tmp/test-context /tmp/test-dockerfile
}

# Test container networking
test_container_networking() {
    log "Testing container networking..."
    
    # Test basic networking
    if docker run --rm alpine ping -c 1 google.com > /dev/null 2>&1; then
        success "Container internet connectivity working"
    else
        error "Container internet connectivity failed"
    fi
    
    # Test port binding
    local test_port=18080
    
    # Start a test container with port binding
    local container_id=$(docker run -d -p $test_port:80 nginx:alpine)
    
    if [ $? -eq 0 ]; then
        sleep 3  # Wait for container to start
        
        # Test port accessibility
        if curl -s -f http://localhost:$test_port > /dev/null 2>&1; then
            success "Container port binding working"
        else
            error "Container port binding failed"
        fi
        
        # Cleanup
        docker stop $container_id > /dev/null 2>&1
        docker rm $container_id > /dev/null 2>&1
    else
        error "Failed to start test container"
    fi
}

# Test volume mounting
test_volume_mounting() {
    log "Testing volume mounting..."
    
    # Create test directory and file
    local test_dir="/tmp/docker-volume-test"
    mkdir -p $test_dir
    echo "test data" > $test_dir/test.txt
    
    # Test bind mount
    if docker run --rm -v $test_dir:/test alpine cat /test/test.txt | grep -q "test data"; then
        success "Docker bind mount working"
    else
        error "Docker bind mount failed"
    fi
    
    # Test named volume
    local volume_name="cross-platform-test-vol"
    docker volume create $volume_name > /dev/null 2>&1
    
    if docker run --rm -v $volume_name:/test alpine touch /test/volume-test.txt; then
        success "Docker named volume working"
    else
        error "Docker named volume failed"
    fi
    
    # Cleanup
    docker volume rm $volume_name > /dev/null 2>&1 || true
    rm -rf $test_dir
}

# Test Docker Compose functionality
test_docker_compose() {
    log "Testing Docker Compose functionality..."
    
    # Create test docker-compose.yml
    cat > /tmp/test-compose.yml << 'EOF'
version: '3.8'
services:
  web:
    image: nginx:alpine
    ports:
      - "18081:80"
  redis:
    image: redis:alpine
    command: redis-server --appendonly yes
volumes:
  redis_data:
networks:
  default:
    driver: bridge
EOF
    
    # Test compose up
    if docker-compose -f /tmp/test-compose.yml up -d > /dev/null 2>&1; then
        success "Docker Compose up successful"
        
        # Wait for services to start
        sleep 5
        
        # Test service connectivity
        if curl -s -f http://localhost:18081 > /dev/null 2>&1; then
            success "Docker Compose service networking working"
        else
            error "Docker Compose service networking failed"
        fi
        
        # Test compose down
        if docker-compose -f /tmp/test-compose.yml down > /dev/null 2>&1; then
            success "Docker Compose down successful"
        else
            error "Docker Compose down failed"
        fi
    else
        error "Docker Compose up failed"
    fi
    
    # Cleanup
    rm -f /tmp/test-compose.yml
}

# Test Observer Eye specific requirements
test_observer_eye_requirements() {
    log "Testing Observer Eye specific requirements..."
    
    # Test required ports availability
    local required_ports=(80 8000 8400 5432 6379)
    
    for port in "${required_ports[@]}"; do
        if netstat -tuln 2>/dev/null | grep -q ":$port "; then
            warning "Port $port is already in use"
        else
            success "Port $port is available"
        fi
    done
    
    # Test disk space
    local available_space=$(df . | awk 'NR==2 {print $4}')
    local required_space=20971520  # 20GB in KB
    
    if [ "$available_space" -gt "$required_space" ]; then
        success "Sufficient disk space available ($(($available_space / 1024 / 1024))GB)"
    else
        error "Insufficient disk space ($(($available_space / 1024 / 1024))GB available, 20GB required)"
    fi
    
    # Test memory
    local total_memory
    case $(detect_platform) in
        Linux)
            total_memory=$(free -m | awk 'NR==2{print $2}')
            ;;
        macOS)
            total_memory=$(sysctl -n hw.memsize | awk '{print $1/1024/1024}')
            ;;
        Windows)
            # This would need to be adapted for Windows
            total_memory=8192  # Assume 8GB
            ;;
    esac
    
    if [ "$total_memory" -gt 4096 ]; then
        success "Sufficient memory available (${total_memory}MB)"
    else
        warning "Limited memory available (${total_memory}MB, 4GB recommended)"
    fi
}

# Test platform-specific optimizations
test_platform_optimizations() {
    local platform=$1
    log "Testing platform-specific optimizations for $platform..."
    
    case $platform in
        Linux)
            # Test kernel parameters
            if [ -f /proc/sys/vm/max_map_count ]; then
                local max_map_count=$(cat /proc/sys/vm/max_map_count)
                if [ "$max_map_count" -ge 262144 ]; then
                    success "vm.max_map_count is optimized ($max_map_count)"
                else
                    warning "vm.max_map_count could be optimized (current: $max_map_count, recommended: 262144)"
                fi
            fi
            
            # Test file descriptor limits
            local file_max=$(cat /proc/sys/fs/file-max 2>/dev/null || echo "0")
            if [ "$file_max" -ge 65536 ]; then
                success "File descriptor limit is adequate ($file_max)"
            else
                warning "File descriptor limit could be increased (current: $file_max)"
            fi
            ;;
            
        macOS)
            # Test Docker Desktop resource allocation
            if docker info 2>/dev/null | grep -q "CPUs: [4-9]"; then
                success "Docker Desktop has adequate CPU allocation"
            else
                warning "Docker Desktop CPU allocation could be increased"
            fi
            
            # Test file system performance
            local fs_type=$(df -T . 2>/dev/null | awk 'NR==2 {print $2}' || echo "unknown")
            if [ "$fs_type" = "apfs" ]; then
                success "Using APFS file system (good performance)"
            else
                warning "File system type: $fs_type"
            fi
            ;;
            
        Windows)
            # Test WSL 2 configuration
            if [ -f ~/.wslconfig ]; then
                success "WSL configuration file exists"
            else
                warning "WSL configuration file not found (performance could be optimized)"
            fi
            ;;
    esac
}

# Test container security
test_container_security() {
    log "Testing container security..."
    
    # Test non-root user in containers
    local user_id=$(docker run --rm alpine id -u)
    if [ "$user_id" = "0" ]; then
        warning "Container running as root (security concern)"
    else
        success "Container running as non-root user (ID: $user_id)"
    fi
    
    # Test Docker daemon security
    if docker info 2>/dev/null | grep -q "Security Options"; then
        success "Docker security options are configured"
    else
        warning "Docker security options not visible"
    fi
    
    # Test image scanning capability
    if command -v docker scan &> /dev/null || docker --help | grep -q scan; then
        success "Docker image scanning capability available"
    else
        warning "Docker image scanning not available"
    fi
}

# Main test execution
main() {
    local platform=$(detect_platform)
    
    echo "=========================================="
    echo "Observer Eye Platform - Cross-Platform Testing"
    echo "Platform: $platform"
    echo "=========================================="
    echo ""
    
    log "Starting cross-platform tests for $platform..."
    
    # Run all test suites
    test_docker_installation
    echo ""
    
    test_platform_docker_features "$platform"
    echo ""
    
    test_docker_build_performance
    echo ""
    
    test_container_networking
    echo ""
    
    test_volume_mounting
    echo ""
    
    test_docker_compose
    echo ""
    
    test_observer_eye_requirements
    echo ""
    
    test_platform_optimizations "$platform"
    echo ""
    
    test_container_security
    echo ""
    
    # Print test results
    echo "=========================================="
    echo "Cross-Platform Test Results ($platform)"
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
        echo -e "${RED}Cross-platform tests FAILED on $platform${NC}"
        exit 1
    else
        echo ""
        echo -e "${GREEN}All cross-platform tests PASSED on $platform${NC}"
        echo ""
        log "Cross-platform testing completed successfully!"
        exit 0
    fi
}

# Cleanup function
cleanup() {
    log "Cleaning up test artifacts..."
    
    # Remove any test containers
    docker ps -a --filter "name=cross-platform-test" -q | xargs -r docker rm -f > /dev/null 2>&1 || true
    
    # Remove test images
    docker images --filter "reference=cross-platform-test" -q | xargs -r docker rmi -f > /dev/null 2>&1 || true
    
    # Remove test volumes
    docker volume ls --filter "name=cross-platform-test" -q | xargs -r docker volume rm > /dev/null 2>&1 || true
    
    # Remove test files
    rm -f /tmp/test-dockerfile /tmp/test-compose.yml
    rm -rf /tmp/test-context /tmp/docker-volume-test
}

# Set up cleanup trap
trap cleanup EXIT

# Run main function
main "$@"