# Multi-stage Dockerfile for FastAPI Middleware with eBPF Integration
# Observer-Eye Observability Platform - Business Logic Layer

# ============================================================================
# Build Stage: Dependency Installation and eBPF Toolchain Setup
# ============================================================================
FROM python:3.11-slim as builder

# Set build arguments
ARG DEBIAN_FRONTEND=noninteractive
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

# Add metadata labels
LABEL maintainer="Observer-Eye Platform Team"
LABEL org.opencontainers.image.title="Observer-Eye FastAPI Middleware"
LABEL org.opencontainers.image.description="Business logic layer with eBPF integration and deep system monitoring"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.revision="${VCS_REF}"
LABEL org.opencontainers.image.vendor="Observer-Eye Platform"

# Install system dependencies for basic monitoring and development
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build essentials
    build-essential \
    gcc \
    g++ \
    # System monitoring libraries
    libelf-dev \
    zlib1g-dev \
    libssl-dev \
    libffi-dev \
    # Network and payload inspection
    libpcap-dev \
    # Database and connectivity
    libpq-dev \
    # Basic networking tools
    netcat-openbsd \
    # Process monitoring
    procps \
    # Cleanup
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

# Create build user for security
RUN useradd --create-home --shell /bin/bash --uid 1001 builder

# Set working directory
WORKDIR /build

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies with optimization
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --user --no-warn-script-location \
    -r requirements.txt && \
    # Verify core dependencies
    python -c "import psutil; print('psutil installed successfully')" && \
    python -c "import fastapi; print('FastAPI installed successfully')" && \
    # Clean up pip cache
    pip cache purge

# ============================================================================
# Production Stage: Optimized Runtime Environment
# ============================================================================
FROM python:3.11-slim as production

# Set production arguments
ARG DEBIAN_FRONTEND=noninteractive

# Install minimal runtime dependencies for system monitoring
RUN apt-get update && apt-get install -y --no-install-recommends \
    # System monitoring tools
    procps \
    htop \
    # Network tools for basic inspection
    libpcap0.8 \
    iproute2 \
    net-tools \
    # Database connectivity
    libpq5 \
    # Security and SSL
    ca-certificates \
    openssl \
    # Process management
    dumb-init \
    # Cleanup
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

# Create non-root user for security hardening
RUN groupadd --gid 1001 observer && \
    useradd --uid 1001 --gid observer --shell /bin/bash --create-home observer

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder stage
COPY --from=builder --chown=observer:observer /root/.local /home/observer/.local

# Copy application code
COPY --chown=observer:observer . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/data /app/tmp && \
    chown -R observer:observer /app && \
    chmod -R 755 /app

# Set environment variables for production
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/home/observer/.local/bin:$PATH \
    # FastAPI configuration
    FASTAPI_ENV=production \
    FASTAPI_HOST=0.0.0.0 \
    FASTAPI_PORT=8000 \
    FASTAPI_WORKERS=4 \
    # eBPF and monitoring configuration
    EBPF_ENABLED=true \
    DEEP_MONITORING_ENABLED=true \
    KERNEL_MONITORING_ENABLED=true \
    PAYLOAD_INSPECTION_ENABLED=true \
    # Performance tuning
    UVICORN_LOOP=uvloop \
    UVICORN_HTTP=httptools \
    # Security
    PYTHONHASHSEED=random \
    # Logging
    LOG_LEVEL=INFO \
    LOG_FORMAT=json

# Switch to non-root user
USER observer

# Health check configuration
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health', timeout=5)" || exit 1

# Expose port
EXPOSE 8000

# Use dumb-init for proper signal handling
ENTRYPOINT ["/usr/bin/dumb-init", "--"]

# Default command with production optimizations
CMD ["uvicorn", "main:mymiddleware", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--loop", "uvloop", \
     "--http", "httptools", \
     "--access-log", \
     "--log-level", "info"]

# ============================================================================
# Development Stage: Development Environment with Hot Reload
# ============================================================================
FROM production as development

# Switch back to root for development tools installation
USER root

# Install development tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Development tools
    git \
    curl \
    wget \
    vim \
    # Debugging tools
    gdb \
    strace \
    ltrace \
    # eBPF development tools
    bpftrace \
    # Network debugging
    tcpdump \
    wireshark-common \
    # Performance profiling
    perf-tools-unstable \
    # Cleanup
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install development Python packages
RUN pip install --no-cache-dir \
    # Development tools
    black \
    isort \
    flake8 \
    mypy \
    # Debugging
    ipdb \
    pdbpp \
    # Testing
    pytest-cov \
    pytest-xdist \
    # Documentation
    sphinx \
    # Hot reload
    watchdog

# Switch back to observer user
USER observer

# Override environment for development
ENV FASTAPI_ENV=development \
    FASTAPI_RELOAD=true \
    LOG_LEVEL=DEBUG \
    EBPF_DEBUG=true

# Development command with hot reload
CMD ["uvicorn", "main:mymiddleware", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--reload", \
     "--log-level", "debug"]

# ============================================================================
# Testing Stage: Isolated Testing Environment
# ============================================================================
FROM development as testing

# Switch to root for test dependencies
USER root

# Install testing-specific tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Testing tools
    docker.io \
    # Mock eBPF environment
    linux-headers-$(uname -r) || true \
    # Cleanup
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Switch back to observer user
USER observer

# Set testing environment
ENV FASTAPI_ENV=testing \
    TESTING=true \
    EBPF_MOCK_MODE=true \
    DATABASE_URL=sqlite:///test.db

# Copy test files if they exist
COPY --chown=observer:observer test*.py ./
RUN mkdir -p tests

# Default testing command
CMD ["python", "-m", "pytest", "-v", "--tb=short"]