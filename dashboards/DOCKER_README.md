# Observer-Eye Angular Dashboard - Docker Setup

This directory contains the containerized Angular dashboard for the Observer-Eye observability platform with 3D visualization and BI reporting capabilities.

## Features

- **Angular 21.0.0** with Server-Side Rendering (SSR)
- **TailwindCSS 4.1.12** for styling
- **3D Visualization Libraries**: Three.js, D3.js, ECharts, Vis.js
- **BI Reporting Components**: Chart.js, interactive dashboards
- **WebGL Support** for high-performance 3D rendering
- **Real-time Data Streaming** via WebSocket connections
- **Multi-stage Docker Build** for optimized production images
- **Nginx** reverse proxy with optimized configuration

## Docker Files

### Production Dockerfile
- **File**: `Dockerfile`
- **Base Images**: Node.js 20 Alpine (build), Nginx Alpine (runtime)
- **Features**: Multi-stage build, dependency caching, security hardening
- **Size Optimization**: Removes dev dependencies and build artifacts

### Development Dockerfile
- **File**: `Dockerfile.dev`
- **Base Image**: Node.js 20 Alpine
- **Features**: Hot reload, development dependencies, debugging support

### Nginx Configuration
- **File**: `nginx.conf` - Full production configuration with upstream services
- **File**: `nginx-standalone.conf` - Standalone testing without dependencies

## Build Commands

### Production Build
```bash
# Build the production image
docker build -t observer-eye-dashboard:latest .

# Build with specific tag
docker build -t observer-eye-dashboard:v1.0.0 .
```

### Development Build
```bash
# Build development image
docker build -f Dockerfile.dev -t observer-eye-dashboard:dev .
```

## Run Commands

### Production Container
```bash
# Run with full configuration (requires middleware and backend services)
docker run -d --name observer-dashboard -p 80:80 observer-eye-dashboard:latest

# Run in standalone mode for testing
docker run -d --name observer-dashboard-test -p 8080:80 \
  -v $(pwd)/nginx-standalone.conf:/etc/nginx/nginx.conf \
  observer-eye-dashboard:latest
```

### Development Container
```bash
# Run development server with hot reload
docker run -d --name observer-dashboard-dev -p 4200:4200 \
  -v $(pwd):/app \
  -v /app/node_modules \
  observer-eye-dashboard:dev
```

## Health Checks

The container includes built-in health check endpoints:

```bash
# Health check
curl http://localhost:8080/health
# Response: healthy

# Metrics endpoint
curl http://localhost:8080/metrics
# Response: # Observer-Eye Dashboard Metrics\ndashboard_status 1
```

## Docker Compose Integration

### Development Environment
```yaml
services:
  dashboard:
    build:
      context: ./dashboards
      dockerfile: Dockerfile.dev
    ports:
      - "4200:4200"
    volumes:
      - ./dashboards:/app
      - /app/node_modules
    environment:
      - NODE_ENV=development
```

### Production Environment
```yaml
services:
  dashboard:
    build:
      context: ./dashboards
      dockerfile: Dockerfile
    ports:
      - "80:80"
    depends_on:
      - middleware
      - backend
    environment:
      - NODE_ENV=production
```

## Build Performance

- **Full Build Time**: ~10-15 minutes (includes npm install and Angular build)
- **Incremental Build**: ~2-3 minutes (with Docker layer caching)
- **Final Image Size**: ~50MB (nginx + built Angular app)
- **Build Optimization**: Multi-stage build removes ~800MB of build dependencies

## Security Features

- **Non-root User**: Container runs as `nginx-app` user (UID 1001)
- **Security Headers**: CSP, HSTS, X-Frame-Options, etc.
- **CORS Configuration**: Configurable cross-origin resource sharing
- **Minimal Attack Surface**: Only production files in final image

## 3D Visualization Support

The container includes optimized support for:

- **WebGL Assets**: `.glb`, `.gltf`, `.obj`, `.mtl` files
- **WASM Modules**: WebAssembly for high-performance computing
- **Texture Caching**: Optimized caching for 3D model textures
- **GPU Acceleration**: WebGL context optimization

## API Proxy Configuration

The nginx configuration includes proxy settings for:

- **Middleware API**: `/api/` → `http://middleware:8000/`
- **WebSocket**: `/ws/` → `http://middleware:8000/ws/`
- **BI Analytics**: `/analytics/` → `http://bi-analytics:8002/`

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NODE_ENV` | Build environment | `production` |
| `NODE_OPTIONS` | Node.js memory options | `--max-old-space-size=4096` |

## Troubleshooting

### Build Issues
```bash
# Clear Docker build cache
docker builder prune

# Build without cache
docker build --no-cache -t observer-eye-dashboard:latest .
```

### Runtime Issues
```bash
# Check container logs
docker logs observer-dashboard

# Check nginx configuration
docker exec observer-dashboard nginx -t

# Access container shell
docker exec -it observer-dashboard sh
```

### Common Problems

1. **Build Fails with Node.js Version Error**
   - Ensure using Node.js 20+ (Angular 21 requirement)
   - Update Dockerfile base image if needed

2. **Container Exits with Permission Denied**
   - Check nginx.conf pid file location (`/tmp/nginx.pid`)
   - Verify file permissions in Dockerfile

3. **Static Assets Not Loading**
   - Check nginx static file configuration
   - Verify build output in `/usr/share/nginx/html`

## Development Workflow

1. **Local Development**:
   ```bash
   npm install
   npm start
   ```

2. **Container Testing**:
   ```bash
   docker build -t test .
   docker run -p 8080:80 test
   ```

3. **Production Deployment**:
   ```bash
   docker build -t observer-eye-dashboard:v1.0.0 .
   docker push registry/observer-eye-dashboard:v1.0.0
   ```

## Performance Optimization

- **Gzip Compression**: Enabled for all text assets
- **Static Caching**: 1-year cache for immutable assets
- **Bundle Splitting**: Angular CLI automatic code splitting
- **Tree Shaking**: Removes unused code in production builds
- **Minification**: CSS and JS minification enabled

## Monitoring

The container exposes metrics for monitoring:

- **Health Status**: `/health` endpoint
- **Application Metrics**: `/metrics` endpoint
- **Nginx Status**: Built-in nginx metrics
- **Container Stats**: Docker stats integration