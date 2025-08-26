#!/usr/bin/env python3
"""
Startup script for WFM services with online database configuration.
"""

import subprocess
import time
import signal
import sys
import os
from pathlib import Path

# Service configurations
SERVICES = [
    {
        "name": "API Gateway",
        "script": "api_gateway/main.py",
        "port": 8000,
        "env_file": "env.online"
    },
    {
        "name": "Auth Service",
        "script": "auth_service/main.py",
        "port": 8001,
        "env_file": "env.online"
    },
    {
        "name": "Config Service",
        "script": "config_service/main.py",
        "port": 8002,
        "env_file": "env.online"
    },
    {
        "name": "Rules Service",
        "script": "rules_service/main.py",
        "port": 8003,
        "env_file": "env.online"
    },
    {
        "name": "Scheduler Service",
        "script": "scheduler_service/main.py",
        "port": 8004,
        "env_file": "env.online"
    },
    {
        "name": "Issue Service",
        "script": "issue_service/main.py",
        "port": 8005,
        "env_file": "env.online"
    },
    {
        "name": "Analytics Service",
        "script": "analytics_service/main.py",
        "port": 8006,
        "env_file": "env.online"
    }
]

class ServiceManager:
    """Manages starting and stopping of WFM services."""
    
    def __init__(self):
        self.processes = []
        self.running = True
        
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
                "port": service_config["port"]
            })
            
            print(f"🚀 Started {service_config['name']} on port {service_config['port']} (PID: {process.pid})")
            return process
            
        except Exception as e:
            print(f"❌ Failed to start {service_config['name']}: {str(e)}")
            return None
    
    def start_all_services(self):
        """Start all services."""
        print("🚀 Starting WFM Services with Online Database Configuration...")
        print("=" * 60)
        
        for service_config in SERVICES:
            if not self.running:
                break
            
            process = self.start_service(service_config)
            if process:
                # Wait a bit between starting services
                time.sleep(2)
        
        print("\n✅ All services started!")
        print("📊 Services are running on the following ports:")
        for service in self.processes:
            print(f"  - {service['name']}: http://localhost:{service['port']}")
        
        print(f"\n🌐 API Gateway: http://localhost:8000")
        print("🔍 Health Check: http://localhost:8000/health")
        print("📋 Services Health: http://localhost:8000/health/services")
        
        print("\n⏳ Waiting for services to be ready...")
        time.sleep(5)
        
        # Check service health
        self.check_services_health()
    
    def check_services_health(self):
        """Check health of all services."""
        print("\n🔍 Checking Service Health...")
        
        import httpx
        import asyncio
        
        async def check_health():
            async with httpx.AsyncClient() as client:
                for service in self.processes:
                    try:
                        response = await client.get(f"http://localhost:{service['port']}/health", timeout=5.0)
                        if response.status_code == 200:
                            print(f"✅ {service['name']} is healthy")
                        else:
                            print(f"⚠️ {service['name']} returned status {response.status_code}")
                    except Exception as e:
                        print(f"❌ {service['name']} health check failed: {str(e)}")
        
        try:
            asyncio.run(check_health())
        except Exception as e:
            print(f"⚠️ Health check failed: {str(e)}")
    
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
                
                time.sleep(5)
                
        except KeyboardInterrupt:
            print("\n🛑 Received interrupt signal")
        finally:
            self.stop_all_services()

def main():
    """Main function."""
    # Check if we're in the right directory
    if not Path("shared").exists():
        print("❌ Error: Please run this script from the wfmv4 directory")
        sys.exit(1)
    
    # Check if env.online exists
    if not Path("env.online").exists():
        print("❌ Error: env.online file not found")
        sys.exit(1)
    
    manager = ServiceManager()
    
    try:
        manager.start_all_services()
        manager.monitor_services()
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        manager.stop_all_services()
        sys.exit(1)

if __name__ == "__main__":
    main()
