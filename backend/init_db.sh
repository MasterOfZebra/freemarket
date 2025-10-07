#!/bin/bash
# init_db.sh - Initialize PostgreSQL database for FreeMarket

set -e

# Configuration
DB_NAME="freemarket_db"
DB_USER="freemarket_user"
DB_PASSWORD="password"  # Change this!
DB_HOST="localhost"
DB_PORT="5432"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
}

warn() {
    echo -e "${YELLOW}[WARN] $1${NC}"
}

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    error "PostgreSQL client not found. Please install PostgreSQL."
    exit 1
fi

# Check if we can connect as superuser
if ! sudo -u postgres psql -c "SELECT 1;" &> /dev/null; then
    error "Cannot connect to PostgreSQL as postgres user."
    error "Make sure PostgreSQL is running and you have sudo access."
    exit 1
fi

log "Creating database user..."
sudo -u postgres psql -c "CREATE USER IF NOT EXISTS $DB_USER WITH PASSWORD '$DB_PASSWORD';" 2>/dev/null || warn "User might already exist"

log "Creating database..."
sudo -u postgres psql -c "CREATE DATABASE IF NOT EXISTS $DB_NAME OWNER $DB_USER;" 2>/dev/null || warn "Database might already exist"

log "Granting privileges..."
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

log "Running schema.sql..."
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f schema.sql

log "Database initialization completed!"
log "Database URL: postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
log "Update your .env file with this DATABASE_URL"
