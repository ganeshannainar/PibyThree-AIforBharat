# Database Setup Guide

Quick guide to set up PostgreSQL for the E-commerce API.

## Prerequisites
- Docker & Docker Compose installed
- Port 5432 available

## Quick Start

```bash
# 1. Start PostgreSQL container
docker-compose -f docker-compose.yml up -d

# 2. Run migrations
cd .. && source venv/bin/activate
alembic upgrade head

# 3. (Optional) Create admin user
python -c "
from app.db.database import SessionLocal
from app.models.models import User
from passlib.context import CryptContext

db = SessionLocal()
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
admin = User(
    username='admin',
    email='admin@ecommerce.com',
    password=pwd_context.hash('admin123'),
    role='admin'
)
db.add(admin)
db.commit()
print('Admin created: admin/admin123')
db.close()
"
```

## Database Schema

### Tables (12 total)
| Table | Description |
|-------|-------------|
| `users` | User accounts (admin/user roles) |
| `categories` | Product categories |
| `products` | Product catalog |
| `carts` | Shopping carts |
| `cart_items` | Items in carts |
| `orders` | Customer orders |
| `order_items` | Items in orders |
| `product_sales_data` | Historical sales data |
| `demand_prediction_history` | AI demand predictions |
| `dynamic_pricing_history` | AI pricing predictions |
| `dynamic_promotions` | AI-generated promotions |

### Custom Enums
```sql
-- User roles
CREATE TYPE user_roles AS ENUM ('admin', 'user');

-- Pricing status
CREATE TYPE pricing_status AS ENUM ('pending', 'approved', 'rejected');

-- Promotion status
CREATE TYPE promotion_status AS ENUM ('pending', 'active', 'expired', 'draft', 'live');

-- Order status
CREATE TYPE order_status AS ENUM ('pending', 'confirmed', 'shipped', 'delivered', 'cancelled');
```

## Connection Details
```
Host: localhost
Port: 5432
Database: ecommerce_db
User: ecommerce_user
Password: ecommerce_pass
```

## Scripts

| Script | Description |
|--------|-------------|
| `backup.sh` | Backup database to SQL file |
| `restore.sh` | Restore database from backup |
| `init.sql` | Initialize database schema |

## Backup & Restore

```bash
# Backup
./backup.sh

# Restore
./restore.sh backups/backup_YYYYMMDD_HHMMSS.sql
```

## Troubleshooting

**Port 5432 in use:**
```bash
docker ps -a | grep 5432
docker stop <container_id>
```

**Enum type already exists (during migration):**
```bash
# Reset and re-run migrations
alembic downgrade base
alembic upgrade head
```

**Connection refused:**
```bash
# Check container is running
docker ps | grep ecommerce-postgres
docker logs ecommerce-postgres
```
