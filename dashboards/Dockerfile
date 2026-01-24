# Multi-stage Dockerfile for Angular Dashboard with 3D Visualization and BI Reporting
# Observer-Eye Observability Platform - Presentation Layer
# Supports Angular 21.0.0 with SSR, TailwindCSS 4.1.12, and WebGL capabilities

# ============================================================================
# Stage 1: Build Stage with All Dependencies
# ============================================================================
FROM node:20-alpine AS builder

# Set working directory
WORKDIR /app

# Install system dependencies for 3D visualization and WebGL support
RUN apk add --no-cache \
    python3 \
    make \
    g++ \
    cairo-dev \
    jpeg-dev \
    pango-dev \
    musl-dev \
    giflib-dev \
    pixman-dev \
    pangomm-dev \
    libjpeg-turbo-dev \
    freetype-dev

# Copy package files for dependency caching
COPY package*.json ./

# Install all dependencies (needed for build process)
RUN npm ci --legacy-peer-deps --silent --no-audit --no-fund && \
    npm cache clean --force

# Copy source code
COPY . .

# Set build environment variables for optimization
ENV NODE_ENV=production
ENV NODE_OPTIONS="--max-old-space-size=4096"

# Build the Angular application with SSR support
# Includes 3D visualization libraries and BI reporting components
RUN npm run build:production && \
    # Verify build outputs
    ls -la dist/

# ============================================================================
# Stage 2: Production Runtime Stage
# ============================================================================
FROM nginx:alpine AS production

# Install runtime dependencies for WebGL and 3D visualization support
RUN apk add --no-cache \
    curl \
    ca-certificates \
    tzdata

RUN  rm -rf /usr/share/nginx/html/*

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy built application from builder stage
COPY --from=builder /app/dist/dashboards/browser /usr/share/nginx/html

# Create non-root user for security
RUN addgroup -g 1001 -S nginx-app && \
    adduser -S -D -H -u 1001 -h /var/cache/nginx -s /sbin/nologin -G nginx-app -g nginx-app nginx-app

# Set proper permissions
RUN chown -R nginx-app:nginx-app /usr/share/nginx/html && \
    chown -R nginx-app:nginx-app /var/cache/nginx && \
    chown -R nginx-app:nginx-app /var/log/nginx && \
    chown -R nginx-app:nginx-app /etc/nginx/conf.d && \
    touch /tmp/nginx.pid && \
    chown nginx-app:nginx-app /tmp/nginx.pid

# Create directories for nginx
RUN mkdir -p /var/cache/nginx/client_temp && \
    mkdir -p /var/cache/nginx/proxy_temp && \
    mkdir -p /var/cache/nginx/fastcgi_temp && \
    mkdir -p /var/cache/nginx/uwsgi_temp && \
    mkdir -p /var/cache/nginx/scgi_temp && \
    chown -R nginx-app:nginx-app /var/cache/nginx

# Switch to non-root user
USER nginx-app

# Expose port 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

# Labels for container metadata
LABEL maintainer="Observer-Eye Platform Team"
LABEL version="1.0.0"
LABEL description="Angular Dashboard with 3D Visualization and BI Reporting for Observer-Eye Observability Platform"
LABEL org.opencontainers.image.title="Observer-Eye Angular Dashboard"
LABEL org.opencontainers.image.description="Presentation layer with 3D visualization, real-time dashboards, and BI reporting"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.vendor="Observer-Eye Platform"

# Start nginx
CMD ["nginx", "-g", "daemon off;"]