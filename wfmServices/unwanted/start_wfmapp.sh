#!/bin/bash

# WFM App Frontend Startup Script

echo "🚀 Starting WFM App Frontend..."

# Check if we're in the right directory
if [ ! -d "wfmApp" ]; then
    echo "❌ Error: wfmApp directory not found. Please run this script from the root directory."
    exit 1
fi

# Navigate to wfmApp directory
cd wfmApp

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies"
        exit 1
    fi
fi

# Check if .env.local exists, if not create it
if [ ! -f ".env.local" ]; then
    echo "⚙️ Creating .env.local file..."
    cat > .env.local << EOF
# WFM App Environment Configuration
# Backend Service URLs (Local Development)
NEXT_PUBLIC_AUTH_SERVICE_URL=http://localhost:8000
NEXT_PUBLIC_API_GATEWAY_URL=http://localhost:8000
NODE_ENV=development

# MongoDB Online Connection Details
MONGO_USERNAME=wfmadmin
MONGO_PASSWORD=tsarolabs@12345#

# MongoDB Connection String
MONGODB_CONNECTION_STRING=mongodb+srv://wfmadmin:tsarolabs@12345#@wfmdb.cvkb04l.mongodb.net/?retryWrites=true&w=majority&appName=wfmDB

# Additional Configuration
MONGO_DB_NAME=wfm
MONGO_COLLECTION_USERS=users
MONGO_COLLECTION_ROLES=roles
MONGO_COLLECTION_TENANTS=tenants
EOF
    echo "✅ Created .env.local file"
fi

# Start the development server
echo "🌐 Starting Next.js development server..."
echo "📱 Frontend will be available at: http://localhost:3000"
echo "🔗 Backend services should be running on ports 8000-8006"
echo ""
echo "Press Ctrl+C to stop the frontend server"
echo ""

npm run dev
