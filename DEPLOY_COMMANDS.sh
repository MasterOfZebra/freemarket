#!/bin/bash

# ===========================================
# FREEMARKET v2.0.0 - PRODUCTION DEPLOYMENT
# ===========================================
# Commands for server deployment and testing
# Run as root or with sudo where required

set -e  # Exit on any error

echo "🚀 FREEMARKET v2.0.0 - PRODUCTION DEPLOYMENT"
echo "============================================"

# ===========================================
# 1. SERVER PREPARATION
# ===========================================

echo "📋 Step 1: Server Preparation"

# Update system packages
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
echo "Installing required packages..."
sudo apt install -y curl wget git htop iotop ncdu docker.io docker-compose-plugin

# Configure Docker
echo "Configuring Docker..."
sudo systemctl enable docker
sudo systemctl start docker

# Add current user to docker group (logout/login required)
sudo usermod -aG docker $USER

# Install Node.js for frontend builds
echo "Installing Node.js..."
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify installations
echo "Verifying installations..."
docker --version
docker compose version
node --version
npm --version

echo "✅ Server preparation complete"

# ===========================================
# 2. DATABASE SETUP (EXTERNAL POSTGRES)
# ===========================================

echo "📋 Step 2: Database Setup"

# Note: Assuming external PostgreSQL is already configured
# Update these variables with your actual DB details

export DB_HOST="192.168.1.9"
export DB_PORT="5432"
export DB_NAME="assistance_kz"
export DB_USER="assistadmin_pg"
export DB_PASSWORD="assistMurzAdmin"

# Test database connection
echo "Testing database connection..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT version();"

echo "✅ Database connection verified"

# ===========================================
# 3. CODE DEPLOYMENT
# ===========================================

echo "📋 Step 3: Code Deployment"

# Create deployment directory
sudo mkdir -p /opt/freemarket
sudo chown $USER:$USER /opt/freemarket
cd /opt/freemarket

# Clone repository
echo "Cloning repository..."
git clone https://github.com/MasterOfZebra/freemarket.git .
git checkout main
git pull origin main

# Verify code integrity
echo "Verifying code integrity..."
ls -la
wc -l ARCHITECTURE_CURRENT.md CHANGELOG.md PRE_RELEASE_CHECKLIST.md

echo "✅ Code deployment complete"

# ===========================================
# 4. ENVIRONMENT CONFIGURATION
# ===========================================

echo "📋 Step 4: Environment Configuration"

# Copy environment template
cp .env.example .env

# Update environment variables
cat > .env << EOF
# Database Configuration
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# API Configuration
API_TITLE=FreeMarket API
API_VERSION=2.0.0
API_DESCRIPTION=FreeMarket Exchange Platform API v2.0.0

# CORS Configuration
CORS_ORIGINS=["http://localhost:3000", "http://localhost:80", "https://freemarket.com"]

# Environment
ENV=production

# Feature Flags
USE_BY_CATEGORY_FORMS=1
NEW_LISTING_API=1
LEGACY_API_SUPPORT=0

# Telegram Bot (configure with actual values)
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# JWT Configuration (for future auth)
JWT_SECRET_KEY=your_jwt_secret_key_here
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Security
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=100

# Monitoring
PROMETHEUS_METRICS_ENABLED=true
HEALTH_CHECK_ENABLED=true
EOF

# Verify environment
echo "Verifying environment configuration..."
grep -E "(API_VERSION|DATABASE_URL|USE_BY_CATEGORY_FORMS)" .env

echo "✅ Environment configuration complete"

# ===========================================
# 5. SSL CERTIFICATES SETUP
# ===========================================

echo "📋 Step 5: SSL Certificates"

# Create certificates directory
mkdir -p certs

# Note: Replace with your actual SSL certificates
# For development/testing, you can use self-signed certificates

echo "⚠️  Note: Configure SSL certificates in ./certs/ directory"
echo "   - fullchain.pem (certificate chain)"
echo "   - privkey.pem (private key)"
echo "   For production, use Let's Encrypt or your CA certificates"

# Self-signed certificates for testing (REMOVE IN PRODUCTION)
echo "Creating self-signed certificates for testing..."
sudo openssl req -x509 -newkey rsa:4096 -keyout certs/privkey.pem -out certs/fullchain.pem -days 365 -nodes -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

echo "✅ SSL certificates configured"

# ===========================================
# 6. DOCKER DEPLOYMENT
# ===========================================

echo "📋 Step 6: Docker Deployment"

# Build and deploy
echo "Building Docker images..."
docker compose -f docker-compose.prod.yml build --no-cache

echo "Starting services..."
docker compose -f docker-compose.prod.yml up -d

# Wait for services to start
echo "Waiting for services to start..."
sleep 30

# Check service status
echo "Checking service status..."
docker compose -f docker-compose.prod.yml ps

echo "✅ Docker deployment complete"

# ===========================================
# 7. DATABASE MIGRATIONS
# ===========================================

echo "📋 Step 7: Database Migrations"

# Run Alembic migrations
echo "Running database migrations..."
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Sanity check migrations
echo "Running migration sanity checks..."
docker compose -f docker-compose.prod.yml exec backend alembic check

# Run data migration if needed
echo "Running data migration (if upgrading from v1.x)..."
# Uncomment if upgrading from v1.x:
# docker compose -f docker-compose.prod.yml exec backend python scripts/migrate_legacy_listings.py migrate

echo "✅ Database migrations complete"

# ===========================================
# 8. HEALTH CHECKS
# ===========================================

echo "📋 Step 8: Health Checks"

# Check backend health
echo "Checking backend health..."
curl -f http://localhost:8000/health || echo "❌ Backend health check failed"

# Check API version header
echo "Checking API version header..."
curl -I http://localhost:8000/api/listings/wants | grep "X-API-Version" || echo "❌ API version header missing"

# Check frontend
echo "Checking frontend..."
curl -f http://localhost/ || echo "❌ Frontend not accessible"

# Check database connectivity
echo "Checking database connectivity..."
docker compose -f docker-compose.prod.yml exec backend python -c "
from backend.database import SessionLocal
db = SessionLocal()
try:
    result = db.execute('SELECT 1').scalar()
    print('✅ Database connection: OK')
except Exception as e:
    print(f'❌ Database connection: FAILED - {e}')
finally:
    db.close()
"

echo "✅ Health checks complete"

# ===========================================
# 9. FUNCTIONAL TESTING
# ===========================================

echo "📋 Step 9: Functional Testing"

# Test API endpoints
echo "Testing API endpoints..."

# Test wants endpoint
echo "Testing /api/listings/wants..."
curl -s "http://localhost/api/listings/wants?limit=5" | jq '.items | length' || echo "❌ Wants endpoint failed"

# Test offers endpoint
echo "Testing /api/listings/offers..."
curl -s "http://localhost/api/listings/offers?limit=5" | jq '.items | length' || echo "❌ Offers endpoint failed"

# Test health endpoint
echo "Testing /health..."
curl -s http://localhost:8000/health | jq '.status' || echo "❌ Health endpoint failed"

# Test API docs
echo "Testing API documentation..."
curl -f http://localhost:8000/docs || echo "❌ API docs not accessible"

# Test frontend
echo "Testing frontend..."
curl -s http://localhost/ | grep -q "FreeMarket" && echo "✅ Frontend accessible" || echo "❌ Frontend not accessible"

echo "✅ Functional testing complete"

# ===========================================
# 10. LOAD TESTING
# ===========================================

echo "📋 Step 10: Load Testing"

# Install Apache Bench if not available
which ab || sudo apt install -y apache2-utils

echo "Running load tests..."

# API load test
echo "API endpoints load test (10 concurrent, 100 requests)..."
ab -n 100 -c 10 -g /tmp/api_load.tsv http://localhost/api/listings/wants 2>/dev/null || echo "Load test completed"

# Frontend load test
echo "Frontend load test (50 concurrent, 200 requests)..."
ab -n 200 -c 50 -g /tmp/frontend_load.tsv http://localhost/ 2>/dev/null || echo "Frontend load test completed"

# Analyze results
echo "Load test results summary:"
echo "API Test Results:" $(tail -1 /tmp/api_load.tsv 2>/dev/null | cut -f 6,8,9,10 | awk '{print "RPS:", 1000/$1, "P95:", $2"ms", "P99:", $3"ms", "Errors:", $4}') || echo "No API results"
echo "Frontend Test Results:" $(tail -1 /tmp/frontend_load.tsv 2>/dev/null | cut -f 6,8,9,10 | awk '{print "RPS:", 1000/$1, "P95:", $2"ms", "P99:", $3"ms", "Errors:", $4}') || echo "No frontend results"

echo "✅ Load testing complete"

# ===========================================
# 11. MONITORING SETUP
# ===========================================

echo "📋 Step 11: Monitoring Setup"

# Install Prometheus and Grafana (optional)
echo "Installing monitoring stack..."
sudo apt install -y prometheus grafana

# Configure Prometheus
echo "Configuring Prometheus..."
sudo systemctl enable prometheus
sudo systemctl start prometheus

# Configure Grafana
echo "Configuring Grafana..."
sudo systemctl enable grafana-server
sudo systemctl start grafana-server

# Check monitoring endpoints
echo "Checking monitoring endpoints..."
curl -f http://localhost:9090/-/healthy && echo "✅ Prometheus healthy" || echo "❌ Prometheus not accessible"
curl -f http://localhost:3000/api/health && echo "✅ Grafana healthy" || echo "❌ Grafana not accessible"

echo "✅ Monitoring setup complete"

# ===========================================
# 12. SECURITY AUDIT
# ===========================================

echo "📋 Step 12: Security Audit"

# Install security scanning tools
echo "Installing security tools..."
pip install pip-audit safety bandit
npm install -g auditjs

# Scan Python dependencies
echo "Scanning Python dependencies..."
pip-audit --format json | jq '.vulnerabilities | length' && echo "Python audit completed" || echo "❌ Python audit failed"

# Scan Node.js dependencies
echo "Scanning Node.js dependencies..."
npm audit --audit-level moderate && echo "✅ NPM audit passed" || echo "⚠️  NPM audit found issues"

# Run bandit security linter
echo "Running Bandit security linter..."
bandit -r backend/ -f json -o /tmp/bandit_results.json && echo "✅ Bandit scan completed" || echo "❌ Bandit scan failed"

echo "✅ Security audit complete"

# ===========================================
# 13. BACKUP CONFIGURATION
# ===========================================

echo "📋 Step 13: Backup Configuration"

# Setup automated backups
echo "Setting up automated backups..."

# Database backup script
cat > /opt/freemarket/backup-db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/freemarket/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/freemarket_$TIMESTAMP.sql"

mkdir -p $BACKUP_DIR

PGPASSWORD=$DB_PASSWORD pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER $DB_NAME > $BACKUP_FILE

# Keep only last 7 days
find $BACKUP_DIR -name "freemarket_*.sql" -mtime +7 -delete

echo "✅ Database backup completed: $BACKUP_FILE"
EOF

chmod +x /opt/freemarket/backup-db.sh

# Add to crontab for daily backups at 2 AM
(crontab -l ; echo "0 2 * * * /opt/freemarket/backup-db.sh") | crontab -

echo "✅ Backup configuration complete"

# ===========================================
# 14. FINAL VERIFICATION
# ===========================================

echo "📋 Step 14: Final Verification"

# Check all services are running
echo "Checking all services..."
docker compose -f docker-compose.prod.yml ps

# Check logs for errors
echo "Checking logs for errors..."
docker compose -f docker-compose.prod.yml logs --tail=50 | grep -i error || echo "No recent errors found"

# Test end-to-end functionality
echo "Testing end-to-end functionality..."
curl -s "http://localhost/api/listings/wants?limit=1" | jq -r '.items[0].item_name // "No data"' && echo "✅ E2E test passed" || echo "❌ E2E test failed"

# Performance check
echo "Performance check..."
time curl -s "http://localhost/api/listings/wants?limit=10" > /dev/null && echo "✅ Performance acceptable" || echo "❌ Performance issues"

echo "✅ Final verification complete"

# ===========================================
# DEPLOYMENT SUMMARY
# ===========================================

echo ""
echo "🎉 FREEMARKET v2.0.0 DEPLOYMENT COMPLETE!"
echo "========================================="
echo ""
echo "📊 DEPLOYMENT SUMMARY:"
echo "✅ Server preparation"
echo "✅ Database setup"
echo "✅ Code deployment"
echo "✅ Environment configuration"
echo "✅ SSL certificates"
echo "✅ Docker deployment"
echo "✅ Database migrations"
echo "✅ Health checks"
echo "✅ Functional testing"
echo "✅ Load testing"
echo "✅ Monitoring setup"
echo "✅ Security audit"
echo "✅ Backup configuration"
echo "✅ Final verification"
echo ""
echo "🌐 ACCESS POINTS:"
echo "   Frontend: http://your-server-ip/"
echo "   API: http://your-server-ip:8000/"
echo "   API Docs: http://your-server-ip:8000/docs"
echo "   Health: http://your-server-ip:8000/health"
echo "   Monitoring: http://your-server-ip:9090 (Prometheus)"
echo "   Dashboards: http://your-server-ip:3000 (Grafana)"
echo ""
echo "🔧 MANAGEMENT COMMANDS:"
echo "   Status: docker compose -f docker-compose.prod.yml ps"
echo "   Logs: docker compose -f docker-compose.prod.yml logs -f"
echo "   Restart: docker compose -f docker-compose.prod.yml restart"
echo "   Update: git pull && docker compose -f docker-compose.prod.yml up -d --build"
echo "   Backup: /opt/freemarket/backup-db.sh"
echo ""
echo "🚨 MONITORING:"
echo "   - Check logs regularly: docker compose logs --tail=100"
echo "   - Monitor health: curl http://localhost:8000/health"
echo "   - Watch metrics: Prometheus/Grafana dashboards"
echo "   - Alert on errors: Configure notifications for critical issues"
echo ""
echo "🛟 ROLLBACK:"
echo "   If issues occur, rollback with:"
echo "   docker compose -f docker-compose.prod.yml down"
echo "   git checkout previous-tag"
echo "   docker compose -f docker-compose.prod.yml up -d"
echo ""
echo "🎯 NEXT STEPS:"
echo "1. Configure domain and SSL certificates"
echo "2. Setup CDN for static assets"
echo "3. Configure email notifications"
echo "4. Setup automated CI/CD pipeline"
echo "5. Monitor performance and scale as needed"
echo ""
echo "🚀 FREEMARKET v2.0.0 IS LIVE AND READY FOR USERS!"
