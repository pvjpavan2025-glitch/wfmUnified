#!/bin/bash

# WFM Unified System Startup Script
# This script starts all services in the correct order with proper health checks

set -e

echo "🚀 Starting WFM Unified System..."
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check service health
check_service_health() {
    local service_name=$1
    local port=$2
    local max_attempts=30
    local attempt=1
    
    echo -e "${BLUE}🔍 Checking health of $service_name on port $port...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "http://localhost:$port/health" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name is healthy!${NC}"
            return 0
        fi
        
        echo -e "${YELLOW}⏳ Attempt $attempt/$max_attempts: $service_name not ready yet...${NC}"
        sleep 5
        ((attempt++))
    done
    
    echo -e "${RED}❌ $service_name failed to become healthy after $max_attempts attempts${NC}"
    return 1
}

# Function to check database health
check_database_health() {
    local service_name=$1
    local max_attempts=30
    local attempt=1
    
    echo -e "${BLUE}🔍 Checking health of $service_name...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose ps $service_name | grep -q "healthy"; then
            echo -e "${GREEN}✅ $service_name is healthy!${NC}"
            return 0
        fi
        
        echo -e "${YELLOW}⏳ Attempt $attempt/$max_attempts: $service_name not ready yet...${NC}"
        sleep 5
        ((attempt++))
    done
    
    echo -e "${RED}❌ $service_name failed to become healthy after $max_attempts attempts${NC}"
    return 1
}

# Step 1: Start all services with docker-compose
echo -e "${BLUE}📊 Starting all services with docker-compose...${NC}"
docker-compose up -d

echo -e "${YELLOW}⏳ Waiting for databases to be healthy...${NC}"
sleep 15

# Check database health
check_database_health "postgres"
check_database_health "redis"
check_database_health "mongodb"

echo -e "${GREEN}✅ All databases are healthy!${NC}"

# Step 2: Wait for backend services to start
echo -e "${BLUE}🔧 Waiting for backend services to start...${NC}"
sleep 20

# Check key backend services
check_service_health "API Gateway" "8000"
check_service_health "Auth Service" "8001"

echo -e "${GREEN}✅ Backend services are running!${NC}"

# Step 3: Wait for BPMN engine to start
echo -e "${BLUE}⚙️ Waiting for BPMN Process Engine to start...${NC}"
sleep 15

check_service_health "BPMN Backend" "8100"

echo -e "${GREEN}✅ BPMN Process Engine is running!${NC}"

# Step 4: Wait for frontend to start
echo -e "${BLUE}🌐 Waiting for Frontend Application to start...${NC}"
sleep 15

# Check frontend
if curl -s -f "http://localhost:3000" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend is accessible!${NC}"
else
    echo -e "${YELLOW}⚠️ Frontend is starting (may take a few more seconds)...${NC}"
fi

echo ""
echo -e "${GREEN}🎉 WFM Unified System startup completed!${NC}"
echo "=================================="
echo -e "${BLUE}📱 Frontend: http://localhost:3000${NC}"
echo -e "${BLUE}🔧 API Gateway: http://localhost:8000${NC}"
echo -e "${BLUE}⚙️ BPMN Backend: http://localhost:8100${NC}"
echo -e "${BLUE}🗄️ PostgreSQL: localhost:5432${NC}"
echo -e "${BLUE}🔴 Redis: localhost:6379${NC}"
echo -e "${BLUE}🍃 MongoDB: localhost:27017${NC}"
echo ""
echo -e "${YELLOW}💡 Use 'docker-compose ps' to check service status${NC}"
echo -e "${YELLOW}💡 Use 'docker-compose logs [service-name]' to view logs${NC}"
