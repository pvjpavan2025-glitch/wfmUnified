#!/usr/bin/env python3
"""
Integrated service startup script for WFM Services + wfmApp integration.
Starts all backend services and provides integration instructions.
"""

import subprocess
import time
import signal
import sys
import os
import json
import requests
from pathlib import Path
from datetime import datetime

# Service configurations
SERVICES = [
    {
        "name": "API Gateway",
        "script": "wfmServices/api_gateway/main.py",
        "port": 8000,
        "env_file": "wfmServices/env.online",
        "health_endpoint": "/health"
    },
    {
        "name": "Auth Service",
        "script": "wfmServices/auth_service/main.py",
        "port": 8001,
        "env_file": "wfmServices/env.online",
        "health_endpoint": "/health"
    },
    {
        "name": "Config Service",
        "script": "wfmServices/config_service/main.py",
        "port": 8002,
        "env_file": "wfmServices/env.online",
        "health_endpoint": "/health"
    },
    {
        "name": "Rules Service",
        "script": "wfmServices/rules_service/main.py",
        "port": 8003,
        "env_file": "wfmServices/env.online",
        "health_endpoint": "/health"
    },
    {
        "name": "Scheduler Service",
        "script": "wfmServices/scheduler_service/main.py",
        "port": 8004,
        "env_file": "wfmServices/env.online",
        "health_endpoint": "/health"
    },
    {
        "name": "Issue Service",
        "script": "wfmServices/issue_service/main.py",
        "port": 8005,
        "env_file": "wfmServices/env.online",
        "health_endpoint": "/health"
    },
    {
        "name": "Analytics Service",
        "script": "wfmServices/analytics_service/main.py",
        "port": 8006,
        "env_file": "wfmServices/env.online",
        "health_endpoint": "/health"
    }
]

class IntegratedServiceManager:
    """Manages starting and stopping of WFM services with wfmApp integration."""
    
    def __init__(self):
        self.processes = []
        self.running = True
        self.services_status = {}
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print(f"\n🛑 Received signal {signum}, shutting down services...")
        self.running = False
        self.stop_all_services()
        sys.exit(0)
    
    def start_service(self, service_config):
        """Start a single service."""
        try:
            # Set environment variables
            env = os.environ.copy()
            env["ENV_FILE"] = service_config["env_file"]
            
            # Start the service
            process = subprocess.Popen(
                [sys.executable, service_config["script"]],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.processes.append({
                "name": service_config["name"],
                "process": process,
                "port": service_config["port"],
                "config": service_config
            })
            
            print(f"🚀 Started {service_config['name']} on port {service_config['port']} (PID: {process.pid})")
            return process
            
        except Exception as e:
            print(f"❌ Failed to start {service_config['name']}: {str(e)}")
            return None
    
    def start_all_services(self):
        """Start all services."""
        print("🚀 Starting WFM Services with Online Database Configuration...")
        print("=" * 70)
        
        for service_config in SERVICES:
            if not self.running:
                break
            
            process = self.start_service(service_config)
            if process:
                # Wait a bit between starting services
                time.sleep(3)
        
        print("\n✅ All services started!")
        print("📊 Services are running on the following ports:")
        for service in self.processes:
            print(f"  - {service['name']}: http://localhost:{service['port']}")
        
        print(f"\n🌐 API Gateway: http://localhost:8000")
        print("🔍 Health Check: http://localhost:8000/health")
        print("📋 Services Health: http://localhost:8000/health/services")
        
        print("\n⏳ Waiting for services to be ready...")
        time.sleep(8)
        
        # Check service health
        self.check_services_health()
        
        # Show integration instructions
        self.show_integration_instructions()
    
    def check_services_health(self):
        """Check health of all services."""
        print("\n🔍 Checking Service Health...")
        
        for service in self.processes:
            try:
                response = requests.get(
                    f"http://localhost:{service['port']}{service['config']['health_endpoint']}", 
                    timeout=5.0
                )
                if response.status_code == 200:
                    print(f"✅ {service['name']} is healthy")
                    self.services_status[service['name']] = "healthy"
                else:
                    print(f"⚠️ {service['name']} returned status {response.status_code}")
                    self.services_status[service['name']] = f"status_{response.status_code}"
            except Exception as e:
                print(f"❌ {service['name']} health check failed: {str(e)}")
                self.services_status[service['name']] = "unhealthy"
    
    def show_integration_instructions(self):
        """Show integration instructions for wfmApp."""
        print("\n" + "=" * 70)
        print("🔗 WFM SERVICES + WFMAPP INTEGRATION INSTRUCTIONS")
        print("=" * 70)
        
        print("\n📱 Frontend (wfmApp) Setup:")
        print("1. Navigate to wfmApp directory:")
        print("   cd wfmApp")
        
        print("\n2. Install dependencies:")
        print("   npm install")
        print("   # or")
        print("   yarn install")
        
        print("\n3. Create .env.local file with backend URLs:")
        print("   cp env.online .env.local")
        print("   # Update .env.local with:")
        print("   NEXT_PUBLIC_AUTH_SERVICE_URL=http://localhost:8000")
        print("   NEXT_PUBLIC_API_GATEWAY_URL=http://localhost:8000")
        
        print("\n4. Start the Next.js development server:")
        print("   npm run dev")
        print("   # or")
        print("   yarn dev")
        
        print("\n🌐 Frontend will be available at: http://localhost:3000")
        
        print("\n🔧 Backend Services Status:")
        for service_name, status in self.services_status.items():
            status_icon = "✅" if status == "healthy" else "⚠️" if "status_" in status else "❌"
            print(f"   {status_icon} {service_name}: {status}")
        
        print("\n📡 API Endpoints Available:")
        print("   - Authentication: http://localhost:8000/auth/*")
        print("   - Users: http://localhost:8000/users/*")
        print("   - Configs: http://localhost:8000/configs/*")
        print("   - Rules: http://localhost:8000/rules/*")
        print("   - Jobs: http://localhost:8000/jobs/*")
        print("   - Issues: http://localhost:8000/issues/*")
        print("   - Reports: http://localhost:8000/reports/*")
        print("   - Metrics: http://localhost:8000/metrics/*")
        
        print("\n🧪 Testing Integration:")
        print("   - Health Check: curl http://localhost:8000/health")
        print("   - Services Health: curl http://localhost:8000/health/services")
        print("   - Frontend: Open http://localhost:3000 in browser")
        
        print("\n📝 Next Steps:")
        print("   1. Start wfmApp frontend (npm run dev)")
        print("   2. Test API endpoints with curl or Postman")
        print("   3. Test frontend-backend integration")
        print("   4. Use the comprehensive test script: python3 test_online_endpoints.py")
        
        print("\n" + "=" * 70)
    
    def stop_all_services(self):
        """Stop all running services."""
        print("\n🛑 Stopping all services...")
        
        for service in self.processes:
            try:
                process = service["process"]
                if process.poll() is None:  # Process is still running
                    process.terminate()
                    print(f"🛑 Terminated {service['name']} (PID: {process.pid})")
                    
                    # Wait for graceful shutdown
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        print(f"💀 Force killed {service['name']} (PID: {process.pid})")
                        
            except Exception as e:
                print(f"⚠️ Error stopping {service['name']}: {str(e)}")
        
        self.processes.clear()
        print("✅ All services stopped")
    
    def monitor_services(self):
        """Monitor running services."""
        print("\n📊 Monitoring Services (Press Ctrl+C to stop)...")
        
        try:
            while self.running:
                # Check if any services have stopped unexpectedly
                for service in self.processes[:]:  # Copy list to avoid modification during iteration
                    process = service["process"]
                    if process.poll() is not None:
                        print(f"⚠️ {service['name']} stopped unexpectedly (exit code: {process.returncode})")
                        self.processes.remove(service)
                
                if not self.processes:
                    print("❌ All services have stopped")
                    break
                
                time.sleep(10)
                
        except KeyboardInterrupt:
            print("\n🛑 Received interrupt signal")
        finally:
            self.stop_all_services()

def create_wfmapp_env_file():
    """Create .env.local file for wfmApp with correct backend URLs."""
    env_content = """# WFM App Environment Configuration
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
"""
    
    env_file_path = Path("wfmApp/.env.local")
    try:
        with open(env_file_path, "w") as f:
            f.write(env_content)
        print(f"✅ Created {env_file_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to create {env_file_path}: {str(e)}")
        return False

def main():
    """Main function."""
    # Check if we're in the right directory
    if not Path("wfmServices").exists() or not Path("wfmApp").exists():
        print("❌ Error: Please run this script from the root directory containing both wfmServices and wfmApp")
        sys.exit(1)
    
    # Check if wfmServices/env.online exists
    if not Path("wfmServices/env.online").exists():
        print("❌ Error: wfmServices/env.online file not found")
        sys.exit(1)
    
    print("🚀 WFM Services + wfmApp Integration Setup")
    print("=" * 50)
    
    # Create wfmApp environment file
    create_wfmapp_env_file()
    
    manager = IntegratedServiceManager()
    
    try:
        manager.start_all_services()
        manager.monitor_services()
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        manager.stop_all_services()
        sys.exit(1)

if __name__ == "__main__":
    main()
