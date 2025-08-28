# WFM Service Online Database Testing

This document provides instructions for testing the WFM (Workforce Management) service with online MongoDB Atlas and Redis Cloud databases.

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.8+
- Required Python packages (see `requirements.txt`)
- Access to online MongoDB Atlas and Redis Cloud databases

### 2. Environment Configuration

The service is configured to use the `env.online` file which contains:
- MongoDB Atlas connection string
- Redis Cloud connection details
- JWT secret keys
- Service configuration

### 3. Database Initialization

First, initialize the online database with test data:

```bash
python init_test_data.py
```

This will create:
- Test tenant
- Test user (`testuser` / `TestPassword123!`)
- Test role (admin)
- Test configurations, rules, jobs, and issues

## 🧪 Testing All Endpoints

### Option 1: Comprehensive Test Script

Run the comprehensive endpoint tester:

```bash
python test_online_endpoints.py
```

This script tests:
- ✅ Health endpoints
- 🔐 Authentication endpoints
- 👥 User management endpoints
- ⚙️ Configuration endpoints
- 📋 Rules endpoints
- ⏰ Scheduler endpoints
- 🐛 Issue endpoints
- 📊 Analytics endpoints
- 🚫 Unauthorized access tests

### Option 2: Manual Testing

Start all services and test manually:

```bash
# Start all services
python start_services.py

# In another terminal, test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/health/services
```

## 🔧 Service Management

### Starting Services

```bash
python start_services.py
```

This starts all services:
- API Gateway (port 8000)
- Auth Service (port 8001)
- Config Service (port 8002)
- Rules Service (port 8003)
- Scheduler Service (port 8004)
- Issue Service (port 8005)
- Analytics Service (port 8006)

### Stopping Services

Press `Ctrl+C` in the service manager terminal, or kill the processes manually.

## 📊 Test Results

The comprehensive test script generates:
- Console output with real-time test results
- `test_results.json` file with detailed results
- Summary statistics (pass/fail counts, success rate)

## 🔍 Individual Service Testing

### API Gateway
```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/services
```

### Authentication
```bash
# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"TestPassword123!","tenant_id":"TENANT_ID"}'

# Verify token (use token from login response)
curl -X POST http://localhost:8000/auth/verify \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### User Management
```bash
# List users (requires auth token)
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/users

# Create user (requires auth token)
curl -X POST http://localhost:8000/users \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username":"newuser","email":"new@example.com","password":"password","first_name":"New","last_name":"User","tenant_id":"TENANT_ID"}'
```

### Configuration
```bash
# List configs (requires auth token)
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/configs

# Create config (requires auth token)
curl -X POST http://localhost:8000/configs \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"key":"test_key","value":"test_value","tenant_id":"TENANT_ID","description":"Test"}'
```

### Rules
```bash
# List rules (requires auth token)
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/rules

# Evaluate rules (requires auth token)
curl -X POST http://localhost:8000/rules/evaluate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"data":{"status":"active"}}'
```

### Scheduler
```bash
# List jobs (requires auth token)
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/jobs

# Create job (requires auth token)
curl -X POST http://localhost:8000/jobs \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"test_job","description":"Test","tenant_id":"TENANT_ID","schedule":"0 9 * * 1-5","status":"active"}'
```

### Issues
```bash
# List issues (requires auth token)
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/issues

# Create issue (requires auth token)
curl -X POST http://localhost:8000/issues \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Issue","description":"Test","tenant_id":"TENANT_ID","priority":"medium","status":"open"}'
```

### Analytics
```bash
# List reports (requires auth token)
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/reports

# Get metrics (requires auth token)
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/metrics
```

## 🐛 Troubleshooting

### Common Issues

1. **Connection Errors**
   - Verify MongoDB Atlas and Redis Cloud credentials in `env.online`
   - Check network connectivity
   - Ensure IP whitelisting in MongoDB Atlas

2. **Authentication Failures**
   - Verify JWT secret key in `env.online`
   - Check user credentials in database
   - Ensure proper token format in Authorization header

3. **Service Startup Issues**
   - Check port availability
   - Verify Python dependencies are installed
   - Check service logs for errors

### Debug Mode

Set `DEBUG=true` in `env.online` for detailed logging.

### Logs

Check individual service logs for detailed error information.

## 📈 Performance Testing

For load testing, consider using tools like:
- Apache Bench (ab)
- wrk
- Artillery
- Locust

Example:
```bash
# Test health endpoint with 1000 requests
ab -n 1000 -c 10 http://localhost:8000/health
```

## 🔒 Security Testing

The test suite includes:
- Unauthorized access tests
- Invalid token tests
- Missing authentication header tests

## 📝 Notes

- All endpoints require valid JWT tokens (except health checks)
- Tenant isolation is enforced across all services
- Database connections use connection pooling for efficiency
- Redis is used for caching and session management

## 🆘 Support

If you encounter issues:
1. Check the test results and error messages
2. Verify database connectivity
3. Check service logs
4. Ensure all dependencies are installed
5. Verify environment configuration
