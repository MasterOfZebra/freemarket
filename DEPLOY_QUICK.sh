#!/bin/bash
# FREEMARKET v2.0.0 - QUICK DEPLOYMENT COMMANDS
# Copy-paste these commands to deploy on your server

# 1. SERVER PREPARATION
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git htop docker-compose-plugin

# Install Docker from official repository (avoids conflicts)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo systemctl enable docker && sudo systemctl start docker
rm get-docker.sh
sudo usermod -aG docker $USER

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# 2. DATABASE CONNECTION TEST (update with your DB details)
export DB_HOST="192.168.1.9"
export DB_PORT="5432"
export DB_NAME="assistance_kz"
export DB_USER="assistadmin_pg"
export DB_PASSWORD="assistMurzAdmin"
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT version();"

# 3. CODE DEPLOYMENT
sudo mkdir -p /opt/freemarket
sudo chown $USER:$USER /opt/freemarket
cd /opt/freemarket
git clone https://github.com/MasterOfZebra/freemarket.git .
git checkout main
git pull origin main

# 4. ENVIRONMENT SETUP
cp .env.example .env
# Edit .env file with your actual values
nano .env

# 5. SSL CERTIFICATES (self-signed for testing)
mkdir -p certs
sudo openssl req -x509 -newkey rsa:4096 -keyout certs/privkey.pem -out certs/fullchain.pem -days 365 -nodes -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

# 6. DOCKER DEPLOYMENT
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d
sleep 30
docker compose -f docker-compose.prod.yml ps

# 7. DATABASE MIGRATIONS
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
docker compose -f docker-compose.prod.yml exec backend alembic check

# 8. HEALTH CHECKS
curl -f http://localhost:8000/health
curl -I http://localhost:8000/api/listings/wants | grep "X-API-Version"
curl -f http://localhost/

# 9. FUNCTIONAL TESTING
curl -s "http://localhost/api/listings/wants?limit=5" | jq '.items | length'
curl -s "http://localhost/api/listings/offers?limit=5" | jq '.items | length'
curl -s http://localhost:8000/health | jq '.status'

# 10. LOAD TESTING
sudo apt install -y apache2-utils
ab -n 100 -c 10 http://localhost/api/listings/wants
ab -n 200 -c 50 http://localhost/

# 11. MONITORING (optional)
sudo apt install -y prometheus grafana
sudo systemctl enable prometheus && sudo systemctl start prometheus
sudo systemctl enable grafana-server && sudo systemctl start grafana-server

# 12. SECURITY SCAN
pip install pip-audit safety bandit
pip-audit --format json
npm audit --audit-level moderate

# 13. BACKUP SETUP
cat > backup-db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/freemarket/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/freemarket_$TIMESTAMP.sql"
mkdir -p $BACKUP_DIR
PGPASSWORD=assistMurzAdmin pg_dump -h 192.168.1.9 -p 5432 -U assistadmin_pg assistance_kz > $BACKUP_FILE
find $BACKUP_DIR -name "freemarket_*.sql" -mtime +7 -delete
echo "Backup completed: $BACKUP_FILE"
EOF
chmod +x backup-db.sh
(crontab -l ; echo "0 2 * * * /opt/freemarket/backup-db.sh") | crontab -

# 14. FINAL VERIFICATION
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs --tail=50 | grep -i error || echo "No errors found"

echo "🎉 FREEMARKET v2.0.0 DEPLOYMENT COMPLETE!"
echo "Frontend: http://your-server-ip/"
echo "API: http://your-server-ip:8000/"
echo "API Docs: http://your-server-ip:8000/docs"
