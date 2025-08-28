# WFM Unified Application

[![Build Status](https://dev.azure.com/tsaro/WFM/_apis/build/status%2FwfmUnified?branchName=main)](https://dev.azure.com/tsaro/WFM/_build/latest?definitionId=4&branchName=main)

This repository contains the integrated Workforce Management (WFM) system with Order-Process-Task workflow architecture and BPMN modeling capabilities.

## Architecture Overview

The system implements an **Order-Process-Task** hierarchical workflow architecture:

### Core Components
1. **wfmApp** - Next.js frontend with Order-Process-Task UI and integrated BPMN modeler
2. **wfmServices** - API Gateway and core backend services
3. **wfmProcess** - SpiffWorkflow BPMN engine for process execution
4. **intServices** - Integration layer for external systems
5. **vendor-service** - Vendor and technician management
6. **process-service** - BPMN process management and execution

### Workflow Hierarchy
- **Orders**: Top-level work requests from external systems (OSM, CRM)
- **Processes**: BPMN workflows that define how to fulfill orders
- **Tasks**: Individual work items assigned to technicians with leads

### Key Principles
- Orders contain multiple Processes
- Processes contain multiple Tasks
- Only Tasks can be assigned/scheduled to technicians
- Each task assignment requires both a Technician and Team Lead
- BPMN diagrams represent Processes and are executed by SpiffWorkflow

## Key Features

### Frontend Features
- **Order Management**: Complete order lifecycle with process and task visibility
- **Task Management**: Advanced task assignment with technician + lead pairing
- **Vendor Management**: Comprehensive vendor, technician, and team lead management
- **BPMN Modeling**: Integrated workflow designer for process creation
- **Dashboard**: Real-time metrics for orders, processes, tasks, and technician utilization
- **Unified Interface**: Single application with consistent navigation

### Backend Features
- **Microservices Architecture**: Scalable, independent services
- **BPMN Process Engine**: SpiffWorkflow integration for workflow execution
- **Rules Engine**: Automatic process identification from order metadata
- **Scheduling System**: Advanced task assignment with skill matching
- **Analytics**: Performance tracking and utilization metrics
- **API Gateway**: Centralized routing and authentication

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for development)
- Python 3.9+ (for backend development)

### Development Setup

1. **Clone and setup the repository:**
   ```bash
   git clone <repository-url>
   cd wfm-unified
   ```

2. **Install frontend dependencies:**
   ```bash
   cd wfm/wfmApp
   npm install --legacy-peer-deps
   ```

3. **Start the unified application:**
   ```bash
   # From the root directory
   docker-compose up -d
   ```

### Service Ports

- **Frontend (wfmApp)**: http://localhost:3000
- **API Gateway**: http://localhost:8000
- **Auth Service**: http://localhost:8001
- **Config Service**: http://localhost:8002
- **Rules Service**: http://localhost:8003
- **Scheduler Service**: http://localhost:8004
- **Issue Service**: http://localhost:8005
- **Analytics Service**: http://localhost:8006
- **Dashboard Service**: http://localhost:8007
- **Order Service**: http://localhost:8008
- **Vendor Service**: http://localhost:8009
- **Process Service**: http://localhost:8010
- **BPMN Backend**: http://localhost:8100
- **Traefik Dashboard**: http://localhost:8080
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## Order-Process-Task Workflow

### Workflow Lifecycle

1. **Order Creation**: External systems (OSM, CRM) create orders with metadata
2. **Process Identification**: Rules service analyzes order metadata to identify required processes
3. **Process Instantiation**: BPMN processes are created and executed via SpiffWorkflow
4. **Task Generation**: Processes generate specific tasks that need completion
5. **Task Assignment**: Tasks are assigned to technician + lead pairs based on skills and availability
6. **Task Execution**: Technicians complete tasks with lead oversight
7. **Process Completion**: All tasks complete, marking the process as finished
8. **Order Fulfillment**: All processes complete, fulfilling the original order

### Data Flow

```
External System → Order → Rules Engine → Process Selection → BPMN Execution → Task Creation → Assignment → Completion
```

### Integration Points

- **Frontend Integration**: Unified wfmApp with Order, Task, Vendor, and BPMN modeling pages
- **Backend Integration**: Microservices communicate via API Gateway
- **Process Integration**: SpiffWorkflow engine executes BPMN processes
- **Database Integration**: MongoDB for WFM data, PostgreSQL for BPMN engine
- **External Integration**: APIs for OSM, CRM, and other external systems

### Key Files

#### Configuration
- `/docker-compose.yml` - Unified deployment configuration
- `/AZURE_DEPLOYMENT_GUIDE.md` - Azure deployment instructions
- `/.env.example` - Environment variable template

#### Frontend (wfmApp)
- `/wfmApp/app/orders/page.tsx` - Order management interface
- `/wfmApp/app/tasks/page.tsx` - Task management interface  
- `/wfmApp/app/vendors/page.tsx` - Vendor management interface
- `/wfmApp/app/modelling/page.tsx` - BPMN modeling interface
- `/wfmApp/components/task-management.tsx` - Task assignment and tracking
- `/wfmApp/components/dashboard-content.tsx` - Order-Process-Task metrics
- `/wfmApp/components/app-shell.tsx` - Navigation with new menu items

#### Backend Services
- `/wfmServices/` - Core WFM microservices
- `/wfmServices/vendor_service/` - Vendor and technician management
- `/wfmServices/process_service/` - Process management and BPMN integration
- `/wfmProcess/backend/` - SpiffWorkflow BPMN engine
- `/intServices/` - External system integrations

## Development Workflow

### Branch Strategy

- **feature/load-save-intg** - Current integration branch (both repos)
- Create feature branches from this branch for additional work

### Making Changes

1. **Frontend Changes**: Work in `/wfm/wfmApp/`
2. **Backend Services**: Work in `/wfm/wfmServices/`
3. **BPMN Engine**: Work in `/wfmProcess/backend/`
4. **Integration Services**: Work in `/wfm/intServices/`

### Testing

```bash
# Start all services
docker-compose up -d

# Check service health
docker-compose ps

# View logs
docker-compose logs -f [service-name]

# Stop all services
docker-compose down
```

## Environment Configuration

### Production Environment Variables

Update the following in `docker-compose.yml` for production:

- MongoDB connection strings
- Redis connection strings
- JWT secret keys
- Database passwords
- API endpoints

### Development Environment

For local development, you can override environment variables:

```bash
# Create .env file in root directory
cp .env.example .env
# Edit .env with your local configuration
```

## Troubleshooting

### Common Issues

1. **Port Conflicts**: Ensure ports 3000, 8000-8008, 5432, 6379 are available
2. **Docker Network**: If services can't communicate, check network configuration
3. **Dependencies**: Run `npm install --legacy-peer-deps` in wfmApp for BPMN packages
4. **Database Connection**: Ensure PostgreSQL is healthy before starting BPMN backend

### Logs and Debugging

```bash
# View all service logs
docker-compose logs

# View specific service logs
docker-compose logs wfmapp
docker-compose logs wfmprocess-backend

# Follow logs in real-time
docker-compose logs -f
```

## Contributing

1. Create feature branch from `feature/load-save-intg`
2. Make changes and test locally
3. Update documentation if needed
4. Submit pull request

## License

[Your License Here]
