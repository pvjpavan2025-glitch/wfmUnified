# WFM Unified Application

This repository contains the integrated Workforce Management (WFM) system with BPMN workflow modeling capabilities.

## Architecture Overview

The system consists of:

1. **wfmApp** - Main UI application (Next.js) with integrated BPMN modeler
2. **wfmServices** - Backend microservices for WFM operations
3. **wfmProcess** - BPMN workflow engine backend
4. **intServices** - Integration layer services

## Key Features

- **Unified Interface**: Single application with shared sidebar navigation
- **BPMN Modeling**: Integrated workflow designer accessible via "Modelling" menu
- **Microservices Architecture**: Scalable backend services
- **Containerized Deployment**: Docker-based deployment with unified compose file

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
- **BPMN Backend**: http://localhost:8100
- **Auth Service**: http://localhost:8001
- **Config Service**: http://localhost:8002
- **Rules Service**: http://localhost:8003
- **Scheduler Service**: http://localhost:8004
- **Issue Service**: http://localhost:8005
- **Analytics Service**: http://localhost:8006
- **Dashboard Service**: http://localhost:8007
- **Order Service**: http://localhost:8008
- **Traefik Dashboard**: http://localhost:8080
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## Integration Details

### Frontend Integration

The wfmProcess frontend has been integrated into wfmApp:

- **Modelling Menu**: Added to the main sidebar navigation
- **BPMN Components**: Copied and adapted from wfmProcess/frontend
- **Shared Layout**: Uses the same AppShell component for consistent UI
- **Dependencies**: Added BPMN-related packages to wfmApp

### Backend Integration

- **Unified Docker Compose**: Single file managing all services
- **Network Configuration**: All services on the same Docker network
- **Database Setup**: PostgreSQL for BPMN engine, MongoDB for WFM services
- **Service Discovery**: Services can communicate via container names

### Key Files

- `/docker-compose.yml` - Unified deployment configuration
- `/wfm/wfmApp/app/modelling/` - BPMN modeling pages
- `/wfm/wfmApp/components/modelling/` - BPMN React components
- `/wfm/wfmApp/components/app-shell.tsx` - Updated with Modelling menu

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
