#!/bin/bash
# update_cloudflare_ufw.sh
# Script to update UFW firewall rules with Cloudflare IP ranges
# Safely handles existing rules, logs actions, and maintains SSH access
# Run as root or with sudo

set -euo pipefail

# Configuration
LOG_FILE="/var/log/update_cloudflare_ufw.log"
TMP_RULES="/tmp/ufw_cdn_rules.$$"
CF_V4_URL="https://www.cloudflare.com/ips-v4"
CF_V6_URL="https://www.cloudflare.com/ips-v6"
ADMIN_IP="${ADMIN_IP:-REPLACE_WITH_ADMIN_IP}"  # Set via environment or replace directly

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $*" | tee -a "$LOG_FILE"
}

# Error handling
trap 'log "Script failed at line $LINENO with exit code $?"; cleanup' ERR
cleanup() {
    rm -f "$TMP_RULES"
    log "Cleanup completed"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    log "This script must be run as root"
    exit 1
fi

# Check if ADMIN_IP is set
if [[ "$ADMIN_IP" == "REPLACE_WITH_ADMIN_IP" ]]; then
    log "ERROR: ADMIN_IP not set. Please set ADMIN_IP environment variable or edit script."
    exit 1
fi

log "Starting Cloudflare UFW update script"
log "Admin IP: $ADMIN_IP"

# Backup current UFW status
log "Backing up current UFW rules"
sudo ufw status numbered > "/tmp/ufw_status_pre_$(date +%Y%m%d_%H%M%S).txt" 2>/dev/null || log "Warning: Could not backup numbered status"

# Get current rules for HTTP/HTTPS
log "Identifying existing Cloudflare-related rules"
EXISTING_CF_RULES=$(sudo ufw status | grep -i "cf-range\|cloudflare" | wc -l)
log "Found $EXISTING_CF_RULES existing Cloudflare-related rules"

# Remove existing Cloudflare HTTP/HTTPS rules
log "Removing existing Cloudflare HTTP/HTTPS rules"
sudo ufw --force delete allow 80/tcp 2>/dev/null || log "No existing rule for port 80"
sudo ufw --force delete allow 443/tcp 2>/dev/null || log "No existing rule for port 443"

# Ensure SSH access from admin IP
log "Ensuring SSH access from admin IP"
if ! sudo ufw status | grep -q "$ADMIN_IP.*22"; then
    sudo ufw allow from "$ADMIN_IP" to any port 22 proto tcp
    log "Added SSH rule for admin IP"
else
    log "SSH rule for admin IP already exists"
fi

# Download and add Cloudflare IPv4 ranges
log "Downloading Cloudflare IPv4 ranges"
if ! curl -s --max-time 30 "$CF_V4_URL" > "$TMP_RULES"; then
    log "ERROR: Failed to download IPv4 ranges"
    exit 1
fi

log "Adding Cloudflare IPv4 ranges to UFW"
while read -r ip; do
    if [[ -n "$ip" ]]; then
        sudo ufw allow from "$ip" to any port 80,443 proto tcp comment 'cf-range-v4'
        log "Added IPv4 range: $ip"
    fi
done < "$TMP_RULES"

# Download and add Cloudflare IPv6 ranges
log "Downloading Cloudflare IPv6 ranges"
if ! curl -s --max-time 30 "$CF_V6_URL" > "$TMP_RULES"; then
    log "ERROR: Failed to download IPv6 ranges"
    exit 1
fi

log "Adding Cloudflare IPv6 ranges to UFW"
while read -r ip; do
    if [[ -n "$ip" ]]; then
        sudo ufw allow from "$ip" to any port 80,443 proto tcp comment 'cf-range-v6'
        log "Added IPv6 range: $ip"
    fi
done < "$TMP_RULES"

# Set default policies if not already set
log "Ensuring default policies"
sudo ufw default deny incoming 2>/dev/null || log "Default deny incoming already set"
sudo ufw default allow outgoing 2>/dev/null || log "Default allow outgoing already set"

# Enable UFW if not already enabled
if ! sudo ufw status | grep -q "Status: active"; then
    log "Enabling UFW"
    echo "y" | sudo ufw --force enable
else
    log "UFW already enabled, reloading rules"
    sudo ufw reload
fi

# Verify rules were added
NEW_CF_RULES=$(sudo ufw status | grep -c "cf-range")
log "Added $((NEW_CF_RULES - EXISTING_CF_RULES)) new Cloudflare rules"

# Cleanup
cleanup

log "Cloudflare UFW update completed successfully"
log "Please verify with: sudo ufw status"
