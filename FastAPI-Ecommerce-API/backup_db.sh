#!/bin/bash
# Database Backup Script for E-commerce PostgreSQL
# Usage: ./backup_db.sh [backup_name]

set -e

# Configuration
CONTAINER_NAME="ecommerce-postgres"
DB_NAME="ecommerce_db"
DB_USER="ecommerce_user"
BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME=${1:-"backup_${DATE}"}

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo "🗄️  Starting backup of $DB_NAME..."

# Check if container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "❌ Error: Container $CONTAINER_NAME is not running"
    exit 1
fi

# Create backup
docker exec $CONTAINER_NAME pg_dump -U $DB_USER -d $DB_NAME -F c -b -v -f /tmp/${BACKUP_NAME}.dump

# Copy backup from container to host
docker cp $CONTAINER_NAME:/tmp/${BACKUP_NAME}.dump "$BACKUP_DIR/${BACKUP_NAME}.dump"

# Clean up backup from container
docker exec $CONTAINER_NAME rm /tmp/${BACKUP_NAME}.dump

# Create SQL backup as well (human-readable)
docker exec $CONTAINER_NAME pg_dump -U $DB_USER -d $DB_NAME > "$BACKUP_DIR/${BACKUP_NAME}.sql"

echo "✅ Backup completed successfully!"
echo "📁 Backup files:"
echo "   - $BACKUP_DIR/${BACKUP_NAME}.dump (binary, for pg_restore)"
echo "   - $BACKUP_DIR/${BACKUP_NAME}.sql (SQL text, human-readable)"
echo ""
echo "📋 To restore from backup, run:"
echo "   ./restore_db.sh $BACKUP_DIR/${BACKUP_NAME}.dump"
