#!/bin/bash

# WFM Unified System Stop Script
# This script stops all services gracefully

set -e

echo "🛑 Stopping WFM Unified System..."
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Stop all services
echo -e "${BLUE}🛑 Stopping all WFM services...${NC}"
docker-compose down --remove-orphans

echo -e "${GREEN}✅ All WFM services stopped successfully${NC}"

# Clean up any remaining containers
echo -e "${BLUE}🧹 Cleaning up any remaining containers...${NC}"
docker container prune -f

# Clean up any remaining networks
echo -e "${BLUE}🧹 Cleaning up any remaining networks...${NC}"
docker network prune -f

echo ""
echo -e "${GREEN}🎉 WFM Unified System stopped successfully!${NC}"
echo "=================================="
echo -e "${YELLOW}💡 All services have been stopped and cleaned up${NC}"
echo -e "${YELLOW}💡 Use 'docker ps' to verify no containers are running${NC}"
echo -e "${YELLOW}💡 Use 'start-wfm.sh' to start the system again${NC}"
