# Deployment Guide

This guide covers deploying the BPMN Workflow Engine in various environments.

## 🚀 Quick Start with Docker

### Prerequisites
- Docker & Docker Compose installed
- At least 4GB RAM available
- Ports 80, 3000, 8000, 5432, 6379 available

### 1. Clone and Setup
```bash
git clone <repository-url>
cd bpmn-workflow-engine

# Copy environment file
cp backend/env.example backend/.env

# Edit environment variables
nano backend/.env
```

### 2. Start Services
```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### 3. Access Applications
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/docs
- **Database**: localhost:5432
- **Redis**: localhost:6379

## 🏗️ Production Deployment

### Environment Variables
```bash
# Production environment file
DEBUG=false
LOG_LEVEL=WARNING
SECRET_KEY=<generate-secure-key>
DATABASE_URL=<production-db-url>
REDIS_URL=<production-redis-url>
CORS_ORIGINS=<your-domain>
```

### Database Setup
```bash
# Create production database
createdb workflow_production

# Run migrations
cd backend
alembic upgrade head
```

### SSL Configuration
```bash
# Generate SSL certificates
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx.key -out nginx.crt

# Update nginx configuration
# See docker/nginx/conf.d/default.conf
```

### Scaling
```bash
# Scale backend services
docker-compose up -d --scale backend=3

# Use load balancer (HAProxy, Nginx)
# Configure Redis clustering for high availability
```

## ☁️ Cloud Deployment

### AWS Deployment
```bash
# Using AWS ECS
aws ecs create-cluster --cluster-name bpmn-workflow

# Deploy with AWS CLI
aws ecs register-task-definition --cli-input-json file://task-definition.json
aws ecs create-service --cluster bpmn-workflow --service-name bpmn-service
```

### Kubernetes Deployment
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods
kubectl get services
```

### Docker Swarm
```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.swarm.yml bpmn-workflow
```

## 🔧 Configuration

### Backend Configuration
```python
# app/core/config.py
class Settings(BaseSettings):
    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # Workflow Engine
    max_workflow_instances: int = Field(default=1000, env="MAX_WORKFLOW_INSTANCES")
    workflow_timeout_seconds: int = Field(default=3600, env="WORKFLOW_TIMEOUT_SECONDS")
```

### Frontend Configuration
```typescript
// Environment variables
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/ws

// API configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
```

### Nginx Configuration
```nginx
# docker/nginx/conf.d/default.conf
server {
    listen 80;
    server_name localhost;
    
    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📊 Monitoring & Health Checks

### Health Check Endpoints
```bash
# Backend health
curl http://localhost:8000/health

# Database health
pg_isready -h localhost -p 5432 -U workflow_user

# Redis health
redis-cli ping
```

### Logging Configuration
```python
# Structured logging
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
```

### Metrics Collection
```python
# Prometheus metrics
from prometheus_client import Counter, Histogram, generate_latest

# Workflow metrics
workflow_started = Counter('workflow_started_total', 'Total workflows started')
workflow_completed = Counter('workflow_completed_total', 'Total workflows completed')
workflow_duration = Histogram('workflow_duration_seconds', 'Workflow execution time')
```

## 🔒 Security Configuration

### Authentication & Authorization
```python
# JWT token configuration
from jose import JWTError, jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt
```

### CORS Configuration
```python
# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)
```

### Rate Limiting
```python
# Redis-based rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/upload-bpmn")
@limiter.limit("10/minute")
async def upload_bpmn(request: Request):
    # Implementation
    pass
```

## 🚨 Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Check database status
docker-compose logs postgres

# Test connection
docker exec -it bpmn-postgres psql -U workflow_user -d workflow
```

#### Redis Connection Issues
```bash
# Check Redis status
docker-compose logs redis

# Test Redis connection
docker exec -it bpmn-redis redis-cli ping
```

#### Frontend Build Issues
```bash
# Clear node modules
rm -rf frontend/node_modules
npm install

# Check build logs
docker-compose logs frontend
```

#### Backend Startup Issues
```bash
# Check Python dependencies
docker exec -it bpmn-backend pip list

# Check application logs
docker-compose logs backend
```

### Performance Tuning

#### Database Optimization
```sql
-- Create indexes for common queries
CREATE INDEX idx_workflow_instances_status ON workflow_instances(status);
CREATE INDEX idx_task_instances_workflow_id ON task_instances(workflow_instance_id);
CREATE INDEX idx_execution_logs_timestamp ON execution_logs(created_at);
```

#### Redis Optimization
```bash
# Redis configuration
maxmemory 256mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

#### Application Optimization
```python
# Connection pooling
from sqlalchemy.pool import QueuePool

engine = create_async_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True
)
```

## 📈 Scaling Strategies

### Horizontal Scaling
```yaml
# docker-compose.scale.yml
services:
  backend:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### Load Balancing
```nginx
# Nginx upstream configuration
upstream backend {
    least_conn;
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}
```

### Database Scaling
```bash
# Read replicas
# Master-slave replication
# Database sharding strategies
```

## 🔄 Backup & Recovery

### Database Backup
```bash
# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
docker exec bpmn-postgres pg_dump -U workflow_user workflow > $BACKUP_DIR/workflow_$DATE.sql

# Retention policy
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
```

### Configuration Backup
```bash
# Backup configuration files
tar -czf config_backup_$DATE.tar.gz \
  backend/.env \
  docker/nginx/conf.d/ \
  docker-compose.yml
```

### Disaster Recovery
```bash
# Restore database
docker exec -i bpmn-postgres psql -U workflow_user workflow < backup.sql

# Restore configuration
tar -xzf config_backup_$DATE.tar.gz
docker-compose restart
```

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [BPMN.io Documentation](https://bpmn.io/)
- [Docker Documentation](https://docs.docker.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)
