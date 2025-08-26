#!/bin/bash

# Setup Script for Online MongoDB Connection
# This script sets up the environment for online MongoDB deployment

echo "🚀 Setting up Online MongoDB Connection for WFM System..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

echo "✅ Python3 found: $(python3 --version)"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip first."
    exit 1
fi

echo "✅ pip3 found: $(pip3 --version)"

# Install MongoDB Python driver with SRV support
echo "📦 Installing MongoDB Python driver with SRV support..."
pip3 install "pymongo[srv]"

if [ $? -eq 0 ]; then
    echo "✅ MongoDB Python driver installed successfully"
else
    echo "❌ Failed to install MongoDB Python driver"
    exit 1
fi

# Install additional dependencies
echo "📦 Installing additional dependencies..."
pip3 install python-dotenv dnspython

if [ $? -eq 0 ]; then
    echo "✅ Additional dependencies installed successfully"
else
    echo "❌ Failed to install additional dependencies"
    exit 1
fi

# Create .env.local from env.online template
if [ ! -f .env.local ]; then
    echo "📝 Creating .env.local from env.online template..."
    cp env.online .env.local
    echo "✅ .env.local created. Please update the backend URLs."
else
    echo "⚠️  .env.local already exists. Please check if it needs updates."
fi

echo ""
echo "🎉 Online MongoDB setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Update .env.local with your actual backend URLs"
echo "2. Test the MongoDB connection"
echo "3. Deploy your application"
echo ""
echo "🔗 MongoDB Connection String:"
echo "mongodb+srv://wfmadmin:tsarolabs@12345#@wfmdb.cvkb04l.mongodb.net/?retryWrites=true&w=majority&appName=wfmDB"
echo ""
echo "📚 Documentation: NEXTJS_INTEGRATION_GUIDE.md"
