# AutoTest Installation Guide

Complete installation instructions for AutoTest accessibility testing platform.

## System Requirements

### Minimum Requirements
- **Operating System**: Linux, macOS, or Windows 10+
- **Python**: Version 3.8 or higher
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 2GB free disk space
- **Database**: MongoDB 4.4+
- **Browser**: Chrome, Firefox, Safari, or Edge (for web interface)

### Recommended Configuration
- **CPU**: 4+ cores for optimal performance
- **Memory**: 8GB+ RAM for large website testing
- **Storage**: SSD recommended for better performance
- **Network**: Stable internet connection for website testing

## Prerequisites Installation

### Python Installation

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
python3 --version  # Should show 3.8+
```

#### macOS
```bash
# Using Homebrew
brew install python
python3 --version
```

#### Windows
1. Download Python from [python.org](https://python.org)
2. Run installer with "Add Python to PATH" checked
3. Verify installation: `python --version`

### MongoDB Installation

#### Linux (Ubuntu/Debian)
```bash
# Import MongoDB public key
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -

# Add MongoDB repository
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list

# Install MongoDB
sudo apt-get update
sudo apt-get install -y mongodb-org

# Start and enable MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod
sudo systemctl status mongod
```

#### macOS
```bash
# Using Homebrew
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb/brew/mongodb-community
```

#### Windows
1. Download MongoDB Community Server from [mongodb.com](https://mongodb.com)
2. Run the installer
3. Start MongoDB service from Services panel

### Git Installation
```bash
# Linux
sudo apt install git

# macOS
brew install git

# Windows - download from git-scm.com
```

## AutoTest Installation

### 1. Clone Repository
```bash
git clone https://github.com/bobdodd/autoTest.git
cd autoTest
```

### 2. Create Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate

# Windows:
venv\Scripts\activate

# Verify activation (should show venv path)
which python
```

### 3. Install Dependencies
```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Verify critical packages
python -c "import flask, pymongo, selenium; print('Dependencies OK')"
```

### 4. Configure Database
AutoTest uses MongoDB with default settings:
- **Host**: localhost
- **Port**: 27017
- **Database**: autotest (created automatically)

#### Custom Configuration (Optional)
Create `autotest/config.json`:
```json
{
    "database": {
        "mongodb_uri": "mongodb://localhost:27017/",
        "database_name": "autotest"
    },
    "server": {
        "host": "127.0.0.1",
        "port": 5000,
        "debug": true
    }
}
```

### 5. Initialize Application
```bash
# Test database connection
python -c "
from autotest.core.database import DatabaseConnection
from autotest.utils.config import Config
config = Config()
db = DatabaseConnection(config)
db.connect()
print('Database connection successful')
"
```

### 6. Start AutoTest
```bash
python -m autotest.web.app
```

You should see:
```
* Running on http://127.0.0.1:5000
* Debug mode: on
```

### 7. Verify Installation
1. Open browser to `http://localhost:5000`
2. You should see the AutoTest dashboard
3. All navigation links should work without errors

## Post-Installation Setup

### Browser Driver Setup
AutoTest uses Selenium WebDriver for testing. The Chrome driver is included, but you may need to update it:

```bash
# Check Chrome version
google-chrome --version  # Linux
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version  # macOS

# Update WebDriver if needed (handled automatically in most cases)
```

### Firewall Configuration
Ensure these ports are accessible:
- **5000**: AutoTest web interface
- **27017**: MongoDB (if accessing remotely)

### Performance Optimization

#### MongoDB Optimization
```javascript
// Connect to MongoDB
mongo

// Create indexes for better performance
use autotest
db.test_results.createIndex({"page_id": 1})
db.test_results.createIndex({"test_date": -1})
db.projects.createIndex({"project_id": 1})
db.scheduled_tests.createIndex({"schedule_id": 1})
```

#### System Limits
For high-volume testing, increase system limits:

```bash
# Linux - add to /etc/security/limits.conf
* soft nofile 65536
* hard nofile 65536

# Reload limits
ulimit -n 65536
```

## Docker Installation (Alternative)

### Docker Compose Setup
Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  mongodb:
    image: mongo:6.0
    container_name: autotest-mongo
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    environment:
      MONGO_INITDB_DATABASE: autotest

  autotest:
    build: .
    container_name: autotest-app
    ports:
      - "5000:5000"
    depends_on:
      - mongodb
    environment:
      - AUTOTEST_MONGODB_URI=mongodb://mongodb:27017/
    volumes:
      - ./logs:/app/logs

volumes:
  mongodb_data:
```

### Dockerfile
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 5000

# Start application
CMD ["python", "-m", "autotest.web.app"]
```

### Start with Docker
```bash
docker-compose up -d
```

## Production Deployment

### Security Considerations
1. **Change default ports** and use reverse proxy
2. **Enable authentication** (not included in v1.0)
3. **Use HTTPS** with proper SSL certificates
4. **Restrict database access** to application only
5. **Set up proper logging** and monitoring

### Reverse Proxy Configuration (Nginx)
```nginx
server {
    listen 80;
    server_name autotest.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Systemd Service (Linux)
Create `/etc/systemd/system/autotest.service`:
```ini
[Unit]
Description=AutoTest Accessibility Testing Platform
After=network.target mongod.service

[Service]
Type=simple
User=autotest
WorkingDirectory=/opt/autotest
Environment=PATH=/opt/autotest/venv/bin
ExecStart=/opt/autotest/venv/bin/python -m autotest.web.app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable autotest
sudo systemctl start autotest
sudo systemctl status autotest
```

## Troubleshooting Installation

### Common Issues

#### "Module not found" errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

#### MongoDB connection issues
```bash
# Check MongoDB status
sudo systemctl status mongod

# Check if port is listening
netstat -an | grep 27017

# Test connection
mongo --eval "db.adminCommand('ismaster')"
```

#### Permission errors
```bash
# Fix Python package permissions
sudo chown -R $USER:$USER venv/

# Fix MongoDB data directory
sudo chown -R mongodb:mongodb /var/lib/mongodb
```

#### Port conflicts
```bash
# Find what's using port 5000
lsof -i :5000

# Use different port
export AUTOTEST_PORT=5001
```

### Validation Commands
```bash
# Test all components
python -c "
import sys
print('Python:', sys.version)

import pymongo
client = pymongo.MongoClient()
print('MongoDB: Connected')

import selenium
print('Selenium: Available')

from autotest.web.app import create_app
print('AutoTest: Ready')
"
```

## Getting Help

### Log Files
Check these locations for troubleshooting:
- **Application logs**: Console output or configured log file
- **MongoDB logs**: `/var/log/mongodb/mongod.log`
- **System logs**: `journalctl -u autotest` (if using systemd)

### Support Resources
- **GitHub Issues**: Report installation problems
- **Documentation**: Complete user manual
- **Community**: Connect with other users

### Performance Testing
After installation, test with a small website:
```bash
# Run basic test
curl -X POST http://localhost:5000/api/testing/run \
  -H "Content-Type: application/json" \
  -d '{"project_id": "test", "test_type": "accessibility"}'
```

---

**Installation Complete!** Continue with the [Quick Start Guide](QUICK_START.md) to run your first accessibility test.

*Installation Guide - AutoTest Version 1.0*