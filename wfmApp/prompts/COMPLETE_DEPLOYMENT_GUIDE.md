# 🚀 Complete WFM System Deployment Guide

This guide provides comprehensive instructions for deploying the complete WFM (Workforce Management) system with online MongoDB Atlas and Redis Cloud services.

## 🎯 **System Overview**

The WFM system consists of:
- **Frontend**: Next.js 15 application with authentication and role-based access control
- **Backend**: FastAPI microservices (API Gateway, Auth Service, etc.)
- **Database**: MongoDB Atlas cloud cluster
- **Cache**: Redis Cloud service
- **Containerization**: Docker and Docker Compose

## 🌐 **Online Services Configuration**

### **MongoDB Atlas**
- **Cluster URL**: `wfmdb.cvkb04l.mongodb.net`
- **Username**: `wfmadmin`
- **Password**: `tsarolabs@12345#`
- **Database**: `wfm`
- **Connection String**: 
  ```
  mongodb+srv://wfmadmin:tsarolabs%4012345%23@wfmdb.cvkb04l.mongodb.net/?retryWrites=true&w=majority&appName=wfmDB
  ```

### **Redis Cloud**
- **Host**: `redis-15514.c56.east-us.azure.redns.redis-cloud.com`
- **Port**: `15514`
- **Username**: `default`
- **Password**: `kIdJfI3xoLxHiKFnCrkGBYffiDla8Y9h`
- **Connection String**:
  ```
  redis://default:kIdJfI3xoLxHiKFnCrkGBYffiDla8Y9h@redis-15514.c56.east-us.azure.redns.redis-cloud.com:15514
  ```

## 📋 **Prerequisites**

### **System Requirements**
- Docker and Docker Compose
- Python 3.8+
- Node.js 18+
- Git

### **Dependencies**
```bash
# Python dependencies
pip install "pymongo[srv]" redis python-dotenv dnspython requests

# Node.js dependencies
npm install
```

## 🚀 **Deployment Steps**

### **Step 1: Clone and Setup Repository**
```bash
# Clone the repository
git clone <your-repo-url>
cd wfmv4

# Checkout the feature branch
git checkout feature/auth-login-impl
```

### **Step 2: Backend Configuration**
```bash
# Navigate to backend directory
cd wfmv4

# Update environment configuration
cp env.online env.wfmv4

# Verify configuration
cat env.wfmv4 | grep -E "(MONGODB|REDIS|DATABASE)"
```

### **Step 3: Start Backend Services**
```bash
# Start all services with online configuration
./restart-with-online-mongo.sh

# Verify services are running
docker-compose ps

# Check service health
curl http://localhost:8000/health
```

### **Step 4: Frontend Configuration**
```bash
# Navigate to frontend directory
cd ../wfmApp

# Install dependencies
npm install

# Start development server
npm run dev
```

### **Step 5: Database Setup**
```bash
# Set up online MongoDB with initial data
python3 unwanted/setup-online-database.py

# Or reset existing database
python3 unwanted/clear-and-reset-database.py
```

### **Step 6: Integration Testing**
```bash
# Test complete system integration
python3 tests/test-complete-integration.py

# Expected result: 4/4 tests passed ✅
```

## 🔐 **Test Credentials**

Use these credentials to test the system:

- **Tenant ID**: `6899df7293ed4ce8e63f574d`
- **Username**: `testuser`
- **Password**: `test123`
- **Role**: `SuperAdmin`

## 📊 **Service Ports**

| Service | Port | URL | Status |
|---------|------|-----|---------|
| API Gateway | 8000 | http://localhost:8000 | ✅ |
| Auth Service | 8001 | http://localhost:8001 | ✅ |
| Config Service | 8002 | http://localhost:8002 | ✅ |
| Rules Service | 8003 | http://localhost:8003 | ✅ |
| Scheduler Service | 8004 | http://localhost:8004 | ✅ |
| Issue Service | 8005 | http://localhost:8005 | ✅ |
| Analytics Service | 8006 | http://localhost:8006 | ✅ |
| Frontend | 3001 | http://localhost:3001 | ✅ |

## 🧪 **Testing and Verification**

### **Backend Health Check**
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","service":"api-gateway"}
```

### **MongoDB Connection Test**
```bash
python3 test-online-mongo.py
# Expected: ✅ MongoDB: Connected successfully
```

### **Redis Connection Test**
```bash
cd ../wfmv4
python3 test-online-redis.py
# Expected: ✅ Redis connection successful!
```

### **Complete Integration Test**
```bash
cd ../wfmApp
python3 test-complete-integration.py
# Expected: 🎯 Overall Result: 4/4 tests passed
```

### **Frontend Login Test**
1. Open http://localhost:3001/login
2. Enter test credentials
3. Verify successful login and dashboard access

## 🔧 **Troubleshooting**

### **Common Issues**

#### **1. Backend Services Not Starting**
```bash
# Check Docker logs
docker-compose logs

# Restart services
./restart-with-online-mongo.sh
```

#### **2. MongoDB Connection Failed**
- Verify MongoDB Atlas cluster is accessible
- Check network connectivity
- Verify credentials in environment files

#### **3. Redis Connection Failed**
- Verify Redis Cloud service is running
- Check firewall/network access
- Verify credentials in environment files

#### **4. Authentication Errors**
- Check if database has test user data
- Verify tenant ID format (MongoDB ObjectId)
- Check backend logs for detailed errors

### **Debug Commands**
```bash
# Check container environment variables
docker exec wfm_api_gateway env | grep -E "(MONGODB|REDIS|DATABASE)"

# Check service logs
docker-compose logs api-gateway

# Test individual service connections
docker exec wfm_api_gateway python -c "from shared.database import db_manager; import asyncio; asyncio.run(db_manager.connect_mongodb())"
```

## 🚀 **Production Deployment**

### **Environment Variables**
Set these in your production environment:

```bash
# MongoDB
MONGODB_URL=mongodb+srv://wfmadmin:tsarolabs%4012345%23@wfmdb.cvkb04l.mongodb.net/?retryWrites=true&w=majority&appName=wfmDB
DATABASE_NAME=wfm

# Redis
REDIS_URL=redis://default:kIdJfI3xoLxHiKFnCrkGBYffiDla8Y9h@redis-15514.c56.east-us.azure.redns.redis-cloud.com:15514

# Security
JWT_SECRET_KEY=your-production-secret-key
ENVIRONMENT=production
```

### **Docker Production Build**
```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Start production services
docker-compose -f docker-compose.prod.yml up -d
```

### **SSL/TLS Configuration**
- Configure reverse proxy (nginx/traefik)
- Set up SSL certificates
- Update frontend URLs to use HTTPS

## 📈 **Monitoring and Maintenance**

### **Health Checks**
- Monitor service health endpoints
- Set up automated health checks
- Configure alerting for service failures

### **Database Maintenance**
- Regular MongoDB backups
- Monitor database performance
- Set up automated maintenance tasks

### **Log Management**
- Centralized logging (ELK stack)
- Log rotation and retention
- Error monitoring and alerting

## 🔒 **Security Considerations**

### **Authentication & Authorization**
- JWT token management
- Role-based access control
- Session management

### **Data Protection**
- Encrypted connections (TLS/SSL)
- Secure credential storage
- Network access controls

### **API Security**
- Rate limiting
- Input validation
- CORS configuration

## 📚 **Documentation and Support**

### **Key Files**
- `NEXTJS_INTEGRATION_GUIDE.md` - Frontend integration details
- `ONLINE_MONGODB_SETUP.md` - MongoDB Atlas setup
- `docker-compose.yml` - Service configuration
- `env.online` - Environment template

### **Scripts**
- `restart-with-online-mongo.sh` - Backend restart script
- `unwanted/setup-online-database.py` - Database initialization
- `tests/test-complete-integration.py` - Integration testing

### **Support Resources**
- MongoDB Atlas documentation
- Redis Cloud documentation
- Next.js documentation
- FastAPI documentation

## ✅ **Deployment Checklist**

- [ ] Repository cloned and branch checked out
- [ ] Backend environment configured
- [ ] Backend services started and healthy
- [ ] Frontend dependencies installed
- [ ] Frontend server running
- [ ] Database initialized with test data
- [ ] Integration tests passing (4/4)
- [ ] Frontend login working
- [ ] Role-based access verified
- [ ] Production environment variables set
- [ ] SSL/TLS configured (production)
- [ ] Monitoring and alerting configured
- [ ] Backup strategy implemented

## 🎉 **Success Indicators**

When deployment is successful, you should see:

1. **Backend Services**: All 7 services running and healthy
2. **Database**: Connected to MongoDB Atlas with test data
3. **Cache**: Connected to Redis Cloud
4. **Frontend**: Accessible and functional
5. **Authentication**: Login working with test credentials
6. **Integration Tests**: 4/4 tests passing
7. **Dashboard**: Accessible after successful login

## 🚀 **Next Steps After Deployment**

1. **User Management**: Create production users and roles
2. **Data Migration**: Import existing data if applicable
3. **Customization**: Configure business-specific workflows
4. **Training**: Train end users on system usage
5. **Support**: Establish support and maintenance procedures

---

**🎯 The WFM system is now fully deployed and ready for production use!**

For additional support or questions, refer to the individual service documentation or contact the development team.

## Online MongoDB Configuration

If you are using an online MongoDB instance (e.g., MongoDB Atlas), you will need to configure the connection string.

### Automated Setup

Run the interactive setup script from the `wfmApp` directory:
```bash
./unwanted/setup-online-mongo.sh
```
Follow the prompts to enter your MongoDB URI.

### Manual Setup

1. Create a file named `.env.online` in the `wfmApp` directory.
2. Add the following line, replacing `<your-mongodb-uri>` with your actual connection string:
   ```
   MONGO_URI=<your-mongodb-uri>
   ```

### Testing the Online Connection

To test the connection to your online MongoDB instance, run:
```bash
python3 tests/test-online-mongo.py
```

## Running the Integrated System

Once all services are running and the database is configured, you can start the Next.js frontend.

### Start the Frontend
From the `wfmApp` directory:
```bash
npm run dev
```

### Run End-to-End Tests
To ensure the full system is working, run the integration test again:
```bash
python3 tests/test-complete-integration.py
```

## Troubleshooting

- **Connection Errors**: Double-check your `.env` files and ensure the service names in your Docker network match the hosts specified in the configuration.
- **Authentication Issues**: Verify that the JWT secret is consistent across the `auth_service` and `api_gateway`.
- **CORS Errors**: Ensure the API gateway is configured with the correct CORS origins, allowing requests from your frontend's URL.

## Appendix

### Key Scripts and Files

- `docker-compose.integrated.yml` - Docker Compose file for all backend services.
- `unwanted/setup-online-database.py` - Database initialization
- `tests/test-complete-integration.py` - Integration testing
- `unwanted/clear-and-reset-database.py` - Database cleanup
- `.env.example` - Example environment file for backend services.

### Service Endpoints

- **API Gateway**: `http://localhost:8000`
- **Next.js Frontend**: `http://localhost:3000`

---
*This document provides a comprehensive guide to deploying and testing the integrated WFM system.*
