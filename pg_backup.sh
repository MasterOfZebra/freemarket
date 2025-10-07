#!/bin/bash
# pg_backup.sh
# PostgreSQL backup script with compression, encryption, and S3 upload
# Run as root or postgres user

set -euo pipefail

# Configuration - Edit these variables
DB_HOST="127.0.0.1"
DB_PORT="5432"
DB_NAME="freemarket_db"
DB_USER="freemarket_user"
DB_PASSWORD="${DB_PASSWORD:-}"  # Set via environment or replace
BACKUP_DIR="/backup"
S3_BUCKET="your-freemarket-backups"
GPG_RECIPIENT="backup@yourdomain.com"
RETENTION_DAYS=14
LOG_FILE="/var/log/pg_backup.log"

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $*" | tee -a "$LOG_FILE"
}

# Error handling
trap 'log "Backup failed at line $LINENO with exit code $?"' ERR

# Check prerequisites
check_prerequisites() {
    if ! command -v pg_dump &> /dev/null; then
        log "ERROR: pg_dump not found. Install postgresql-client"
        exit 1
    fi

    if ! command -v gzip &> /dev/null; then
        log "ERROR: gzip not found"
        exit 1
    fi

    if ! command -v gpg &> /dev/null; then
        log "ERROR: gpg not found. Install gnupg"
        exit 1
    fi

    if ! command -v aws &> /dev/null; then
        log "ERROR: aws CLI not found. Install awscli"
        exit 1
    fi

    if [[ -z "$DB_PASSWORD" ]]; then
        log "ERROR: DB_PASSWORD not set"
        exit 1
    fi
}

# Create backup directory if it doesn't exist
setup_backup_dir() {
    if [[ ! -d "$BACKUP_DIR" ]]; then
        mkdir -p "$BACKUP_DIR"
        chmod 700 "$BACKUP_DIR"
        log "Created backup directory: $BACKUP_DIR"
    fi
}

# Perform database dump
create_backup() {
    local timestamp
    timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/${DB_NAME}_${timestamp}.sql"
    local compressed_file="${backup_file}.gz"
    local encrypted_file="${compressed_file}.gpg"

    log "Starting backup of database: $DB_NAME"

    # Export password for pg_dump
    export PGPASSWORD="$DB_PASSWORD"

    # Create dump
    log "Creating database dump..."
    pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
            --no-password --format=custom --compress=9 \
            --file="$backup_file.dump" \
            --verbose

    # Compress
    log "Compressing backup..."
    gzip "$backup_file.dump"
    compressed_file="${backup_file}.dump.gz"

    # Encrypt
    log "Encrypting backup..."
    gpg --yes --batch --encrypt --recipient "$GPG_RECIPIENT" \
        --output "$encrypted_file" "$compressed_file"

    # Clean up uncompressed files
    rm -f "$backup_file.dump" "$compressed_file"

    log "Backup created: $encrypted_file"
    echo "$encrypted_file"
}

# Upload to S3
upload_to_s3() {
    local file="$1"
    local s3_key="backups/$(basename "$file")"

    log "Uploading to S3: s3://$S3_BUCKET/$s3_key"
    aws s3 cp "$file" "s3://$S3_BUCKET/$s3_key" --storage-class STANDARD_IA

    if [[ $? -eq 0 ]]; then
        log "Upload successful"
    else
        log "ERROR: Upload failed"
        exit 1
    fi
}

# Clean up old backups
cleanup_old_backups() {
    log "Cleaning up backups older than $RETENTION_DAYS days"

    # Local cleanup
    find "$BACKUP_DIR" -name "*.gpg" -type f -mtime +"$RETENTION_DAYS" -delete

    # S3 cleanup (optional - can be done via lifecycle policy)
    # aws s3api list-objects-v2 --bucket "$S3_BUCKET" --prefix "backups/" \
    #     --query 'Contents[?LastModified<`'"$(date -d "$RETENTION_DAYS days ago" +%Y-%m-%d)"'`].Key' \
    #     --output text | xargs -I {} aws s3 rm "s3://$S3_BUCKET/{}"

    log "Cleanup completed"
}

# Verify backup integrity (optional)
verify_backup() {
    local file="$1"
    log "Verifying backup integrity..."

    # Decrypt and check if pg_restore can read it
    if gpg --decrypt "$file" | pg_restore --list > /dev/null 2>&1; then
        log "Backup verification successful"
    else
        log "ERROR: Backup verification failed"
        exit 1
    fi
}

# Main execution
main() {
    log "=== Starting PostgreSQL backup ==="

    check_prerequisites
    setup_backup_dir

    local backup_file
    backup_file=$(create_backup)

    upload_to_s3 "$backup_file"

    # Optional: verify_backup "$backup_file"

    cleanup_old_backups

    log "=== Backup completed successfully ==="
}

main "$@"
