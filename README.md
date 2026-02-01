# Observer Eye Platform

A comprehensive 3-layer observability platform designed for enterprise monitoring and analytics. The platform provides real-time insights into system performance, security metrics, application health, and network traffic.

## Architecture

```
Internet Users
      ↓
┌─────────────────┐
│ Presentation    │  Angular 21 (Port 80/4200)
│ Layer           │  - Authentication & UI
│ (Dashboard)     │  - Real-time visualization
└─────────────────┘  - TailwindCSS styling
      ↓
┌─────────────────┐
│ Logic Layer     │  FastAPI (Port 8400)
│ (Middleware)    │  - Data transformation
│                 │  - Performance monitoring
└─────────────────┘  - Caching & streaming
      ↓
┌─────────────────┐
│ Data Layer      │  Django 6.0+
│ (Backend)       │  - Multiple specialized apps
│                 │  - Analytics & BI
└─────────────────┘  - Security monitoring
```

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm

### Setup Development Environment

1. **Clone and navigate to the project:**
   ```bash
   cd observer-eye
   ```

2. **Run the setup script:**
   ```bash
   ./dev-setup.sh
   ```

3. **Start the services (in separate terminals):**
   ```bash
   # Terminal 1 - Backend
   ./start-backend.sh
   
   # Terminal 2 - Middleware
   ./start-middleware.sh
   
   # Terminal 3 - Frontend
   ./start-frontend.sh
   ```

### Access the Platform

- **Frontend Dashboard**: http://localhost:4200
- **Middleware API**: http://localhost:8400
- **Backend Admin**: http://localhost:8000/admin

## Technology Stack

### Frontend (Presentation Layer)
- **Framework**: Angular 21 with SSR support
- **Styling**: TailwindCSS 4.x
- **Testing**: Vitest
- **Build Tool**: Angular CLI

### Middleware (Logic Layer)
- **Framework**: FastAPI
- **Server**: Uvicorn
- **Testing**: pytest
- **Data Processing**: pandas, numpy

### Backend (Data Layer)
- **Framework**: Django 6.0+
- **Database**: SQLite (dev), PostgreSQL (prod)
- **Testing**: pytest
- **Observability**: OpenTelemetry

## Project Structure

```
observer-eye/
├── dashboard/          # Angular 21 frontend
│   ├── src/app/       # Application code
│   ├── src/environments/ # Environment configs
│   └── tailwind.config.js # Styling configuration
├── middleware/         # FastAPI logic layer
│   ├── main.py        # Application entry point
│   ├── performance/   # Performance monitoring
│   ├── error_handling/ # Error handling
│   ├── caching/       # Caching mechanisms
│   ├── streaming/     # Real-time streaming
│   └── telemetry/     # Observability
└── backend/           # Django data layer
    └── observer/      # Django project
        ├── analytics/ # BI analysis
        ├── core/      # Core functionality
        ├── notification/ # Alerting system
        └── [15+ specialized apps]
```

## Key Features

### 🔐 Authentication & Security
- Multi-provider OAuth (GitHub, GitLab, Google, Microsoft)
- Password strength validation (16+ chars, complexity requirements)
- Secure session management
- Security performance monitoring

### 📊 Monitoring & Analytics
- Multi-layer performance monitoring
- Real-time analytics and BI capabilities
- Application, system, network, and security metrics
- Template-based dashboard system

### 🚀 Real-time Capabilities
- WebSocket-based streaming
- Live data visualization
- Real-time alerting and notifications
- Performance threshold monitoring

### 🔧 Enterprise Features
- Comprehensive error handling and resilience
- Distributed caching
- Telemetry collection and processing
- Integration capabilities for external systems

## Development Commands

### Backend (Django)
```bash
cd backend/observer
source ../venv1/bin/activate

# Development
python manage.py runserver
python manage.py migrate
python manage.py makemigrations

# Testing
python manage.py test
pytest
```

### Middleware (FastAPI)
```bash
cd middleware
source venv0/bin/activate

# Development
python main.py
uvicorn main:app --reload --port 8400

# Testing
pytest
```

### Frontend (Angular)
```bash
cd dashboard

# Development
npm start
npm run build
npm test

# SSR
npm run serve:ssr:dashboard
```

## Testing Strategy

The platform uses a dual testing approach:

- **Unit Tests**: Specific examples and edge cases
- **Property-Based Tests**: Universal properties across all inputs
- **Integration Tests**: End-to-end workflows
- **Performance Tests**: Load and stress testing

## Configuration

### Environment Variables

**Frontend** (`dashboard/src/environments/`):
- API endpoints and WebSocket URLs
- OAuth provider configurations
- Feature flags and caching settings

**Backend** (`backend/observer/observer/settings.py`):
- Database configurations
- CORS settings
- Security configurations
- Logging and caching

## Security

- Non-root container users
- Secure password policies (16+ characters, complexity)
- HTTPS enforcement in production
- CORS configuration for cross-origin requests
- Security headers and XSS protection

## Production Deployment

The platform is designed for containerized deployment with:
- Docker containers for each layer
- Cross-platform support (Linux, macOS, Windows)
- Environment-specific configurations
- Health checks and graceful shutdown
- No mock/seed data in production builds

## Contributing

1. Follow the established project structure
2. Maintain separation of concerns across layers
3. Write comprehensive tests (unit + property-based)
4. Follow security best practices
5. No mock data in production code

## License

Enterprise observability platform for comprehensive system monitoring.