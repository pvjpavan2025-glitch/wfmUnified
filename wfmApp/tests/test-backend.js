#!/usr/bin/env node

/**
 * Simple test script to verify backend connectivity for Next.js project
 * Run this script to test if the backend services are accessible
 */

const https = require('https');
const http = require('http');

const services = [
  { name: 'API Gateway', url: 'http://localhost:8000/health', port: 8000 },
];

async function testService(service) {
  return new Promise((resolve) => {
    const client = service.url.startsWith('https:') ? https : http;
    
    const req = client.get(service.url, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const response = JSON.parse(data);
          resolve({
            name: service.name,
            status: '✅ Connected',
            port: service.port,
            response: response
          });
        } catch (e) {
          resolve({
            name: service.name,
            status: '⚠️  Connected (Invalid JSON)',
            port: service.port,
            response: data
          });
        }
      });
    });

    req.on('error', (err) => {
      resolve({
        name: service.name,
        status: '❌ Failed',
        port: service.port,
        error: err.message
      });
    });

    req.setTimeout(5000, () => {
      req.destroy();
      resolve({
        name: service.name,
        status: '⏰ Timeout',
        port: service.port,
        error: 'Request timeout after 5 seconds'
      });
    });
  });
}

async function testAllServices() {
  console.log('🔍 Testing Backend Services Connectivity for Next.js Project...\n');
  
  const results = await Promise.all(services.map(testService));
  
  results.forEach(result => {
    console.log(`${result.status} ${result.name} (Port ${result.port})`);
    if (result.response) {
      console.log(`   Response: ${JSON.stringify(result.response)}`);
    }
    if (result.error) {
      console.log(`   Error: ${result.error}`);
    }
    console.log('');
  });

  const allConnected = results.every(r => r.status.includes('✅'));
  
  if (allConnected) {
    console.log('🎉 API Gateway is running! Next.js frontend should be able to connect.');
    console.log('\nNext steps:');
    console.log('1. Start the Next.js frontend: npm run dev');
    console.log('2. Navigate to http://localhost:3000/login');
    console.log('3. Test authentication with these credentials:');
    console.log('   - Tenant ID: 6899bf83022ff0e94574e39a');
    console.log('   - Username: testuser');
    console.log('   - Password: test123');
  } else {
    console.log('⚠️  API Gateway is not accessible. Please check:');
    console.log('1. Are the backend services running? (docker-compose up -d)');
    console.log('2. Is port 8000 accessible?');
    console.log('3. Are there any firewall/network issues?');
  }
}

// Run the test
testAllServices().catch(console.error);
