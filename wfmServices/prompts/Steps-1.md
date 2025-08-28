1. Create new environment:
python3 -m venv wfmv4

2. Activate the environment:
source wfmv4/bin/activate

3. Install the requirements:
pip install -r requirements.txt

4. Start the infra:
docker-compose -f docker-compose.wfmv4.yml up -d

5. Check for Infra:
docker ps

6. Copy the env file:
cp .env.example .env

7. Start the services:
source wfmv4/bin/activate && python -m api_gateway.main
source wfmv4/bin/activate && python -m auth_service.main
source wfmv4/bin/activate && python -m config_service.main
source wfmv4/bin/activate && python -m rules_service.main
source wfmv4/bin/activate && python -m scheduler_service.main
source wfmv4/bin/activate && python -m issue_service.main

8. Check if all the services are running:
sleep 5 && curl -s http://localhost:8000/health | head -20

9. Check if APi Gateway is running:
curl -s http://localhost:8000/health/services

10. Check what is running on the ports:
lsof -i :8000-8010

11. Check what endpoints are available:
curl -s http://localhost:8001/docs

12. Check ports specifically:
netstat -an | grep LISTEN | grep 800

13. Check Auth service endpoints:
curl -s http://localhost:8001/openapi.json | jq '.paths | keys' 2>/dev/null || curl -s http://localhost:8001/openapi.json  (OR) curl -s http://localhost:8000/openapi.json | jq '.paths | keys' 2>/dev/null || echo "Checking auth endpoints..."

14. Check which service is running on which port by testing the health endpoints:
for port in 8001 8002 8003 8004 8005 8006; do echo "Port $port:"; curl -s http://localhost:$port/health 2>/dev/null || echo "No response"; echo; done

15. Check if DB is initialized properly:
docker exec wfmv4_mongodb mongosh --username admin --password password --authenticationDatabase admin wfmv4 --eval "db.users.find().pretty()"

16. Create the wfmv4 database and create collections - Optional step - for documentation only:
docker exec wfmv4_mongodb mongosh --username admin --password password --authenticationDatabase admin --eval "use wfmv4; db.createCollection('users'); db.createCollection('roles'); db.createCollection('permissions'); db.createCollection('tenants')"

17. Copy the initialization script to the new database:
docker exec wfmv4_mongodb mongosh --username admin --password password --authenticationDatabase admin wfmv4 < scripts/init-mongo.js

18. Manually create the admin user:
docker exec wfmv4_mongodb mongosh --username admin --password password --authenticationDatabase admin wfmv4 --eval "db.users.insertOne({username: 'admin', email: 'admin@wfm.local', password_hash: '\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3bp.gJZQmO', first_name: 'Admin', last_name: 'User', tenant_id: 'default', role_ids: [], status: 'ACTIVE', created_at: new Date(), updated_at: new Date()})"

19. Create default tenant:
docker exec wfmv4_mongodb mongosh --username admin --password password --authenticationDatabase admin wfmv4 --eval "db.tenants.insertOne({name: 'Default Tenant', domain: 'default', status: 'ACTIVE', settings: {}, created_at: new Date(), updated_at: new Date()})"

20. Optional Steps:
    i. Check the password hash:
    python3 -c "import bcrypt; print(bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt(12)).decode('utf-8'))"

    ii. Update the user with the correct password hash:
    docker exec wfmv4_mongodb mongosh --username admin --password password --authenticationDatabase admin wfmv4 --eval "db.users.updateOne({username: 'admin'}, {\$set: {password_hash: '\$2b\$12\$JyIXw4mHLjnY96MZ1lbNIediLKVdznD3NZ5Vt5.kyhzTBMPvnZV26'}})"

21. Start all the services and run the demonstration:
source wfmv4/bin/activate && python -m rules_service.main --port 8003 &
source wfmv4/bin/activate && python -m scheduler_service.main --port 8004 &
source wfmv4/bin/activate && python -m issue_service.main --port 8005 &
source wfmv4/bin/activate && python -m analytics_service.main --port 8006 &
source wfmv4/bin/activate && python working_demo.py
source wfmv4/bin/activate && python final_demo.py