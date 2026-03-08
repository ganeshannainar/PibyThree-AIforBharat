#!/bin/bash
# Database Backup Script

CONTAINER_NAME="ecommerce-postgres"
DB_NAME="ecommerce_db"
DB_USER="ecommerce_user"
BACKUP_DIR="$(dirname "$0")/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.sql"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo "🔄 Starting backup..."
echo "   Container: $CONTAINER_NAME"
echo "   Database: $DB_NAME"

# Check if container is running
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "❌ Error: Container '$CONTAINER_NAME' is not running"
    exit 1
fi

# Create backup
docker exec "$CONTAINER_NAME" pg_dump -U "$DB_USER" -d "$DB_NAME" > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Backup created: $BACKUP_FILE"
    echo "   Size: $(du -h "$BACKUP_FILE" | cut -f1)"
    
    # Keep only last 10 backups
    cd "$BACKUP_DIR"
    ls -t backup_*.sql | tail -n +11 | xargs -r rm
    echo "   Cleanup: Keeping last 10 backups"
else
    echo "❌ Backup failed"
    exit 1
fi
