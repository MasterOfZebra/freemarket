#!/bin/bash
# deploy.sh - Deploy FreeMarket to production server

set -e

# Configuration
APP_DIR="/opt/freemarket"
BACKEND_DIR="$APP_DIR/backend"
FRONTEND_DIR="$APP_DIR/frontend"
VENV_DIR="$BACKEND_DIR/venv"
LOG_DIR="/var/log/freemarket"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
    exit 1
}

warn() {
    echo -e "${YELLOW}[WARN] $1${NC}"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    error "This script must be run as root"
fi

log "Starting FreeMarket deployment..."

# Create directories
log "Creating directories..."
mkdir -p "$APP_DIR" "$LOG_DIR"
chown www-data:www-data "$APP_DIR" "$LOG_DIR"

# Install system dependencies
log "Installing system dependencies..."
apt update
apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx redis-server git curl

# Clone/update repository (assuming code is already there, or add git clone)
# cd /tmp
# git clone https://github.com/your-repo/freemarket.git
# cp -r freemarket/* $APP_DIR/

# Setup backend
log "Setting up backend..."
cd "$BACKEND_DIR"

# Create virtual environment
python3 -m venv "$VENV_DIR"
chown -R www-data:www-data "$VENV_DIR"

# Install Python dependencies
sudo -u www-data "$VENV_DIR/bin/pip" install --upgrade pip
sudo -u www-data "$VENV_DIR/bin/pip" install -r requirements.txt

# Setup database
log "Setting up database..."
chmod +x init_db.sh
./init_db.sh

# Build frontend
log "Building frontend..."
cd "$FRONTEND_DIR"
npm install
npm run build
chown -R www-data:www-data "$FRONTEND_DIR"

# Configure services
log "Configuring services..."

# Copy systemd services
cp freemarket.service /etc/systemd/system/
cp freemarket-bot.service /etc/systemd/system/

# Copy nginx config
cp freemarket.nginx /etc/nginx/sites-available/freemarket
ln -sf /etc/nginx/sites-available/freemarket /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test configurations
log "Testing configurations..."
nginx -t || error "Nginx configuration test failed"
systemctl daemon-reload

# Start services
log "Starting services..."
systemctl enable freemarket freemarket-bot nginx postgresql redis
systemctl start postgresql redis
systemctl start freemarket freemarket-bot nginx

# Wait for services to start
sleep 5

# Health check
log "Running health checks..."
curl -f http://localhost/health || warn "API health check failed"
curl -f http://localhost/ || warn "Frontend health check failed"

log "Deployment completed successfully!"
log "Services status:"
systemctl status freemarket freemarket-bot nginx --no-pager -l

echo ""
echo "Next steps:"
echo "1. Configure SSL certificates"
echo "2. Update DNS records"
echo "3. Configure firewall (UFW)"
echo "4. Set up monitoring"
echo "5. Configure backups"
