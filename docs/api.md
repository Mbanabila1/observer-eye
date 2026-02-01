# Observer Eye Platform - API Documentation

## API Overview

The Observer Eye Platform provides comprehensive RESTful APIs across three layers:

- **Frontend API**: Angular services for UI interactions
- **Middleware API**: FastAPI endpoints for data processing and orchestration
- **Backend API**: Django REST endpoints for data persistence and business logic

## Middleware API (FastAPI) - Port 8400

### Base URL
- Development: `http://localhost:8400`
- Production: `https://your-domain.com/api`

### Authentication

Most endpoints require authentication via Bearer token:

```http
Authorization: Bearer <your-jwt-token>
```

### Health Check Endpoints

#### Basic Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "middleware",
  "version": "1.0.0",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### Detailed Health Check
```http
GET /health/detailed
```

**Response:**
```json
{
  "status": "healthy",
  "service": "middleware",
  "version": "1.0.0",
  "metrics": {
    "cpu_usage": 45.2,
    "memory_usage": 67.8,
    "disk_usage": 23.1,
    "uptime_seconds": 3600
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Data Processing Endpoints

#### Process Data
```http
POST /data/process
Content-Type: application/json
```

**Request Body:**
```json
{
  "data": {
    "metrics": [
      {
        "name": "cpu_usage",
        "value": 75.5,
        "timestamp": "2024-01-01T12:00:00Z"
      }
    ]
  },
  "schema_name": "metrics_schema"
}
```

**Response:**
```json
{
  "success": true,
  "processed_data": {
    "metrics": [
      {
        "name": "cpu_usage",
        "value": 75.5,
        "timestamp": "2024-01-01T12:00:00Z",
        "normalized": true
      }
    ]
  },
  "errors": [],
  "warnings": [],
  "processing_time_ms": 45.2,
  "stages_completed": ["validation", "filtering", "normalization"],
  "metadata": {
    "processor_version": "1.0.0",
    "schema_version": "1.2.0"
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "processed_by": "user123"
}
```

#### Validate Data
```http
POST /data/validate
Content-Type: application/json
```

**Request Body:**
```json
{
  "data": {
    "field1": "value1",
    "field2": 123
  },
  "schema_name": "validation_schema"
}
```

**Response:**
```json
{
  "is_valid": true,
  "status": "valid",
  "errors": [],
  "warnings": [
    {
      "field": "field2",
      "message": "Value is within acceptable range but close to limit",
      "code": "WARN_001",
      "value": 123
    }
  ],
  "validated_data": {
    "field1": "value1",
    "field2": 123
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### Get Pipeline Statistics
```http
GET /data/pipeline/stats
```

**Response:**
```json
{
  "pipeline_stats": {
    "total_processed": 15420,
    "success_rate": 98.5,
    "average_processing_time_ms": 23.4,
    "error_count": 231,
    "warning_count": 45
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "requested_by": "user123"
}
```

### Data Ingestion Endpoints

#### Ingest Streaming Data
```http
POST /data/ingest/streaming
Content-Type: application/json
```

**Request Body:**
```json
{
  "data": {
    "metric_name": "cpu_usage",
    "value": 75.5,
    "timestamp": "2024-01-01T12:00:00Z",
    "source": "server-01"
  },
  "data_type": "real_time_metrics"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Data queued for processing",
  "buffer_size": 45,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### Ingest Batch Data
```http
POST /data/ingest/batch
Content-Type: application/json
```

**Request Body:**
```json
{
  "data": [
    {
      "metric_name": "cpu_usage",
      "value": 75.5,
      "timestamp": "2024-01-01T12:00:00Z"
    },
    {
      "metric_name": "memory_usage",
      "value": 67.8,
      "timestamp": "2024-01-01T12:00:00Z"
    }
  ],
  "data_type": "real_time_metrics"
}
```

**Response:**
```json
{
  "success": true,
  "records_processed": 2,
  "quality_metrics": {
    "completeness": 1.0,
    "accuracy": 1.0,
    "timeliness": 0.95,
    "consistency": 1.0,
    "overall": 0.9875
  },
  "backend_response": {
    "success": true,
    "records_saved": 2
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### Get Ingestion Statistics
```http
GET /data/ingest/stats
```

**Response:**
```json
{
  "service_status": "running",
  "buffer_sizes": {
    "real_time_metrics": 23,
    "log_stream": 12,
    "telemetry_stream": 8
  },
  "quality_metrics": {
    "real_time_metrics": {
      "completeness": 0.98,
      "accuracy": 0.99,
      "timeliness": 0.95,
      "consistency": 0.97
    }
  },
  "performance_metrics": {
    "requests_per_second": 145.2,
    "average_response_time_ms": 12.3
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Cache Management Endpoints

#### Get Cache Statistics
```http
GET /cache/stats
```

**Response:**
```json
{
  "cache_stats": {
    "total_keys": 1523,
    "memory_usage_bytes": 45231680,
    "hit_rate": 0.87,
    "miss_rate": 0.13,
    "eviction_count": 45
  },
  "invalidation_stats": {
    "total_invalidations": 234,
    "pattern_invalidations": 123,
    "key_invalidations": 111
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "requested_by": "user123"
}
```

#### Invalidate Cache
```http
POST /cache/invalidate
Content-Type: application/json
```

**Request Body (by key):**
```json
{
  "key": "user:123:profile"
}
```

**Request Body (by pattern):**
```json
{
  "pattern": "user:*:profile"
}
```

**Request Body (by event):**
```json
{
  "event_type": "user_updated",
  "event_data": {
    "user_id": "123"
  }
}
```

**Response:**
```json
{
  "success": true,
  "invalidated_count": 15,
  "timestamp": "2024-01-01T12:00:00Z",
  "invalidated_by": "user123"
}
```

### CRUD Operations

#### Handle CRUD Operation
```http
POST /crud
Content-Type: application/json
```

**Request Body:**
```json
{
  "operation": "create",
  "app_name": "analytics",
  "model_name": "AnalyticsData",
  "data": {
    "name": "CPU Usage Report",
    "description": "Daily CPU usage analytics",
    "data": {
      "average_cpu": 65.2,
      "peak_cpu": 89.1
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "operation": "create",
  "model": "AnalyticsData",
  "data": {
    "id": 123,
    "name": "CPU Usage Report",
    "description": "Daily CPU usage analytics",
    "created_at": "2024-01-01T12:00:00Z"
  },
  "audit_log_id": "audit_456",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Telemetry Endpoints

#### Collect Single Telemetry
```http
POST /telemetry
Content-Type: application/json
```

**Request Body:**
```json
{
  "trace_id": "abc123def456",
  "span_id": "span789",
  "operation": "database_query",
  "duration_ms": 45.2,
  "status": "success",
  "attributes": {
    "query": "SELECT * FROM users",
    "rows_returned": 150
  }
}
```

**Response:**
```json
{
  "success": true,
  "telemetry_id": "tel_789",
  "message": "Telemetry data collected successfully",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### Collect Telemetry Batch
```http
POST /telemetry/batch
Content-Type: application/json
```

**Request Body:**
```json
[
  {
    "trace_id": "abc123",
    "span_id": "span1",
    "operation": "api_call",
    "duration_ms": 23.1
  },
  {
    "trace_id": "def456",
    "span_id": "span2",
    "operation": "database_query",
    "duration_ms": 67.8
  }
]
```

**Response:**
```json
{
  "success": true,
  "telemetry_ids": ["tel_790", "tel_791"],
  "collected_count": 2,
  "message": "Telemetry batch collected successfully",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### Get Telemetry Correlations
```http
GET /telemetry/correlations?limit=50&rule_id=rule123
```

**Response:**
```json
{
  "success": true,
  "correlations": [
    {
      "correlation_id": "corr_123",
      "rule_id": "rule123",
      "matched_spans": ["span1", "span2"],
      "correlation_strength": 0.85,
      "timestamp": "2024-01-01T12:00:00Z"
    }
  ],
  "count": 1,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### Get Telemetry Analysis
```http
GET /telemetry/analysis?limit=50&severity=high
```

**Response:**
```json
{
  "success": true,
  "analysis_results": [
    {
      "pattern_id": "pattern_123",
      "pattern_type": "anomaly",
      "severity": "high",
      "description": "Unusual spike in response times",
      "affected_services": ["user-service", "auth-service"],
      "confidence": 0.92,
      "timestamp": "2024-01-01T12:00:00Z"
    }
  ],
  "count": 1,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Backend API (Django) - Port 8000

### Base URL
- Development: `http://localhost:8000`
- Production: `https://your-domain.com/backend`

### Authentication

Django uses session-based authentication and JWT tokens:

```http
# Session authentication
Cookie: sessionid=<session-id>

# JWT authentication
Authorization: Bearer <jwt-token>
```

### Core Endpoints

#### User Management
```http
GET /api/users/
POST /api/users/
GET /api/users/{id}/
PUT /api/users/{id}/
DELETE /api/users/{id}/
```

#### Authentication
```http
POST /api/auth/login/
POST /api/auth/logout/
POST /api/auth/refresh/
GET /api/auth/user/
```

#### OAuth Integration
```http
GET /api/oauth/providers/
POST /api/oauth/authorize/{provider}/
POST /api/oauth/callback/{provider}/
```

### Analytics Endpoints

#### Analytics Data
```http
GET /api/analytics/data/
POST /api/analytics/data/
GET /api/analytics/data/{id}/
PUT /api/analytics/data/{id}/
DELETE /api/analytics/data/{id}/
```

**Example Response:**
```json
{
  "id": 123,
  "name": "CPU Usage Analytics",
  "description": "Daily CPU usage report",
  "data": {
    "average_cpu": 65.2,
    "peak_cpu": 89.1,
    "samples": 1440
  },
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

#### Analytics Queries
```http
GET /api/analytics/queries/
POST /api/analytics/queries/
GET /api/analytics/queries/{id}/execute/
```

### Metrics Endpoints

#### Application Metrics
```http
GET /api/metrics/application/
POST /api/metrics/application/
GET /api/metrics/application/{id}/
```

#### Network Metrics
```http
GET /api/metrics/network/
POST /api/metrics/network/
GET /api/metrics/network/{id}/
```

#### Security Metrics
```http
GET /api/metrics/security/
POST /api/metrics/security/
GET /api/metrics/security/{id}/
```

### Data Ingestion Endpoints

#### Ingest Metrics
```http
POST /api/ingest/metrics/
Content-Type: application/json
```

**Request Body:**
```json
{
  "source": "application_name",
  "metrics": [
    {
      "metric_name": "cpu_usage",
      "value": 75.5,
      "unit": "percent",
      "timestamp": "2024-01-01T12:00:00Z",
      "tags": {
        "host": "server1",
        "env": "production"
      }
    }
  ]
}
```

#### Ingest Logs
```http
POST /api/ingest/logs/
Content-Type: application/json
```

**Request Body:**
```json
{
  "source": "application_name",
  "logs": [
    {
      "level": "ERROR",
      "message": "Database connection failed",
      "timestamp": "2024-01-01T12:00:00Z",
      "context": {
        "user_id": "123",
        "request_id": "abc"
      }
    }
  ]
}
```

#### Ingest Telemetry
```http
POST /api/ingest/telemetry/
Content-Type: application/json
```

**Request Body:**
```json
{
  "source": "service_name",
  "telemetry": [
    {
      "trace_id": "abc123",
      "span_id": "def456",
      "operation": "database_query",
      "duration_ms": 150,
      "timestamp": "2024-01-01T12:00:00Z",
      "attributes": {
        "query": "SELECT * FROM users"
      }
    }
  ]
}
```

#### Bulk Ingestion
```http
POST /api/ingest/bulk/
Content-Type: application/json
```

**Request Body:**
```json
{
  "source": "application_name",
  "data": [
    {
      "data_type": "metrics",
      "metric_name": "cpu_usage",
      "value": 75.5
    },
    {
      "data_type": "log",
      "level": "ERROR",
      "message": "Error occurred"
    }
  ]
}
```

### Notification Endpoints

#### Notification Channels
```http
GET /api/notifications/channels/
POST /api/notifications/channels/
GET /api/notifications/channels/{id}/
PUT /api/notifications/channels/{id}/
DELETE /api/notifications/channels/{id}/
```

#### Alerts
```http
GET /api/notifications/alerts/
POST /api/notifications/alerts/
GET /api/notifications/alerts/{id}/
PUT /api/notifications/alerts/{id}/
DELETE /api/notifications/alerts/{id}/
```

#### Alert Rules
```http
GET /api/notifications/rules/
POST /api/notifications/rules/
GET /api/notifications/rules/{id}/
PUT /api/notifications/rules/{id}/
DELETE /api/notifications/rules/{id}/
```

### Dashboard Template Endpoints

#### Dashboard Templates
```http
GET /api/dashboards/templates/
POST /api/dashboards/templates/
GET /api/dashboards/templates/{id}/
PUT /api/dashboards/templates/{id}/
DELETE /api/dashboards/templates/{id}/
```

#### User Dashboards
```http
GET /api/dashboards/
POST /api/dashboards/
GET /api/dashboards/{id}/
PUT /api/dashboards/{id}/
DELETE /api/dashboards/{id}/
```

## Error Handling

### HTTP Status Codes

- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation errors
- `500 Internal Server Error`: Server error

### Error Response Format

```json
{
  "error": "Validation failed",
  "status_code": 422,
  "details": {
    "field_errors": {
      "email": ["This field is required"],
      "password": ["Password must be at least 8 characters"]
    }
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req_123"
}
```

## Rate Limiting

### Default Limits

- **Anonymous users**: 100 requests per hour
- **Authenticated users**: 1000 requests per hour
- **Data ingestion**: 10000 requests per hour

### Rate Limit Headers

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## Pagination

### Query Parameters

- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)
- `ordering`: Sort field (prefix with `-` for descending)

### Response Format

```json
{
  "count": 150,
  "next": "http://localhost:8000/api/users/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "username": "user1"
    }
  ]
}
```

## Filtering and Search

### Query Parameters

- `search`: Full-text search
- `{field}`: Exact match filter
- `{field}__contains`: Contains filter
- `{field}__gte`: Greater than or equal
- `{field}__lte`: Less than or equal
- `{field}__in`: In list filter

### Examples

```http
GET /api/metrics/application/?search=cpu
GET /api/metrics/application/?value__gte=50
GET /api/metrics/application/?timestamp__gte=2024-01-01T00:00:00Z
GET /api/metrics/application/?source__in=server1,server2
```

## WebSocket Connections

### Real-time Updates

Connect to WebSocket endpoints for real-time data:

```javascript
// Connect to real-time metrics
const ws = new WebSocket('ws://localhost:8400/ws/metrics');

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Real-time metric:', data);
};

// Subscribe to specific channels
ws.send(JSON.stringify({
  action: 'subscribe',
  channel: 'cpu_metrics'
}));
```

### Available Channels

- `metrics`: Real-time metrics updates
- `alerts`: Alert notifications
- `logs`: Log stream
- `telemetry`: Telemetry data
- `system_health`: System health updates

## SDK and Client Libraries

### Python Client

```python
from observer_eye_client import ObserverEyeClient

client = ObserverEyeClient(
    base_url='http://localhost:8400',
    api_key='your-api-key'
)

# Send metrics
client.metrics.send({
    'name': 'cpu_usage',
    'value': 75.5,
    'timestamp': '2024-01-01T12:00:00Z'
})

# Query analytics
results = client.analytics.query({
    'metric': 'cpu_usage',
    'start_time': '2024-01-01T00:00:00Z',
    'end_time': '2024-01-01T23:59:59Z'
})
```

### JavaScript Client

```javascript
import { ObserverEyeClient } from '@observer-eye/client';

const client = new ObserverEyeClient({
  baseUrl: 'http://localhost:8400',
  apiKey: 'your-api-key'
});

// Send telemetry
await client.telemetry.send({
  traceId: 'abc123',
  spanId: 'def456',
  operation: 'api_call',
  duration: 45.2
});

// Get real-time updates
client.realtime.subscribe('metrics', (data) => {
  console.log('New metric:', data);
});
```

## API Versioning

The API uses URL versioning:

- `v1`: Current stable version
- `v2`: Next version (beta)

Example:
```http
GET /api/v1/metrics/application/
GET /api/v2/metrics/application/
```

## OpenAPI Documentation

Interactive API documentation is available at:

- **FastAPI**: `http://localhost:8400/docs` (Swagger UI)
- **FastAPI**: `http://localhost:8400/redoc` (ReDoc)
- **Django**: `http://localhost:8000/api/schema/` (OpenAPI schema)

For more detailed examples and integration guides, see the [Configuration Guide](configuration.md).