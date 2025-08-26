# Online MongoDB Setup Guide for WFM System

This guide explains how to set up and use the online MongoDB Atlas cluster for the WFM (Workforce Management) system.

## 🌐 MongoDB Atlas Cluster Details

### Connection Information
- **Cluster URL**: `wfmdb.cvkb04l.mongodb.net`
- **Username**: `wfmadmin`
- **Password**: `tsarolabs@12345#`
- **Database Name**: `wfm`
- **App Name**: `wfmDB`

### Connection String
```
mongodb+srv://wfmadmin:tsarolabs@12345#@wfmdb.cvkb04l.mongodb.net/?retryWrites=true&w=majority&appName=wfmDB
```

## 🚀 Quick Setup

### 1. Install Dependencies
```bash
# Install MongoDB Python driver with SRV support
python -m pip install "pymongo[srv]"

# Install additional dependencies
pip install python-dotenv dnspython
```

### 2. Run Setup Script
```bash
# Make script executable (if not already)
chmod +x unwanted/setup-online-mongo.sh

# Run setup script
./unwanted/setup-online-mongo.sh
```

This script will prompt for your MongoDB connection details and create the necessary configuration files.

### 3. Test Connection
```bash
# Test MongoDB connection
python3 tests/test-online-mongo.py
```

If the connection is successful, you will see a confirmation message.

## 📁 Files Created

### Environment Configuration
- `env.online` - Template for online MongoDB configuration
- `requirements-online.txt` - Python dependencies for online deployment

### Setup Scripts
- `unwanted/setup-online-mongo.sh` - Automated setup script
- `tests/test-online-mongo.py` - Connection testing script

## 🔧 Manual Setup

### 1. Create Environment File
Copy `env.online` to `.env.local`:
```bash
cp env.online .env.local
```

### 2. Update Backend URLs
Edit `.env.local` and update the backend service URLs:
```bash
# Update these with your actual backend URLs
NEXT_PUBLIC_AUTH_SERVICE_URL=https://your-backend-domain.com
NEXT_PUBLIC_API_GATEWAY_URL=https://your-backend-domain.com
```

### 3. Install Python Dependencies
```bash
# Install from requirements file
pip install -r requirements-online.txt

# Or install manually
pip install "pymongo[srv]" python-dotenv dnspython
```

## 🧪 Testing the Connection

### Python Test Script
```bash
python3 tests/test-online-mongo.py
```

### Expected Output
```
🚀 WFM Online MongoDB Connection Test
==================================================
✅ PyMongo version: 4.x.x

🔍 Testing Online MongoDB Connection...
📍 Cluster: wfmdb.cvkb04l.mongodb.net
👤 Username: wfmadmin
🗄️  Database: wfm

⏳ Attempting to connect...
✅ Successfully connected to MongoDB Atlas!
📊 Available databases: ['admin', 'wfm', ...]
📁 Collections in 'wfm': ['users', 'roles', 'tenants', ...]
✅ Insert test successful: [ObjectId]
✅ Find test successful: {...}
✅ Cleanup test successful
🔒 Connection closed successfully

🎉 All tests passed! MongoDB connection is working.
```

## 🔒 Security Considerations

### SSL/TLS
- MongoDB Atlas uses SSL/TLS by default
- The connection string includes SSL parameters
- Certificate verification is disabled for testing (use proper certificates in production)

### Authentication
- Username and password are stored in environment variables
- Never commit credentials to version control
- Use environment-specific configuration files

### Network Access
- MongoDB Atlas requires network access from your application
- Ensure your deployment environment can reach the cluster
- Consider IP whitelisting for additional security

## 🚀 Deployment

### Environment Variables
Set these environment variables in your deployment platform:

```bash
# MongoDB Connection
MONGODB_CONNECTION_STRING=mongodb+srv://wfmadmin:tsarolabs@12345#@wfmdb.cvkb04l.mongodb.net/?retryWrites=true&w=majority&appName=wfmDB

# Backend Services
NEXT_PUBLIC_AUTH_SERVICE_URL=https://your-backend-domain.com
NEXT_PUBLIC_API_GATEWAY_URL=https://your-backend-domain.com

# Environment
NODE_ENV=production
```

### Docker Deployment
If using Docker, add to your Dockerfile:
```dockerfile
# Install Python dependencies
RUN pip install "pymongo[srv]" python-dotenv dnspython

# Copy environment files
COPY env.online .env.local
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Connection Timeout
```
⏰ Server selection timeout: ...
```
**Solution**: Check network connectivity and firewall settings

#### 2. Authentication Failed
```
❌ Connection failed: Authentication failed
```
**Solution**: Verify username and password are correct

#### 3. SSL Certificate Issues
```
❌ SSL certificate verification failed
```
**Solution**: Ensure proper SSL configuration or use `ssl_cert_reqs=ssl.CERT_NONE` for testing

#### 4. PyMongo Not Installed
```
❌ PyMongo not installed
```
**Solution**: Run `pip install "pymongo[srv]"`

### Debug Mode
Enable debug logging in your application:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 Additional Resources

### Documentation
- [PyMongo Documentation](https://pymongo.readthedocs.io/)
- [MongoDB Atlas Documentation](https://docs.atlas.mongodb.com/)
- [Next.js Environment Variables](https://nextjs.org/docs/basic-features/environment-variables)

### Support
- Check the browser console for error messages
- Verify MongoDB Atlas cluster status
- Test connection with the provided Python script
- Review network and firewall configurations

## 🔄 Migration from Local to Online

### 1. Backup Local Data
```bash
# Export local MongoDB data
mongodump --db wfm --out ./backup
```

### 2. Update Configuration
- Change connection strings from localhost to Atlas cluster
- Update environment variables
- Test connection with new configuration

### 3. Import Data
```bash
# Import to Atlas cluster
mongorestore --uri "mongodb+srv://wfmadmin:tsarolabs@12345#@wfmdb.cvkb04l.mongodb.net/wfm" ./backup/wfm
```

## ✅ Checklist

- [ ] MongoDB Atlas cluster accessible
- [ ] Python dependencies installed
- [ ] Environment file configured
- [ ] Connection test successful
- [ ] Backend URLs updated
- [ ] Security settings configured
- [ ] Data migration completed (if applicable)
- [ ] Application tested with online database

## 🎯 Next Steps

1. **Test the connection** with the provided script
2. **Update your backend configuration** to use the online MongoDB
3. **Deploy your application** with the new configuration
4. **Monitor performance** and adjust connection settings as needed
5. **Set up monitoring** and alerting for the database cluster

---

**Note**: This setup is for development and testing. For production deployment, ensure proper security measures, monitoring, and backup strategies are in place.

### Test Credentials
Use these credentials to test the integration:

- **Tenant ID**: `6899df7293ed4ce8e63f574d`
- **Username**: `testuser`
- **Password**: `test123`
