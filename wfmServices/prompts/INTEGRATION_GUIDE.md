# WFM Services + wfmApp Integration Guide

This guide provides comprehensive instructions for integrating the WFM backend services with the wfmApp frontend application.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   wfmApp       │    │   API Gateway   │    │   Backend      │
│   (Frontend)   │◄──►│   (Port 8000)   │◄──►│   Services     │
│   Port 3000    │    │                 │    │   Ports 8001-6 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Online DBs    │
                       │ MongoDB + Redis │
                       └─────────────────┘
```

## 🚀 Quick Start Options

### Option 1: Python Script (Recommended for Development)
```bash
# Start all services with integration
python3 start_integrated_services.py
```

### Option 2: Docker Compose
```bash
# Start all services in containers
docker-compose -f docker-compose.integrated.yml up -d
```

### Option 3: Manual Startup
```bash
# Start services individually
cd wfmServices
python3 api_gateway/main.py &
python3 auth_service/main.py &
python3 config_service/main.py &
python3 rules_service/main.py &
python3 scheduler_service/main.py &
python3 issue_service/main.py &
python3 analytics_service/main.py &

# Start frontend
cd wfmApp
npm run dev
```

## 📋 Prerequisites

### Backend (wfmServices)
- Python 3.8+
- Required packages: `pip install -r wfmServices/requirements.txt`
- Online database access (MongoDB Atlas + Redis Cloud)

### Frontend (wfmApp)
- Node.js 18+
- npm or yarn
- Required packages: `npm install` in wfmApp directory

## 🔧 Configuration

### Backend Environment
The backend services use `wfmServices/env.online` with:
- MongoDB Atlas connection string
- Redis Cloud connection details
- JWT secret keys
- Service configuration

### Frontend Environment
The frontend uses `wfmApp/.env.local` with:
- Backend service URLs
- API endpoints
- Development configuration

## 📡 Service Endpoints

### API Gateway (Port 8000)
- **Health**: `GET /health`
- **Services Health**: `GET /health/services`
- **Authentication**: `POST /auth/login`, `POST /auth/verify`
- **Users**: `GET/POST/PUT/DELETE /users/*`
- **Configs**: `GET/POST/PUT/DELETE /configs/*`
- **Rules**: `GET/POST/PUT/DELETE /rules/*`
- **Jobs**: `GET/POST/PUT/DELETE /jobs/*`
- **Issues**: `GET/POST/PUT/DELETE /issues/*`
- **Reports**: `GET /reports/*`
- **Metrics**: `GET /metrics/*`

### Individual Services
- **Auth Service**: Port 8001
- **Config Service**: Port 8002
- **Rules Service**: Port 8003
- **Scheduler Service**: Port 8004
- **Issue Service**: Port 8005
- **Analytics Service**: Port 8006

## 🔐 Authentication Flow

1. **Login**: `POST /auth/login` with username, password, tenant_id
2. **Token**: Receive JWT access token
3. **Authorization**: Include `Authorization: Bearer <token>` header
4. **Verification**: `POST /auth/verify` to validate token

### Test Credentials
- **Username**: `testuser`
- **Password**: `TestPassword123!`
- **Tenant ID**: `6899f993b9032cd7d152b90c`

## 🧪 Testing Integration

### 1. Health Checks
```bash
# Backend health
curl http://localhost:8000/health
curl http://localhost:8000/health/services

# Individual service health
curl http://localhost:8001/health
curl http://localhost:8002/health
# ... etc
```

### 2. Authentication Test
```bash
# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"TestPassword123!","tenant_id":"6899f993b9032cd7d152b90c"}'

# Use token from response
TOKEN="your_token_here"
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/users
```

### 3. Frontend Test
```bash
# Start frontend
cd wfmApp
npm run dev

# Open browser to http://localhost:3000
```

### 4. Comprehensive Testing
```bash
# Run full endpoint test suite
python3 test_online_endpoints.py
```

## 🔄 Development Workflow

### 1. Start Services
```bash
python3 start_integrated_services.py
```

### 2. Start Frontend
```bash
cd wfmApp
npm run dev
```

### 3. Make Changes
- Backend: Edit files in `wfmServices/`
- Frontend: Edit files in `wfmApp/`
- Services auto-reload on changes

### 4. Test Changes
- API endpoints: Use curl or Postman
- Frontend: Browser at http://localhost:3000
- Integration: Test full user flows

## 🐛 Troubleshooting

### Common Issues

#### Backend Services Won't Start
- Check Python dependencies: `pip install -r wfmServices/requirements.txt`
- Verify database connectivity: `python3 test_db_connection.py`
- Check port availability: `lsof -i :8000-8006`

#### Frontend Won't Start
- Check Node.js version: `node --version` (should be 18+)
- Install dependencies: `npm install`
- Check port 3000 availability

#### Database Connection Issues
- Verify MongoDB Atlas credentials in `env.online`
- Check Redis Cloud connectivity
- Ensure IP whitelisting in MongoDB Atlas

#### Authentication Failures
- Verify JWT secret in `env.online`
- Check user credentials in database
- Ensure proper token format in requests

### Debug Mode
Set `DEBUG=true` in environment files for detailed logging.

### Logs
Check service logs in `wfmServices/logs/` directory.

## 📊 Monitoring

### Service Status
- **Health Endpoints**: `/health` on each service
- **Aggregated Health**: `/health/services` on API Gateway
- **Real-time Monitoring**: Service manager script output

### Performance Metrics
- **Response Times**: Available via health endpoints
- **Error Rates**: Check service logs
- **Database Performance**: MongoDB Atlas metrics

## 🚀 Production Deployment

### Docker Deployment
```bash
# Build and start all services
docker-compose -f docker-compose.integrated.yml up -d --build

# View logs
docker-compose -f docker-compose.integrated.yml logs -f

# Stop services
docker-compose -f docker-compose.integrated.yml down
```

### Environment Variables
Update environment files for production:
- Database connection strings
- JWT secrets
- Service URLs
- Logging levels

### Scaling
- **Backend**: Scale individual services as needed
- **Frontend**: Use load balancer for multiple instances
- **Database**: MongoDB Atlas auto-scaling

## 📝 API Documentation

### Swagger/OpenAPI
- **API Gateway**: http://localhost:8000/docs
- **Individual Services**: http://localhost:8001/docs, etc.

### Postman Collection
Import the provided Postman collection for easy API testing.

## 🔗 Useful Links

- **Frontend**: http://localhost:3000
- **API Gateway**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Services Health**: http://localhost:8000/health/services

## 📞 Support

For integration issues:
1. Check service logs
2. Verify configuration
3. Test individual components
4. Review this guide
5. Check troubleshooting section

## 🎯 Next Steps

1. **Start Integration**: Run `python3 start_integrated_services.py`
2. **Test Backend**: Verify all services are healthy
3. **Start Frontend**: Run `npm run dev` in wfmApp
4. **Test Integration**: Verify frontend-backend communication
5. **Run Tests**: Execute comprehensive test suite
6. **Develop**: Start building your application features

---

**Happy Coding! 🚀**
