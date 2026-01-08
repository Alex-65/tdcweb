# Health Check API

Endpoints for monitoring application health and connectivity.

## Overview

The health check endpoints are used by load balancers, monitoring systems, and developers to verify the application is running correctly.

## Endpoints

### GET /api/v1/health

Basic application health check.

**Authentication:** None required

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "status": "ok",
    "version": "0.1.0",
    "timestamp": "2025-01-08T12:00:00.000000+00:00"
  }
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| status | string | Always "ok" if responding |
| version | string | Application version |
| timestamp | string | ISO 8601 timestamp (UTC) |

---

### GET /api/v1/health/db

Database connectivity health check.

**Authentication:** None required

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "status": "ok",
    "database": "connected",
    "timestamp": "2025-01-08T12:00:00.000000+00:00"
  }
}
```

**Response (503 Service Unavailable):**
```json
{
  "success": false,
  "error": "Database connection failed"
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| status | string | "ok" if database is connected |
| database | string | "connected" or connection status |
| timestamp | string | ISO 8601 timestamp (UTC) |

---

### GET /api/v1/health/full

Comprehensive health check including all system components.

**Authentication:** None required

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "status": "ok",
    "version": "0.1.0",
    "components": {
      "database": "ok"
    },
    "timestamp": "2025-01-08T12:00:00.000000+00:00"
  }
}
```

**Response (200 OK - Degraded):**
```json
{
  "success": true,
  "data": {
    "status": "degraded",
    "version": "0.1.0",
    "components": {
      "database": "ok",
      "redis": "error"
    },
    "timestamp": "2025-01-08T12:00:00.000000+00:00"
  }
}
```

**Status Values:**

| Status | Description |
|--------|-------------|
| ok | All components healthy |
| degraded | Some components unhealthy |

**Component Values:**

| Value | Description |
|-------|-------------|
| ok | Component is healthy |
| error | Component is unhealthy |

## Usage Examples

### cURL

```bash
# Basic health check
curl http://localhost:9500/api/v1/health

# Database health check
curl http://localhost:9500/api/v1/health/db

# Full system health
curl http://localhost:9500/api/v1/health/full
```

### Python

```python
import requests

response = requests.get('http://localhost:9500/api/v1/health')
if response.status_code == 200:
    data = response.json()
    print(f"Status: {data['data']['status']}")
    print(f"Version: {data['data']['version']}")
```

### JavaScript

```javascript
fetch('http://localhost:9500/api/v1/health')
  .then(res => res.json())
  .then(data => {
    console.log('Status:', data.data.status);
    console.log('Version:', data.data.version);
  });
```

## Load Balancer Configuration

### Nginx

```nginx
upstream backend {
    server localhost:9500;
}

server {
    location /health {
        proxy_pass http://backend/api/v1/health;
        proxy_connect_timeout 5s;
        proxy_read_timeout 5s;
    }
}
```

### AWS ALB

Configure health check with:
- Path: `/api/v1/health`
- Port: `9500`
- Protocol: `HTTP`
- Healthy threshold: `2`
- Unhealthy threshold: `3`
- Timeout: `5` seconds
- Interval: `30` seconds

## Implementation

**Source:** `backend/app/routes/api/health.py`

The health check endpoints are implemented using the standard response format defined in `backend/app/utils/responses.py`.
