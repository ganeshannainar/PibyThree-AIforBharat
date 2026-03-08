#!/bin/bash
# Database Restore Script for E-commerce PostgreSQL
# Usage: ./restore_db.sh <backup_file.dump>

set -e

# Configuration
CONTAINER_NAME="ecommerce-postgres"
DB_NAME="ecommerce_db"
DB_USER="ecommerce_user"

if [ -z "$1" ]; then
    echo "❌ Error: Please provide a backup file path"
    echo "Usage: ./restore_db.sh <backup_file.dump>"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Check if container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "❌ Error: Container $CONTAINER_NAME is not running"
    exit 1
fi

echo "⚠️  WARNING: This will drop and recreate the $DB_NAME database!"
read -p "Are you sure you want to continue? (y/N) " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Restore cancelled"
    exit 1
fi

echo "🗄️  Starting restore from $BACKUP_FILE..."

# Copy backup to container
docker cp "$BACKUP_FILE" $CONTAINER_NAME:/tmp/restore.dump

# Drop existing connections and recreate database
docker exec $CONTAINER_NAME psql -U $DB_USER -d postgres -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '$DB_NAME' AND pid <> pg_backend_pid();" 2>/dev/null || true
docker exec $CONTAINER_NAME psql -U $DB_USER -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"
docker exec $CONTAINER_NAME psql -U $DB_USER -d postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"

# Restore from backup
docker exec $CONTAINER_NAME pg_restore -U $DB_USER -d $DB_NAME -v /tmp/restore.dump

# Clean up
docker exec $CONTAINER_NAME rm /tmp/restore.dump

echo "✅ Restore completed successfully!"
