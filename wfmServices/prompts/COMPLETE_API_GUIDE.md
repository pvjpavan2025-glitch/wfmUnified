# 🚀 WFM System Complete API Guide

## 📋 Overview

This document provides a comprehensive guide to all WFM system endpoints, sample payloads, and the recommended execution sequence. The system consists of 6 microservices with full API coverage.

## 🏗️ Service Architecture

| Service | Port | Status | Description |
|---------|------|--------|-------------|
| Auth Service | 8000 | ✅ Ready | Authentication & Authorization |
| Config Service | 8002 | ✅ Ready | Configuration Management |
| Rules Service | 8001 | ✅ Ready | Rules Engine |
| Scheduler Service | 8005 | ✅ Ready | Job Scheduling |
| Issue Service | 8003 | ✅ Ready | Issue Management |
| Analytics Service | 8004 | ✅ Ready | Analytics & Reporting |

## 🔄 Execution Sequence

### Phase 1: System Setup
1. **Authentication** → 2. **Configuration** → 3. **Rules Setup**

### Phase 2: Core Operations  
4. **Job Scheduling** → 5. **Issue Management** → 6. **Analytics**

---

## 1. 🔐 Authentication Service (Port 8000)

### 1.1 User Login
**Endpoint:** `POST /auth/login`
**Headers:** `Content-Type: application/json`

```json
{
  "username": "admin",
  "password": "admin123",
  "tenant_id": "default"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 1800,
  "user": {
    "id": "user_123",
    "username": "admin",
    "email": "admin@wfm.local",
    "first_name": "Admin",
    "last_name": "User",
    "status": "ACTIVE",
    "role_ids": ["admin_role"],
    "permissions": ["read", "write", "admin"]
  }
}
```

### 1.2 Create User
**Endpoint:** `POST /users`
**Headers:** 
- `Content-Type: application/json`
- `Authorization: Bearer {token}`
- `x-tenant-id: default`

```json
{
  "username": "analyst1",
  "email": "analyst1@company.com",
  "password": "secure_password",
  "first_name": "John",
  "last_name": "Doe",
  "tenant_id": "default",
  "role_ids": ["analyst_role"],
  "status": "ACTIVE"
}
```

### 1.3 Get User
**Endpoint:** `GET /users/{user_id}`
**Headers:** 
- `Authorization: Bearer {token}`
- `x-tenant-id: default`

### 1.4 List Users
**Endpoint:** `GET /users?skip=0&limit=100`
**Headers:** 
- `Authorization: Bearer {token}`
- `x-tenant-id: default`

### 1.5 Create Role
**Endpoint:** `POST /roles`
**Headers:** 
- `Content-Type: application/json`
- `Authorization: Bearer {token}`
- `x-tenant-id: default`

```json
{
  "name": "Senior Analyst",
  "description": "Senior level analyst with advanced permissions",
  "tenant_id": "default",
  "permission_ids": ["read", "write", "analyze"],
  "status": "ACTIVE"
}
```

---

## 2. ⚙️ Configuration Service (Port 8002)

### 2.1 Create Configuration
**Endpoint:** `POST /configs`
**Headers:** 
- `Content-Type: application/json`
- `Authorization: Bearer {token}`
- `x-tenant-id: default`

```json
{
  "key": "scheduler_settings",
  "value": {
    "max_jobs_per_analyst": 5,
    "working_hours": {
      "start": "09:00",
      "end": "17:00"
    },
    "priority_weights": {
      "critical": 10,
      "high": 7,
      "medium": 4,
      "low": 1
    }
  },
  "tenant_id": "default",
  "description": "Scheduler configuration settings",
  "category": "scheduling"
}
```

### 2.2 Get Configuration
**Endpoint:** `GET /configs/{config_id}`
**Headers:** 
- `Authorization: Bearer {token}`
- `x-tenant-id: default`

### 2.3 Get Configuration by Key
**Endpoint:** `GET /configs/key/{key}`
**Headers:** 
- `Authorization: Bearer {token}`
- `x-tenant-id: default`

### 2.4 List Configurations
**Endpoint:** `GET /configs?skip=0&limit=100&category=scheduling`
**Headers:** 
- `Authorization: Bearer {token}`
- `x-tenant-id: default`

### 2.5 Update Configuration
**Endpoint:** `PUT /configs/{config_id}`
**Headers:** 
- `Content-Type: application/json`
- `Authorization: Bearer {token}`
- `x-tenant-id: default`

```json
{
  "value": {
    "max_jobs_per_analyst": 8,
    "working_hours": {
      "start": "08:00",
      "end": "18:00"
    }
  },
  "description": "Updated scheduler settings"
}
```

---

## 3. 🎯 Rules Service (Port 8001)

### 3.1 Create Rule
**Endpoint:** `POST /rules`
**Headers:** 
- `Content-Type: application/json`
- `Authorization: Bearer {token}`
- `x-tenant-id: default`

```json
{
  "name": "High Priority Job Assignment",
  "description": "Automatically assign high priority jobs to senior analysts",
  "tenant_id": "default",
  "tag_name": "scheduling",
  "sequence": 1,
  "order_id": "order_123",
  "conditions": {
    "priority": {"eq": "HIGH"},
    "job_type": {"in": ["critical", "urgent"]},
    "analyst_experience": {"gte": 3}
  },
  "actions": [
    {
      "type": "assign_to_senior",
      "parameters": {
        "min_experience": 3,
        "preferred_skills": ["system_analysis", "performance_tuning"]
      }
    },
    {
      "type": "send_notification",
      "parameters": {
        "recipients": ["senior_analysts"],
        "message": "High priority job assigned"
      }
    }
  ],
  "status": "ACTIVE"
}
```

### 3.2 Get Rule
**Endpoint:** `GET /rules/{rule_id}`
**Headers:** 
- `Authorization: Bearer {token}`
- `x-tenant-id: default`

### 3.3 List Rules
**Endpoint:** `GET /rules?skip=0&limit=100&category=scheduling`
**Headers:** 
- `Authorization: Bearer {token}`
- `x-tenant-id: default`

### 3.4 Evaluate Rule
**Endpoint:** `POST /rules/{rule_id}/evaluate`
**Headers:** 
- `Content-Type: application/json`
- `Authorization: Bearer {token}`
- `x-tenant-id: default`

```json
{
  "data": {
    "priority": "HIGH",
    "job_type": "critical",
    "analyst_experience": 5,
    "required_skills": ["system_analysis"],
    "deadline": "2025-08-06T10:00:00Z"
  },
  "tenant_id": "default"
}
```

**Response:**
```json
{
  "rule_id": "rule_123",
  "evaluated": true,
  "conditions_met": true,
  "actions_executed": [
    {
      "type": "assign_to_senior",
      "result": "analyst_456 assigned",
      "success": true
    },
    {
      "type": "send_notification",
      "result": "Notification sent",
      "success": true
    }
  ],
  "execution_time": "2025-08-05T05:45:00Z"
}
```

### 3.5 Update Rule
**Endpoint:** `PUT /rules/{rule_id}`
**Headers:** 
- `Content-Type: application/json`
- `Authorization: Bearer {token}`
- `x-tenant-id: default`

```json
{
  "description": "Updated rule description",
  "conditions": {
    "priority": {"eq": "HIGH"},
    "job_type": {"in": ["critical", "urgent", "emergency"]}
  },
  "status": "ACTIVE"
}
```

---

## 4. 📅 Scheduler Service (Port 8005)

### 4.1 Create Job
**Endpoint:** `POST /jobs`
**Headers:** 
- `Content-Type: application/json`
- `Authorization: Bearer {token}`
- `x-tenant-id: default`

```json
{
  "title": "Critical System Performance Analysis",
  "description": "Analyze and optimize critical system performance issues",
  "tenant_id": "default",
  "priority": "HIGH",
  "estimated_duration": 120,
  "required_skills": ["system_analysis", "performance_tuning", "troubleshooting"],
  "deadline": "2025-08-06T10:00:00Z",
  "client_id": "client_123",
  "job_type": "critical",
  "complexity": "HIGH",
  "location": "remote",
  "dependencies": ["job_456", "job_789"]
}
```

### 4.2 Get Job
**Endpoint:** `GET /jobs/{job_id}`
**Headers:** 
- `Authorization: Bearer {token}`
- `x-tenant-id: default`

### 4.3 List Jobs
**Endpoint:** `GET /jobs?skip=0&limit=100&priority=HIGH&status=OPEN`
**Headers:** 
- `Authorization: Bearer {token}`
- `x-tenant-id: default`

### 4.4 Schedule Job
**Endpoint:** `POST /jobs/{job_id}/schedule`
**Headers:** 
- `Content-Type: application/json`
- `Authorization: Bearer {token}`
- `x-tenant-id: default`

```json
{
  "scheduling_strategy": "skill_based",
  "preferred_analyst_id": "analyst_123",
  "start_time": "2025-08-05T09:00:00Z",
  "end_time": "2025-08-05T11:00:00Z",
  "priority_override": false
}
```

**Response:**
```json
{
  "job_id": "job_123",
  "scheduled": true,
  "assigned_analyst": {
    "id": "analyst_456",
    "name": "John Doe",
    "skills": ["system_analysis", "performance_tuning"],
    "experience": 5,
    "current_workload": 3
  },
  "schedule": {
    "start_time": "2025-08-05T09:00:00Z",
    "end_time": "2025-08-05T11:00:00Z",
    "estimated_completion": "2025-08-05T11:00:00Z"
  },
  "confidence_score": 0.95,
  "reasoning": "Analyst has required skills and availability"
}
```

### 4.5 Create Analyst
**Endpoint:** `POST /analysts`
**Headers:** 
- `Content-Type: application/json`
- `Authorization: Bearer {token}`
- `x-tenant-id: default`

```json
{
  "name": "Jane Smith",
  "email": "jane.smith@company.com",
  "tenant_id": "default",
  "skills": ["system_analysis", "performance_tuning", "troubleshooting"],
  "experience_years": 5,
  "max_jobs": 8,
  "availability": {
    "monday": {"start": "09:00", "end": "17:00"},
    "tuesday": {"start": "09:00", "end": "17:00"},
    "wednesday": {"start": "09:00", "end": "17:00"},
    "thursday": {"start": "09:00", "end": "17:00"},
    "friday": {"start": "09:00", "end": "17:00"}
  },
  "preferences": {
    "preferred_job_types": ["critical", "high"],
    "max_travel_distance": 50,
    "remote_work": true
  },
  "status": "ACTIVE"
}
```

### 4.6 Get Analyst
**Endpoint:** `GET /analysts/{analyst_id}`
**Headers:** 
- `Authorization: Bearer {token}`
- `x-tenant-id: default`

### 4.7 List Analysts
**Endpoint:** `GET /analysts?skip=0&limit=100&status=ACTIVE`
**Headers:** 
- `Authorization: Bearer {token}`
- `x-tenant-id: default`

---

## 5. 🐛 Issue Service (Port 8003)

### 5.1 Create Issue
**Endpoint:** `POST /issues`
**Headers:** 
- `Content-Type: application/json`
- `Authorization: Bearer {token}`
- `x-tenant-id: default`

```json
{
  "title": "System Performance Degradation",
  "description": "Users reporting slow response times during peak hours",
  "tenant_id": "default",
  "priority": "high",
  "category": "technical",
  "assigned_to": "analyst_123",
  "reported_by": "user_456",
  "job_id": "job_789",
  "severity": "medium",
  "impact": "user_experience",
  "environment": "production",
  "tags": ["performance", "response_time", "peak_hours"]
}
```

### 5.2 Get Issue
**Endpoint:** `GET /issues/{issue_id}`
**Headers:** 
- `Authorization: Bearer {token}`
- `x-tenant-id: default`

### 5.3 List Issues
**Endpoint:** `GET /issues?skip=0&limit=100&priority=high&status=open`
**Headers:** 
- `Authorization: Bearer {token}`
- `x-tenant-id: default`

### 5.4 Update Issue
**Endpoint:** `PUT /issues/{issue_id}`
**Headers:** 
- `Content-Type: application/json`
- `Authorization: Bearer {token}`
- `x-tenant-id: default`

```json
{
  "status": "in_progress",
  "assigned_to": "analyst_456",
  "priority": "critical",
  "description": "Updated description with additional context"
}
```

### 5.5 Add Comment
**Endpoint:** `POST /issues/{issue_id}/comments`
**Headers:** 
- `Content-Type: application/json`
- `Authorization: Bearer {token}`
- `x-tenant-id: default`

```json
{
  "content": "Investigating the performance issue. Found high CPU usage during peak hours.",
  "tenant_id": "default",
  "is_internal": false,
  "attachments": []
}
```

### 5.6 Escalate Issue
**Endpoint:** `POST /issues/{issue_id}/escalate`
**Headers:** 
- `Content-Type: application/json`
- `Authorization: Bearer {token}`
- `x-tenant-id: default`

```json
{
  "reason": "Issue not resolved within SLA",
  "escalated_to": "senior_analyst_123",
  "priority": "critical",
  "tenant_id": "default"
}
```

### 5.7 Get Issues by Job
**Endpoint:** `GET /issues/job/{job_id}`
**Headers:** 
- `Authorization: Bearer {token}`
- `x-tenant-id: default`

---

## 6. 📊 Analytics Service (Port 8004)

### 6.1 Generate Performance Metrics
**Endpoint:** `GET /metrics/performance`
**Headers:** 
- `Authorization: Bearer {token}`
- `x-tenant-id: default`

**Query Parameters:**
- `time_range`: `last_7_days`, `last_30_days`, `last_90_days`
- `group_by`: `analyst`, `job_type`, `priority`

### 6.2 Get Dashboard Data
**Endpoint:** `GET /dashboard`
**Headers:** 
- `Authorization: Bearer {token}`
- `x-tenant-id: default`

**Query Parameters:**
- `widgets`: `performance`, `workload`, `issues`, `sla`

### 6.3 Generate Report
**Endpoint:** `POST /reports/generate`
**Headers:** 
- `Content-Type: application/json`
- `Authorization: Bearer {token}`
- `x-tenant-id: default`

```json
{
  "report_type": "performance_analysis",
  "parameters": {
    "time_range": "last_30_days",
    "analysts": ["analyst_123", "analyst_456"],
    "metrics": ["response_time", "throughput", "error_rate"],
    "group_by": "analyst",
    "format": "pdf"
  },
  "tenant_id": "default"
}
```

### 6.4 Get Workload Metrics
**Endpoint:** `GET /metrics/workload`
**Headers:** 
- `Authorization: Bearer {token}`
- `x-tenant-id: default`

### 6.5 Get Issue Metrics
**Endpoint:** `GET /metrics/issues`
**Headers:** 
- `Authorization: Bearer {token}`
- `x-tenant-id: default`

### 6.6 Get Trends
**Endpoint:** `GET /trends/{metric_name}`
**Headers:** 
- `Authorization: Bearer {token}`
- `x-tenant-id: default`

**Query Parameters:**
- `time_range`: `last_7_days`, `last_30_days`
- `granularity`: `hourly`, `daily`, `weekly`

---

## 🔄 Complete Workflow Example

### Step 1: Authentication
```bash
# Login to get token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123",
    "tenant_id": "default"
  }'
```

### Step 2: Configuration Setup
```bash
# Create scheduler configuration
curl -X POST http://localhost:8002/configs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {token}" \
  -H "x-tenant-id: default" \
  -d '{
    "key": "scheduler_settings",
    "value": {
      "max_jobs_per_analyst": 5,
      "working_hours": {"start": "09:00", "end": "17:00"}
    },
    "tenant_id": "default",
    "description": "Scheduler configuration"
  }'
```

### Step 3: Rules Setup
```bash
# Create scheduling rule
curl -X POST http://localhost:8001/rules \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {token}" \
  -H "x-tenant-id: default" \
  -d '{
    "name": "High Priority Assignment",
    "description": "Assign high priority jobs to senior analysts",
    "tenant_id": "default",
    "tag_name": "scheduling",
    "sequence": 1,
    "order_id": "order_123",
    "conditions": {"priority": {"eq": "HIGH"}},
    "actions": [{"type": "assign_to_senior"}],
    "status": "ACTIVE"
  }'
```

### Step 4: Job Creation and Scheduling
```bash
# Create job
curl -X POST http://localhost:8005/jobs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {token}" \
  -H "x-tenant-id: default" \
  -d '{
    "title": "Critical System Analysis",
    "description": "Analyze critical system issues",
    "tenant_id": "default",
    "priority": "HIGH",
    "estimated_duration": 120,
    "required_skills": ["system_analysis"],
    "deadline": "2025-08-06T10:00:00Z"
  }'

# Schedule the job
curl -X POST http://localhost:8005/jobs/{job_id}/schedule \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {token}" \
  -H "x-tenant-id: default" \
  -d '{
    "scheduling_strategy": "skill_based"
  }'
```

### Step 5: Issue Management
```bash
# Create issue
curl -X POST http://localhost:8003/issues \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {token}" \
  -H "x-tenant-id: default" \
  -d '{
    "title": "System Performance Issue",
    "description": "Performance degradation detected",
    "tenant_id": "default",
    "priority": "high",
    "category": "technical",
    "assigned_to": "analyst_123",
    "reported_by": "user_456",
    "job_id": "job_123"
  }'

# Add comment
curl -X POST http://localhost:8003/issues/{issue_id}/comments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {token}" \
  -H "x-tenant-id: default" \
  -d '{
    "content": "Investigating the issue",
    "tenant_id": "default"
  }'
```

### Step 6: Analytics and Reporting
```bash
# Get performance metrics
curl -X GET "http://localhost:8004/metrics/performance?time_range=last_30_days" \
  -H "Authorization: Bearer {token}" \
  -H "x-tenant-id: default"

# Generate report
curl -X POST http://localhost:8004/reports/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {token}" \
  -H "x-tenant-id: default" \
  -d '{
    "report_type": "performance_analysis",
    "parameters": {
      "time_range": "last_30_days",
      "metrics": ["response_time", "throughput"]
    },
    "tenant_id": "default"
  }'
```

---

## 5. 🧾 Order Service (Port 8008)

### 5.1 Create Order (READY)
Endpoint: `POST /orders`
Headers:
- `Content-Type: application/json`
- `Authorization: Bearer {token}`

Request:
```json
{
  "external_id": "OSM-12345",
  "source": "OSM",
  "payload": { "...": "original order payload" },
  "status": "ready"
}
```

Response: Order object with id and status.

### 5.2 List READY Orders
Endpoint: `GET /orders/ready`
Headers: `Authorization: Bearer {token}`

### 5.3 Update Order Status
Endpoint: `PATCH /orders/{order_id}/status?status_value={status}`
Headers: `Authorization: Bearer {token}`

---

## 6. 📊 Scheduler Reports (extended)

### 6.1 Jobs Summary by Order
Endpoint: `GET /reports/orders/{order_id}/jobs-summary`
Headers: `Authorization: Bearer {token}`

Response:
```json
{
  "order_id": "<order_id>",
  "total_jobs": 3,
  "status_counts": {"pending": 2, "scheduled": 1},
  "assignment": {"assigned": 1, "unassigned": 2},
  "jobs": [ { "id": "...", "status": "pending", "assigned_analyst": null, "order_id": "<order_id>" } ]
}
```


## 📋 Error Handling

### Common HTTP Status Codes
- `200`: Success
- `201`: Created
- `400`: Bad Request (validation error)
- `401`: Unauthorized (invalid token)
- `403`: Forbidden (insufficient permissions)
- `404`: Not Found
- `422`: Unprocessable Entity (data validation error)
- `500`: Internal Server Error

### Error Response Format
```json
{
  "detail": "Error message",
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2025-08-05T05:45:00Z"
}
```

---

## 🔐 Authentication

All endpoints (except login) require:
- `Authorization: Bearer {token}` header
- `x-tenant-id: {tenant_id}` header

### Token Format
```
Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 📊 Rate Limiting

- **Default**: 100 requests per minute per IP
- **Authenticated**: 1000 requests per minute per user
- **Headers**: `X-RateLimit-Remaining`, `X-RateLimit-Reset`

---

## 🚀 Production Deployment

### Environment Variables
```bash
# Database
MONGODB_URL=mongodb://admin:password@localhost:27018/
REDIS_URL=redis://localhost:6380
DATABASE_NAME=wfmv4

# Security
JWT_SECRET_KEY=your-production-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30

# Services
AUTH_SERVICE_URL=http://localhost:8000
CONFIG_SERVICE_URL=http://localhost:8002
RULES_SERVICE_URL=http://localhost:8001
SCHEDULER_SERVICE_URL=http://localhost:8005
ISSUE_SERVICE_URL=http://localhost:8003
ANALYTICS_SERVICE_URL=http://localhost:8004
```

### Health Check Endpoints
All services provide health check at `/health`:
```bash
curl http://localhost:8000/health  # Auth Service
curl http://localhost:8001/health  # Rules Service
curl http://localhost:8002/health  # Config Service
curl http://localhost:8003/health  # Issue Service
curl http://localhost:8004/health  # Analytics Service
curl http://localhost:8005/health  # Scheduler Service
```

---

## 🎯 Quick Start Commands

### 1. Start Infrastructure
```bash
docker-compose -f docker-compose.wfmv4.yml up -d
```

### 2. Start Services
```bash
# Activate environment
source wfmv4/bin/activate

# Start services (in separate terminals)
python -m auth_service.main --port 8000
python -m config_service.main --port 8002
python -m rules_service.main --port 8001
python -m scheduler_service.main --port 8005
python -m issue_service.main --port 8003
python -m analytics_service.main --port 8004
```

### 3. Test System
```bash
# Test health endpoints
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health
curl http://localhost:8005/health
```

---

## ✅ System Status

- **Infrastructure**: ✅ MongoDB & Redis running
- **Services**: ✅ All 6 microservices ready
- **Authentication**: ✅ JWT-based auth implemented
- **Multi-tenancy**: ✅ Tenant isolation working
- **API Documentation**: ✅ Complete with all endpoints
- **Error Handling**: ✅ Comprehensive error responses
- **Rate Limiting**: ✅ Implemented
- **Health Checks**: ✅ All services responding

**Status: ✅ PRODUCTION READY**

---

## 📞 Support

For API support and questions:
- Check health endpoints for service status
- Review error responses for troubleshooting
- Use the complete workflow example as reference
- All endpoints support proper authentication and authorization

**The WFM system is now fully operational with complete API coverage! 🚀** 