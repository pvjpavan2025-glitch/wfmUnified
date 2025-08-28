# 🐳 WFM Unified System - Modular Docker Compose Structure

## 📋 Overview

The WFM Unified System has been restructured into a modular Docker Compose architecture for better maintainability, scalability, and startup control. This structure ensures services start in the correct order with proper dependency management.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Main Orchestrator                        │
│                 docker-compose.yml                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Service Layers                           │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   Frontend      │  │   BPMN Engine   │  │  Backend    │ │
│  │   Layer         │  │   Layer         │  │  Services   │ │
│  │                 │  │                 │  │  Layer      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│           │                     │                   │       │
│           ▼                     ▼                   ▼       │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                 Database Layer                          │ │
│  │           (PostgreSQL + Redis + MongoDB)               │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 📁 File Structure

```
wfmUnified/
├── docker-compose.yml              # Main orchestrator
├── docker-compose.databases.yml    # Database layer
├── docker-compose.backend.yml      # Backend services layer
├── docker-compose.bpmn.yml         # BPMN process engine layer
├── docker-compose.frontend.yml     # Frontend application layer
├── start-wfm.sh                    # Startup orchestration script
├── stop-wfm.sh                     # Shutdown orchestration script
└── README-MODULAR-DOCKER.md        # This file
```

## 🚀 Startup Sequence

The system follows a **layered startup approach** with proper health checks:

### **Phase 1: Database Layer** 🗄️
- **PostgreSQL** - Workflow storage for BPMN engine
- **Redis** - Caching and state management
- **MongoDB** - Application data storage

### **Phase 2: Backend Services Layer** 🔧
- **API Gateway** - Central routing and authentication
- **Auth Service** - User authentication and JWT management
- **Config Service** - Configuration management
- **Rules Service** - Business rules engine
- **Order Service** - Order management
- **Scheduler Service** - Task scheduling
- **Issue Service** - Issue tracking
- **Analytics Service** - Data analytics
- **Dashboard Service** - Dashboard data
- **Vendor Service** - Vendor management
- **Process Service** - Process orchestration

### **Phase 3: BPMN Process Engine Layer** ⚙️
- **wfmprocess-backend** - BPMN workflow execution engine

### **Phase 4: Frontend Layer** 🌐
- **wfmapp** - Unified frontend application

## 🎯 Key Benefits

✅ **Modular Design** - Each layer can be developed, tested, and deployed independently
✅ **Proper Dependencies** - Services start in the correct order with health checks
✅ **Easy Maintenance** - Clear separation of concerns
✅ **Scalability** - Individual layers can be scaled independently
✅ **Development Friendly** - Developers can work on specific layers without affecting others
✅ **Production Ready** - Proper health checks and restart policies

## 🚀 Quick Start

### **Start the Complete System**
```bash
./start-wfm.sh
```

### **Stop the Complete System**
```bash
./stop-wfm.sh
```

### **Start Individual Layers**
```bash
# Start only databases
docker-compose -f docker-compose.databases.yml up -d

# Start only backend services
docker-compose -f docker-compose.backend.yml up -d

# Start only BPMN engine
docker-compose -f docker-compose.bpmn.yml up -d

# Start only frontend
docker-compose -f docker-compose.frontend.yml up -d
```

### **Check Service Status**
```bash
# Check all services
docker-compose ps

# Check specific layer
docker-compose -f docker-compose.backend.yml ps

# View logs
docker-compose logs [service-name]
```

## 🔧 Configuration

### **Environment Variables**
Each service layer has its own environment configuration:
- **Databases**: Connection strings and credentials
- **Backend**: MongoDB URLs, Redis URLs, JWT secrets
- **BPMN**: PostgreSQL connection, Redis connection
- **Frontend**: API endpoints and service URLs

### **Ports**
| Service | Port | Description |
|---------|------|-------------|
| Frontend | 3000 | Main application |
| API Gateway | 8000 | Central API routing |
| Auth Service | 8001 | Authentication |
| Config Service | 8002 | Configuration |
| Rules Service | 8003 | Business rules |
| Scheduler Service | 8004 | Task scheduling |
| Issue Service | 8005 | Issue tracking |
| Analytics Service | 8006 | Analytics |
| Dashboard Service | 8007 | Dashboard data |
| Order Service | 8008 | Order management |
| Vendor Service | 8009 | Vendor management |
| Process Service | 8010 | Process orchestration |
| BPMN Backend | 8100 | Workflow engine |
| PostgreSQL | 5432 | Database |
| Redis | 6379 | Cache |
| MongoDB | 27017 | Document store |

## 🧪 Development Workflow

### **Working on Backend Services**
```bash
# Start only databases
docker-compose -f docker-compose.databases.yml up -d

# Start backend services with hot reload
docker-compose -f docker-compose.backend.yml up -d

# Make code changes - services will auto-reload
# Test your changes
```

### **Working on Frontend**
```bash
# Start all backend services
./start-wfm.sh

# Stop frontend
docker-compose -f docker-compose.frontend.yml down

# Start frontend in development mode
cd wfmApp && npm run dev
```

### **Working on BPMN Engine**
```bash
# Start databases
docker-compose -f docker-compose.databases.yml up -d

# Start BPMN engine
docker-compose -f docker-compose.bpmn.yml up -d

# Make changes and test
```

## 🚨 Troubleshooting

### **Service Won't Start**
1. Check if dependencies are healthy: `docker-compose ps`
2. View service logs: `docker-compose logs [service-name]`
3. Ensure database services are running and healthy
4. Check network connectivity between services

### **Health Check Failures**
1. Verify service endpoints are accessible
2. Check if required environment variables are set
3. Ensure database connections are working
4. Review service configuration

### **Port Conflicts**
1. Check if ports are already in use: `lsof -i :[PORT]`
2. Modify port mappings in compose files if needed
3. Ensure no other services are using the same ports

## 📚 Additional Resources

- **Docker Compose Documentation**: https://docs.docker.com/compose/
- **Docker Health Checks**: https://docs.docker.com/engine/reference/builder/#healthcheck
- **Service Dependencies**: https://docs.docker.com/compose/compose-file/#depends_on

## 🤝 Contributing

When adding new services:
1. Add the service to the appropriate layer compose file
2. Update the main orchestrator with proper dependencies
3. Add health checks if applicable
4. Update this documentation
5. Test the startup sequence

---

**🎉 Happy Coding with WFM Unified System!**
