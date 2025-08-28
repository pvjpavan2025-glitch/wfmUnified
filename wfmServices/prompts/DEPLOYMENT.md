# WFM System Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the WFM (Workforce Management) system across different environments. The system consists of 7 microservices, each running in its own container with shared infrastructure components.

## Prerequisites

### System Requirements

#### Minimum Requirements
- **CPU**: 4 cores
- **RAM**: 8GB
- **Storage**: 50GB SSD
- **OS**: Ubuntu 20.04+ / CentOS 8+ / macOS 10.15+

#### Recommended Requirements
- **CPU**: 8 cores
- **RAM**: 16GB
- **Storage**: 100GB SSD
- **OS**: Ubuntu 22.04 LTS

### Software Dependencies

#### Required Software
```bash
# Core dependencies
Docker 20.10+
Docker Compose 2.0+
Python 3.11+
Git 2.30+
Make 4.0+

# Optional for production
Kubernetes 1.24+
Helm 3.10+
Nginx 1.20+
```

#### Installation Commands
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y docker.io docker-compose python3.11 python3-pip git make

# CentOS/RHEL
sudo yum install -y docker docker-compose python3.11 python3-pip git make

# macOS
brew install docker docker-compose python@3.11 git make
```

## Environment Setup

### 1. Development Environment

#### Local Setup
```bash
# Clone the repository
git clone <repository-url>
cd wfmv4

# Copy environment file
cp env.example .env

# Edit environment variables
nano .env
```

#### Environment Variables
```bash
# Database Configuration
MONGODB_URL=mongodb://admin:password@localhost:27017/
REDIS_URL=redis://localhost:6379
DATABASE_NAME=wfm

# Security Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30
BCRYPT_ROUNDS=12

# Service Configuration
SERVICE_NAME=wfm-service
SERVICE_PORT=8000
ENVIRONMENT=development
DEBUG=true

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json
ENABLE_CORRELATION_ID=true

# Service URLs
API_GATEWAY_URL=http://localhost:8000
AUTH_SERVICE_URL=http://localhost:8001
CONFIG_SERVICE_URL=http://localhost:8002
RULES_SERVICE_URL=http://localhost:8003
SCHEDULER_SERVICE_URL=http://localhost:8004
ISSUE_SERVICE_URL=http://localhost:8005
ANALYTICS_SERVICE_URL=http://localhost:8006
```

#### Start Development Environment
```bash
# Install dependencies
make install

# Start infrastructure
make db-start

# Initialize database
make db-init

# Start all services
make dev-start

# Check health
make health-check
```

### 2. Staging Environment

#### Docker Compose Setup
```yaml
# docker-compose.staging.yml
version: '3.8'

services:
  mongodb:
    image: mongo:6.0
    container_name: wfm_mongodb_staging
    restart: unless-stopped
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: password
      MONGO_INITDB_DATABASE: wfm
    volumes:
      - mongodb_data_staging:/data/db
      - ./scripts/init-mongo.js:/docker-entrypoint-initdb.d/init-mongo.js:ro

  redis:
    image: redis:7-alpine
    container_name: wfm_redis_staging
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data_staging:/data

  api-gateway:
    build: .
    container_name: wfm_api_gateway_staging
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=staging
      - SERVICE_PORT=8000
    depends_on:
      - mongodb
      - redis

  auth-service:
    build: .
    container_name: wfm_auth_service_staging
    restart: unless-stopped
    ports:
      - "8001:8001"
    environment:
      - ENVIRONMENT=staging
      - SERVICE_PORT=8001
    depends_on:
      - mongodb
      - redis

  config-service:
    build: .
    container_name: wfm_config_service_staging
    restart: unless-stopped
    ports:
      - "8002:8002"
    environment:
      - ENVIRONMENT=staging
      - SERVICE_PORT=8002
    depends_on:
      - mongodb
      - redis

  rules-service:
    build: .
    container_name: wfm_rules_service_staging
    restart: unless-stopped
    ports:
      - "8003:8003"
    environment:
      - ENVIRONMENT=staging
      - SERVICE_PORT=8003
    depends_on:
      - mongodb
      - redis

  scheduler-service:
    build: .
    container_name: wfm_scheduler_service_staging
    restart: unless-stopped
    ports:
      - "8004:8004"
    environment:
      - ENVIRONMENT=staging
      - SERVICE_PORT=8004
    depends_on:
      - mongodb
      - redis

  issue-service:
    build: .
    container_name: wfm_issue_service_staging
    restart: unless-stopped
    ports:
      - "8005:8005"
    environment:
      - ENVIRONMENT=staging
      - SERVICE_PORT=8005
    depends_on:
      - mongodb
      - redis

  analytics-service:
    build: .
    container_name: wfm_analytics_service_staging
    restart: unless-stopped
    ports:
      - "8006:8006"
    environment:
      - ENVIRONMENT=staging
      - SERVICE_PORT=8006
    depends_on:
      - mongodb
      - redis

volumes:
  mongodb_data_staging:
  redis_data_staging:
```

#### Deploy to Staging
```bash
# Build and start staging environment
docker-compose -f docker-compose.staging.yml up -d --build

# Check service status
docker-compose -f docker-compose.staging.yml ps

# View logs
docker-compose -f docker-compose.staging.yml logs -f

# Run health checks
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health
curl http://localhost:8005/health
curl http://localhost:8006/health
```

### 3. Production Environment

#### Kubernetes Deployment

##### Namespace Setup
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: wfm
  labels:
    name: wfm
```

##### ConfigMap for Environment Variables
```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: wfm-config
  namespace: wfm
data:
  MONGODB_URL: "mongodb://admin:password@mongodb:27017/"
  REDIS_URL: "redis://redis:6379"
  DATABASE_NAME: "wfm"
  JWT_ALGORITHM: "HS256"
  JWT_EXPIRATION_MINUTES: "30"
  BCRYPT_ROUNDS: "12"
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
  LOG_FORMAT: "json"
  ENABLE_CORRELATION_ID: "true"
```

##### Secret for Sensitive Data
```yaml
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: wfm-secrets
  namespace: wfm
type: Opaque
data:
  JWT_SECRET_KEY: <base64-encoded-secret>
  MONGODB_PASSWORD: <base64-encoded-password>
```

##### MongoDB Deployment
```yaml
# k8s/mongodb.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mongodb
  namespace: wfm
spec:
  serviceName: mongodb
  replicas: 1
  selector:
    matchLabels:
      app: mongodb
  template:
    metadata:
      labels:
        app: mongodb
    spec:
      containers:
      - name: mongodb
        image: mongo:6.0
        ports:
        - containerPort: 27017
        env:
        - name: MONGO_INITDB_ROOT_USERNAME
          value: "admin"
        - name: MONGO_INITDB_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: wfm-secrets
              key: MONGODB_PASSWORD
        - name: MONGO_INITDB_DATABASE
          value: "wfm"
        volumeMounts:
        - name: mongodb-data
          mountPath: /data/db
  volumeClaimTemplates:
  - metadata:
      name: mongodb-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
---
apiVersion: v1
kind: Service
metadata:
  name: mongodb
  namespace: wfm
spec:
  selector:
    app: mongodb
  ports:
  - port: 27017
    targetPort: 27017
```

##### Redis Deployment
```yaml
# k8s/redis.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: wfm
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        volumeMounts:
        - name: redis-data
          mountPath: /data
      volumes:
      - name: redis-data
        persistentVolumeClaim:
          claimName: redis-pvc
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: redis-pvc
  namespace: wfm
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: wfm
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
```

##### API Gateway Deployment
```yaml
# k8s/api-gateway.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
  namespace: wfm
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-gateway
  template:
    metadata:
      labels:
        app: api-gateway
    spec:
      containers:
      - name: api-gateway
        image: wfm/api-gateway:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: wfm-config
        - secretRef:
            name: wfm-secrets
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: api-gateway
  namespace: wfm
spec:
  selector:
    app: api-gateway
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

##### Service Deployments
```yaml
# k8s/services.yaml
# Auth Service
apiVersion: apps/v1
kind: Deployment
metadata:
  name: auth-service
  namespace: wfm
spec:
  replicas: 2
  selector:
    matchLabels:
      app: auth-service
  template:
    metadata:
      labels:
        app: auth-service
    spec:
      containers:
      - name: auth-service
        image: wfm/auth-service:latest
        ports:
        - containerPort: 8001
        envFrom:
        - configMapRef:
            name: wfm-config
        - secretRef:
            name: wfm-secrets
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: auth-service
  namespace: wfm
spec:
  selector:
    app: auth-service
  ports:
  - port: 8001
    targetPort: 8001

# Config Service
apiVersion: apps/v1
kind: Deployment
metadata:
  name: config-service
  namespace: wfm
spec:
  replicas: 2
  selector:
    matchLabels:
      app: config-service
  template:
    metadata:
      labels:
        app: config-service
    spec:
      containers:
      - name: config-service
        image: wfm/config-service:latest
        ports:
        - containerPort: 8002
        envFrom:
        - configMapRef:
            name: wfm-config
        - secretRef:
            name: wfm-secrets
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: config-service
  namespace: wfm
spec:
  selector:
    app: config-service
  ports:
  - port: 8002
    targetPort: 8002

# Rules Service
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rules-service
  namespace: wfm
spec:
  replicas: 2
  selector:
    matchLabels:
      app: rules-service
  template:
    metadata:
      labels:
        app: rules-service
    spec:
      containers:
      - name: rules-service
        image: wfm/rules-service:latest
        ports:
        - containerPort: 8003
        envFrom:
        - configMapRef:
            name: wfm-config
        - secretRef:
            name: wfm-secrets
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: rules-service
  namespace: wfm
spec:
  selector:
    app: rules-service
  ports:
  - port: 8003
    targetPort: 8003

# Scheduler Service
apiVersion: apps/v1
kind: Deployment
metadata:
  name: scheduler-service
  namespace: wfm
spec:
  replicas: 2
  selector:
    matchLabels:
      app: scheduler-service
  template:
    metadata:
      labels:
        app: scheduler-service
    spec:
      containers:
      - name: scheduler-service
        image: wfm/scheduler-service:latest
        ports:
        - containerPort: 8004
        envFrom:
        - configMapRef:
            name: wfm-config
        - secretRef:
            name: wfm-secrets
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: scheduler-service
  namespace: wfm
spec:
  selector:
    app: scheduler-service
  ports:
  - port: 8004
    targetPort: 8004

# Issue Service
apiVersion: apps/v1
kind: Deployment
metadata:
  name: issue-service
  namespace: wfm
spec:
  replicas: 2
  selector:
    matchLabels:
      app: issue-service
  template:
    metadata:
      labels:
        app: issue-service
    spec:
      containers:
      - name: issue-service
        image: wfm/issue-service:latest
        ports:
        - containerPort: 8005
        envFrom:
        - configMapRef:
            name: wfm-config
        - secretRef:
            name: wfm-secrets
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: issue-service
  namespace: wfm
spec:
  selector:
    app: issue-service
  ports:
  - port: 8005
    targetPort: 8005

# Analytics Service
apiVersion: apps/v1
kind: Deployment
metadata:
  name: analytics-service
  namespace: wfm
spec:
  replicas: 2
  selector:
    matchLabels:
      app: analytics-service
  template:
    metadata:
      labels:
        app: analytics-service
    spec:
      containers:
      - name: analytics-service
        image: wfm/analytics-service:latest
        ports:
        - containerPort: 8006
        envFrom:
        - configMapRef:
            name: wfm-config
        - secretRef:
            name: wfm-secrets
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: analytics-service
  namespace: wfm
spec:
  selector:
    app: analytics-service
  ports:
  - port: 8006
    targetPort: 8006
```

#### Deploy to Production
```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Apply secrets and configmaps
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/configmap.yaml

# Deploy infrastructure
kubectl apply -f k8s/mongodb.yaml
kubectl apply -f k8s/redis.yaml

# Wait for infrastructure to be ready
kubectl wait --for=condition=ready pod -l app=mongodb -n wfm
kubectl wait --for=condition=ready pod -l app=redis -n wfm

# Deploy services
kubectl apply -f k8s/api-gateway.yaml
kubectl apply -f k8s/services.yaml

# Check deployment status
kubectl get pods -n wfm
kubectl get services -n wfm

# Get external IP
kubectl get service api-gateway -n wfm
```

## Monitoring & Logging

### Prometheus Setup
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'wfm-services'
    static_configs:
      - targets: 
        - 'api-gateway:8000'
        - 'auth-service:8001'
        - 'config-service:8002'
        - 'rules-service:8003'
        - 'scheduler-service:8004'
        - 'issue-service:8005'
        - 'analytics-service:8006'
    metrics_path: /metrics
```

### Grafana Dashboards
```json
// monitoring/grafana-dashboard.json
{
  "dashboard": {
    "title": "WFM System Dashboard",
    "panels": [
      {
        "title": "Service Health",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=\"wfm-services\"}",
            "legendFormat": "{{instance}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "http_request_duration_seconds{job=\"wfm-services\"}",
            "legendFormat": "{{instance}} - {{method}} {{path}}"
          }
        ]
      }
    ]
  }
}
```

## Backup & Recovery

### Database Backup
```bash
# MongoDB backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/mongodb"
mkdir -p $BACKUP_DIR

# Backup MongoDB
docker exec wfm_mongodb mongodump --out /dump
docker cp wfm_mongodb:/dump $BACKUP_DIR/mongodb_$DATE

# Compress backup
tar -czf $BACKUP_DIR/mongodb_$DATE.tar.gz $BACKUP_DIR/mongodb_$DATE
rm -rf $BACKUP_DIR/mongodb_$DATE

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

### Redis Backup
```bash
# Redis backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/redis"
mkdir -p $BACKUP_DIR

# Backup Redis
docker exec wfm_redis redis-cli BGSAVE
sleep 5
docker cp wfm_redis:/data/dump.rdb $BACKUP_DIR/redis_$DATE.rdb

# Compress backup
gzip $BACKUP_DIR/redis_$DATE.rdb

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "*.rdb.gz" -mtime +30 -delete
```

## Security Configuration

### SSL/TLS Setup
```nginx
# nginx/ssl.conf
server {
    listen 443 ssl http2;
    server_name wfm.yourdomain.com;

    ssl_certificate /etc/ssl/certs/wfm.crt;
    ssl_certificate_key /etc/ssl/private/wfm.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    location / {
        proxy_pass http://api-gateway:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Network Policies
```yaml
# k8s/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: wfm-network-policy
  namespace: wfm
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 80
    - protocol: TCP
      port: 443
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: wfm
    ports:
    - protocol: TCP
      port: 27017
    - protocol: TCP
      port: 6379
```

## Troubleshooting

### Common Issues

#### Service Not Starting
```bash
# Check service logs
kubectl logs -f deployment/api-gateway -n wfm
docker-compose logs api-gateway

# Check service status
kubectl get pods -n wfm
docker-compose ps

# Check resource usage
kubectl top pods -n wfm
docker stats
```

#### Database Connection Issues
```bash
# Test MongoDB connection
kubectl exec -it deployment/mongodb -n wfm -- mongosh --eval "db.adminCommand('ping')"
docker exec wfm_mongodb mongosh --eval "db.adminCommand('ping')"

# Check Redis connection
kubectl exec -it deployment/redis -n wfm -- redis-cli ping
docker exec wfm_redis redis-cli ping
```

#### Performance Issues
```bash
# Check resource usage
kubectl top nodes
kubectl top pods -n wfm

# Check network connectivity
kubectl exec -it deployment/api-gateway -n wfm -- curl auth-service:8001/health
docker exec wfm_api_gateway curl auth-service:8001/health
```

### Health Check Scripts
```bash
#!/bin/bash
# health-check.sh

SERVICES=(
    "http://localhost:8000/health"
    "http://localhost:8001/health"
    "http://localhost:8002/health"
    "http://localhost:8003/health"
    "http://localhost:8004/health"
    "http://localhost:8005/health"
    "http://localhost:8006/health"
)

for service in "${SERVICES[@]}"; do
    response=$(curl -s -o /dev/null -w "%{http_code}" $service)
    if [ $response -eq 200 ]; then
        echo "✅ $service is healthy"
    else
        echo "❌ $service is unhealthy (HTTP $response)"
    fi
done
```

## Maintenance

### Regular Maintenance Tasks

#### Daily
- [ ] Check service health
- [ ] Review error logs
- [ ] Monitor resource usage
- [ ] Verify backup completion

#### Weekly
- [ ] Update security patches
- [ ] Review performance metrics
- [ ] Clean up old logs
- [ ] Test backup restoration

#### Monthly
- [ ] Update dependencies
- [ ] Review access logs
- [ ] Update SSL certificates
- [ ] Performance optimization

### Update Procedures

#### Rolling Update
```bash
# Update service with zero downtime
kubectl set image deployment/api-gateway api-gateway=wfm/api-gateway:latest -n wfm
kubectl rollout status deployment/api-gateway -n wfm
```

#### Blue-Green Deployment
```bash
# Create new deployment
kubectl apply -f k8s/api-gateway-v2.yaml

# Switch traffic
kubectl patch service api-gateway -p '{"spec":{"selector":{"version":"v2"}}}'

# Remove old deployment
kubectl delete deployment api-gateway-v1 -n wfm
```

## Conclusion

This deployment guide provides comprehensive instructions for deploying the WFM system across different environments. The modular architecture allows for flexible deployment options while maintaining high availability and performance. Regular monitoring and maintenance ensure the system remains stable and secure in production.

For additional support or questions, refer to the troubleshooting section or contact the development team. 