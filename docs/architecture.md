# Observer Eye Platform - Technical Architecture

## Architecture Overview

The Observer Eye Platform implements a modern 3-layer architecture with clear separation of concerns, designed for scalability, maintainability, and performance. Each layer is containerized and can be deployed independently, enabling flexible deployment strategies and horizontal scaling.

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                       │
│                     Angular 21 (Port 80)                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │ Dashboard   │ │ Auth Module │ │ Component Library      │ │
│  │ Components  │ │ & Guards    │ │ & Shared Services      │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │ HTTP/WebSocket
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Logic Layer                            │
│                 FastAPI Middleware (Port 8400)             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │ Data        │ │ Performance │ │ Caching & Error         │ │
│  │ Processing  │ │ Monitoring  │ │ Handling                │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │ CRUD        │ │ Telemetry   │ │ Real-time Streaming     │ │
│  │ Operations  │ │ Collection  │ │ & Data Ingestion        │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │ HTTP/Database
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       Data Layer                            │
│                   Django Backend (Port 8000)               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │ Core Models │ │ Analytics   │ │ Performance Monitoring  │ │
│  │ & Auth      │ │ Engine      │ │ Apps                    │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │ Metrics     │ │ Notification│ │ Dashboard Templates     │ │
│  │ Collection  │ │ System      │ │ & Settings              │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Layer Responsibilities

### Presentation Layer (Angular 21)

**Technology Stack:**
- Angular 21 with Server-Side Rendering (SSR)
- TailwindCSS 4.x for styling
- Vitest for testing
- TypeScript for type safety

**Core Responsibilities:**
- User interface rendering and interaction
- Real-time data visualization with charts and dashboards
- User authentication and session management
- Client-side routing and navigation
- WebSocket connections for real-time updates

**Key Components:**
- **Authentication Module**: OAuth integration, login/logout, session management
- **Dashboard Components**: Customizable widgets, real-time charts, metric cards
- **Component Library**: Reusable UI components (buttons, forms, modals, tables)
- **Service Layer**: HTTP clients, state management, error handling

### Logic Layer (FastAPI Middleware)

**Technology Stack:**
- FastAPI for high-performance API development
- Uvicorn ASGI server
- Pydantic for data validation
- OpenTelemetry for observability
- Redis for caching

**Core Responsibilities:**
- Data transformation, validation, and normalization
- Performance monitoring and metrics collection
- Caching and performance optimization
- Error handling and circuit breaker patterns
- Real-time streaming data ingestion
- API orchestration between frontend and backend

**Key Modules:**

#### Data Processing Pipeline
```python
# Data flow through processing stages
Raw Data → Validation → Filtering → Normalization → Sanitization → Output
```
- **Validation**: Schema validation, data type checking, business rule enforcement
- **Filtering**: Data filtering based on configurable rules and patterns
- **Normalization**: Data format standardization and unit conversion
- **Sanitization**: Security-focused data cleaning and validation

#### Performance Monitoring
- Real-time metrics collection and aggregation
- Performance analysis and bottleneck detection
- Resource utilization monitoring
- Health check endpoints and system diagnostics

#### Caching System
- Multi-level caching with Redis backend
- Intelligent cache invalidation strategies
- Cache performance monitoring and optimization
- Distributed caching for horizontal scaling

#### Error Handling & Resilience
- Circuit breaker patterns for external service calls
- Graceful degradation mechanisms
- Comprehensive error logging and reporting
- Retry logic with exponential backoff

#### Real-time Data Ingestion
- Streaming data ingestion with quality validation
- Batch processing with deduplication
- Real-time data quality analysis
- Buffer management and flow control

### Data Layer (Django Backend)

**Technology Stack:**
- Django 6.0+ with REST framework
- SQLite (development) / PostgreSQL (production)
- OpenTelemetry integration
- Structlog for structured logging

**Core Responsibilities:**
- Data persistence and database management
- Business logic implementation
- RESTful API endpoints
- User management and authentication
- Analytics and reporting

**Django Applications:**

#### Core Applications
- **core**: User management, authentication, audit logging
- **analytics**: Business intelligence and data analysis
- **notification**: Multi-channel alerting and notification system
- **settings**: Platform configuration and user preferences
- **template_dashboards**: Dashboard template management

#### Performance Monitoring Applications
- **application_performance_monitoring**: APM metrics and analysis
- **system_performance_monitoring**: System resource monitoring
- **network_performance_monitoring**: Network traffic analysis
- **security_performance_monitoring**: Security event monitoring
- **identity_performance_monitoring**: Identity provider performance
- **traffic_performance_monitoring**: Traffic pattern analysis
- **analytics_performance_monitoring**: Analytics system performance

#### Metrics Collection Applications
- **appmetrics**: Application-specific metrics
- **netmetrics**: Network performance metrics
- **securitymetrics**: Security-related metrics
- **sysmetrics**: System performance metrics

#### Integration Applications
- **integration**: External system connectors and data import/export
- **grailobserver**: Specialized observability features

## Data Flow Architecture

### Request Flow
```
User Request → Angular Frontend → FastAPI Middleware → Django Backend
                     ↓                    ↓                  ↓
              Client Validation    Data Processing     Database Operations
                     ↓                    ↓                  ↓
              UI State Update     Cache Management    Response Generation
                     ↓                    ↓                  ↓
              Real-time Updates   Performance Metrics   Audit Logging
```

### Data Ingestion Flow
```
External Data Sources → FastAPI Ingestion Endpoints → Data Quality Validation
                                    ↓
                            Buffer Management & Batching
                                    ↓
                            Django Backend Processing
                                    ↓
                            Database Persistence & Analytics
```

### Real-time Streaming Flow
```
Real-time Data → WebSocket Connection → FastAPI Stream Handler
                        ↓
                 Data Quality Analysis
                        ↓
                 Buffer & Batch Processing
                        ↓
                 Django Backend Ingestion
                        ↓
                 Frontend Real-time Updates
```

## Security Architecture

### Authentication & Authorization
- OAuth 2.0 integration with multiple providers (GitHub, GitLab, Google, Microsoft)
- JWT token-based authentication
- Role-based access control (RBAC)
- Session management with secure cookies

### Data Security
- Input validation and sanitization at all layers
- SQL injection prevention through ORM usage
- XSS protection with content security policies
- HTTPS enforcement and secure headers

### Container Security
- Non-root user execution in all containers
- Minimal base images with security updates
- Secret management through environment variables
- Network isolation and firewall rules

## Performance Architecture

### Caching Strategy
```
Browser Cache → CDN → FastAPI Cache → Database Query Cache
     ↓              ↓         ↓              ↓
Static Assets   API Responses  Computed Data   Query Results
```

### Horizontal Scaling
- Stateless application design
- Load balancer compatibility
- Database connection pooling
- Distributed caching with Redis

### Performance Monitoring
- Real-time performance metrics collection
- Application performance monitoring (APM)
- Database query optimization
- Resource utilization tracking

## Deployment Architecture

### Development Environment
```
Docker Compose
├── Angular Development Server (Port 4200)
├── FastAPI with Hot Reload (Port 8400)
├── Django Development Server (Port 8000)
├── Redis Cache (Port 6379)
└── PostgreSQL Database (Port 5432)
```

### Production Environment
```
Container Orchestration (Docker/Kubernetes)
├── Angular Production Build + Nginx (Port 80)
├── FastAPI with Uvicorn (Port 8400)
├── Django with Gunicorn (Port 8000)
├── Redis Cluster (High Availability)
└── PostgreSQL Cluster (High Availability)
```

### Cross-Platform Support
- **Linux**: Native Docker support, optimal performance
- **macOS**: Docker Desktop, development-friendly
- **Windows**: Docker Desktop with WSL2, full compatibility

## Monitoring and Observability

### Application Monitoring
- OpenTelemetry integration across all layers
- Distributed tracing for request flow analysis
- Custom metrics collection and reporting
- Health check endpoints for all services

### Logging Strategy
- Structured logging with JSON format
- Centralized log aggregation
- Log level configuration per environment
- Audit trail for security and compliance

### Alerting and Notifications
- Multi-channel notification system (email, Slack, webhooks)
- Configurable alert rules and thresholds
- Escalation policies and notification routing
- Alert correlation and deduplication

## Technology Decisions and Rationale

### Frontend: Angular 21
- **Mature Framework**: Stable, well-documented, enterprise-ready
- **TypeScript**: Strong typing for large-scale applications
- **SSR Support**: Improved SEO and initial load performance
- **Component Architecture**: Reusable, maintainable UI components

### Middleware: FastAPI
- **High Performance**: Async/await support, excellent throughput
- **Automatic Documentation**: OpenAPI/Swagger integration
- **Type Safety**: Pydantic models for request/response validation
- **Modern Python**: Latest Python features and best practices

### Backend: Django
- **Rapid Development**: Built-in admin, ORM, authentication
- **Scalability**: Proven in large-scale applications
- **Security**: Built-in protection against common vulnerabilities
- **Ecosystem**: Rich third-party package ecosystem

### Database: PostgreSQL
- **ACID Compliance**: Data integrity and consistency
- **JSON Support**: Flexible schema for analytics data
- **Performance**: Excellent query optimization and indexing
- **Scalability**: Horizontal scaling with read replicas

### Caching: Redis
- **High Performance**: In-memory data structure store
- **Persistence**: Optional data persistence for reliability
- **Clustering**: Built-in support for horizontal scaling
- **Data Structures**: Rich data types for complex caching scenarios

## Future Architecture Considerations

### Microservices Evolution
- Potential decomposition of Django backend into microservices
- Service mesh implementation for inter-service communication
- Event-driven architecture with message queues

### Cloud-Native Features
- Kubernetes deployment manifests
- Auto-scaling based on metrics
- Service discovery and load balancing
- Cloud storage integration

### Advanced Analytics
- Machine learning pipeline integration
- Real-time stream processing with Apache Kafka
- Time-series database for metrics storage
- Advanced visualization with custom charting libraries