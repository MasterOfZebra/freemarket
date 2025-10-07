#!/bin/bash
# install_netdata.sh - Install and configure Netdata monitoring

set -e

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

log "Installing Netdata..."

# Install Netdata using official script
wget -O /tmp/netdata-kickstart.sh https://get.netdata.cloud/kickstart.sh
bash /tmp/netdata-kickstart.sh --non-interactive

# Wait for Netdata to start
sleep 10

# Check if Netdata is running
if ! systemctl is-active --quiet netdata; then
    error "Netdata failed to start"
fi

log "Netdata installed successfully"

# Configure Netdata
log "Configuring Netdata..."
cp /opt/freemarket/monitoring/netdata.conf /etc/netdata/netdata.conf
systemctl restart netdata

# Configure firewall (if UFW is used)
if command -v ufw &> /dev/null; then
    log "Configuring UFW for Netdata..."
    ufw allow 19999/tcp comment "Netdata monitoring"
fi

log "Netdata configuration completed"
log "Access Netdata at: http://localhost:19999"
log "API endpoint: http://localhost:19999/api/v1/info"
