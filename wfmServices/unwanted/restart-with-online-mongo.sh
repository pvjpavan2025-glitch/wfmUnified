#!/bin/bash

# Script to restart backend services with online MongoDB configuration
echo "🚀 Restarting WFM Backend Services with Online MongoDB..."

# Stop current services
echo "⏹️  Stopping current services..."
docker-compose down

# Wait a moment for services to stop
sleep 3

# Start services with new configuration
echo "▶️  Starting services with online MongoDB configuration..."
docker-compose up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# Check service status
echo "📊 Checking service status..."
docker-compose ps

# Test backend health
echo "🔍 Testing backend health..."
sleep 5

if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend services are healthy!"
    echo ""
    echo "🎉 Backend successfully updated to use online MongoDB Atlas!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Test authentication: cd ../wfmApp && python3 tests/test-complete-integration.py"
    echo "2. Test frontend login: http://localhost:3001/login"
    echo "3. Use credentials: testuser / test123 / 6899df7293ed4ce8e63f574d"
else
    echo "❌ Backend services are not responding. Check logs with:"
    echo "   docker-compose logs"
fi
