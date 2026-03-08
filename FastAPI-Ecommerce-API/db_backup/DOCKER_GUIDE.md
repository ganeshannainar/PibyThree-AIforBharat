# Docker Compose & Volumes Guide

## Basic Commands

### Container Lifecycle
```bash
# Start containers (detached)
docker-compose up -d

# Stop containers
docker-compose down

# Stop and remove volumes (DELETES DATA!)
docker-compose down -v

# Restart containers
docker-compose restart

# View logs
docker-compose logs -f
docker-compose logs postgres  # specific service
```

### Container Management
```bash
# List running containers
docker ps

# List all containers (including stopped)
docker ps -a

# Stop a container
docker stop <container_name>

# Remove a container
docker rm <container_name>

# Execute command in container
docker exec -it ecommerce-postgres psql -U ecommerce_user -d ecommerce_db
```

---

## Complete Database Schema

### Custom Enum Types

```sql
-- User roles
CREATE TYPE user_roles AS ENUM ('admin', 'user');

-- Dynamic pricing status
CREATE TYPE pricing_status AS ENUM ('pending', 'approved', 'rejected');

-- Promotion status  
CREATE TYPE promotion_status AS ENUM ('pending', 'active', 'expired', 'draft', 'live');

-- Order status
CREATE TYPE order_status AS ENUM ('pending', 'confirmed', 'shipped', 'delivered', 'cancelled');
```

### Table: users
| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | integer | NOT NULL | auto-increment | PRIMARY KEY, UNIQUE |
| username | varchar | NOT NULL | | UNIQUE |
| email | varchar | NOT NULL | | UNIQUE |
| password | varchar | NOT NULL | | |
| full_name | varchar | NOT NULL | | |
| is_active | boolean | NOT NULL | true | |
| created_at | timestamptz | NOT NULL | now() | |
| role | user_roles | NOT NULL | 'user' | |

**Referenced by:** carts, orders, demand_prediction_history, dynamic_pricing_history

### Table: categories
| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | integer | NOT NULL | auto-increment | PRIMARY KEY, UNIQUE |
| name | varchar | NOT NULL | | UNIQUE |

**Referenced by:** products

### Table: products
| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | integer | NOT NULL | auto-increment | PRIMARY KEY, UNIQUE |
| title | varchar | NOT NULL | | |
| description | varchar | NOT NULL | | |
| price | integer | NOT NULL | | |
| discount_percentage | float | NOT NULL | | |
| rating | float | NOT NULL | | |
| stock | integer | NOT NULL | | |
| brand | varchar | NOT NULL | | |
| thumbnail | varchar | NOT NULL | | |
| images | varchar[] | NOT NULL | | |
| is_published | boolean | NOT NULL | true | |
| created_at | timestamptz | NOT NULL | now() | |
| category_id | integer | NOT NULL | | FK → categories(id) CASCADE |
| base_price | float | NULL | | |
| dynamic_price | float | NULL | | |
| is_dynamic_pricing_active | boolean | NOT NULL | false | |

**Referenced by:** cart_items, order_items, demand_prediction_history, dynamic_pricing_history, dynamic_promotions

### Table: carts
| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | integer | NOT NULL | auto-increment | PRIMARY KEY, UNIQUE |
| user_id | integer | NOT NULL | | FK → users(id) CASCADE |
| created_at | timestamptz | NOT NULL | now() | |
| total_amount | float | NOT NULL | | |

**Referenced by:** cart_items

### Table: cart_items
| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | integer | NOT NULL | auto-increment | PRIMARY KEY, UNIQUE |
| cart_id | integer | NOT NULL | | FK → carts(id) CASCADE |
| product_id | integer | NOT NULL | | FK → products(id) CASCADE |
| quantity | integer | NOT NULL | | |
| subtotal | float | NOT NULL | | |

### Table: orders
| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | integer | NOT NULL | auto-increment | PRIMARY KEY, UNIQUE |
| user_id | integer | NOT NULL | | FK → users(id) CASCADE |
| total_amount | float | NOT NULL | | |
| status | order_status | NOT NULL | 'confirmed' | |
| created_at | timestamptz | NOT NULL | now() | |

**Referenced by:** order_items

### Table: order_items
| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | integer | NOT NULL | auto-increment | PRIMARY KEY, UNIQUE |
| order_id | integer | NOT NULL | | FK → orders(id) CASCADE |
| product_id | integer | NULL | | FK → products(id) SET NULL |
| product_title | varchar | NOT NULL | | |
| product_price | float | NOT NULL | | |
| quantity | integer | NOT NULL | | |
| subtotal | float | NOT NULL | | |
| discount_percentage | float | NOT NULL | 0 | |
| discount_amount | float | NOT NULL | 0 | |

### Table: product_sales_data
| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | integer | NOT NULL | auto-increment | PRIMARY KEY |
| product_id | varchar | NOT NULL | | INDEX |
| time_idx | integer | NOT NULL | | INDEX |
| year | integer | NOT NULL | | |
| month | integer | NOT NULL | | |
| week | integer | NOT NULL | | |
| Holiday | varchar | NOT NULL | 'No Holiday' | |
| weather | varchar | NOT NULL | 'Overcast' | |
| total_sales | float | NOT NULL | | |
| created_at | timestamptz | NOT NULL | now() | |

### Table: demand_prediction_history
| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | integer | NOT NULL | auto-increment | PRIMARY KEY |
| product_id | integer | NOT NULL | | FK → products(id) CASCADE, INDEX |
| admin_id | integer | NULL | | FK → users(id) SET NULL |
| holiday_input | varchar | NOT NULL | 'No Holiday' | |
| weather_input | varchar | NOT NULL | 'Overcast' | |
| base_forecast | float | NOT NULL | | |
| trend_score | float | NULL | | |
| sentiment_score | float | NULL | | |
| multiplier | float | NULL | 1 | |
| adjusted_forecast | float | NOT NULL | | |
| demand_level | varchar | NOT NULL | | INDEX |
| demand_change_pct | float | NULL | | |
| status | varchar | NOT NULL | 'pending' | |
| created_at | timestamptz | NOT NULL | now() | |
| acknowledged_at | timestamptz | NULL | | |

### Table: dynamic_pricing_history
| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | integer | NOT NULL | auto-increment | PRIMARY KEY |
| product_id | integer | NOT NULL | | FK → products(id) CASCADE, INDEX |
| admin_id | integer | NULL | | FK → users(id) SET NULL |
| predicted_price | float | NOT NULL | | |
| original_price | float | NOT NULL | | |
| discount_from_original | float | NOT NULL | | |
| status | pricing_status | NOT NULL | 'pending' | INDEX |
| category | varchar | NOT NULL | | |
| brand_tier | varchar | NOT NULL | | |
| msrp | float | NOT NULL | | |
| cogs | float | NOT NULL | | |
| min_margin_req | float | NOT NULL | | |
| inventory_qty | integer | NOT NULL | | |
| weeks_of_cover | float | NOT NULL | | |
| sell_through_rate | float | NOT NULL | | |
| stock_age_days | integer | NOT NULL | | |
| daily_sales_velocity | float | NOT NULL | | |
| conversion_rate | float | NOT NULL | | |
| cart_abandon_rate | float | NOT NULL | | |
| competitor_price | float | NOT NULL | | |
| competitor_price_diff_pct | float | NOT NULL | | |
| competitor_stock_status | integer | NOT NULL | | |
| market_saturation | float | NOT NULL | | |
| season | varchar | NOT NULL | | |
| holiday_event | integer | NOT NULL | | |
| marketing_spend_boost | integer | NOT NULL | | |
| created_at | timestamptz | NOT NULL | now() | |
| decided_at | timestamptz | NULL | | |

**Referenced by:** dynamic_promotions

### Table: dynamic_promotions
| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | integer | NOT NULL | auto-increment | PRIMARY KEY |
| dynamic_pricing_history_id | integer | NOT NULL | | FK → dynamic_pricing_history(id) CASCADE |
| product_id | integer | NOT NULL | | FK → products(id) CASCADE, INDEX |
| product_title | varchar | NOT NULL | | |
| product_description | text | NOT NULL | | |
| product_thumbnail | varchar | NOT NULL | | |
| product_brand | varchar | NOT NULL | | |
| category_name | varchar | NOT NULL | | |
| original_price | float | NOT NULL | | |
| dynamic_price | float | NOT NULL | | |
| discount_percentage | float | NOT NULL | | |
| savings_amount | float | NOT NULL | | |
| promotion_image_url | varchar | NULL | | |
| promotion_text | text | NULL | | |
| headline | varchar | NULL | | |
| tagline | varchar | NULL | | |
| status | promotion_status | NOT NULL | 'pending' | INDEX |
| is_active | boolean | NOT NULL | true | INDEX |
| created_at | timestamptz | NOT NULL | now() | |
| expires_at | timestamptz | NULL | | |
| text_prompt_used | text | NULL | | |
| image_prompt_used | text | NULL | | |

---

## Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│   users     │       │ categories  │       │  products   │
├─────────────┤       ├─────────────┤       ├─────────────┤
│ id (PK)     │       │ id (PK)     │◄──────│ category_id │
│ username    │       │ name        │       │ id (PK)     │
│ email       │       └─────────────┘       │ title       │
│ role        │                             │ price       │
└──────┬──────┘                             │ ...         │
       │                                    └──────┬──────┘
       │                                           │
       ▼                                           │
┌─────────────┐       ┌─────────────┐              │
│   carts     │       │ cart_items  │◄─────────────┤
├─────────────┤       ├─────────────┤              │
│ id (PK)     │◄──────│ cart_id     │              │
│ user_id (FK)│       │ product_id  │──────────────┤
└─────────────┘       └─────────────┘              │
                                                   │
┌─────────────┐       ┌─────────────┐              │
│   orders    │       │ order_items │◄─────────────┤
├─────────────┤       ├─────────────┤              │
│ id (PK)     │◄──────│ order_id    │              │
│ user_id (FK)│       │ product_id  │──────────────┤
│ status      │       └─────────────┘              │
└─────────────┘                                    │
                                                   │
┌──────────────────────────┐                       │
│ demand_prediction_history│◄──────────────────────┤
├──────────────────────────┤                       │
│ id (PK)                  │                       │
│ product_id (FK)          │                       │
│ admin_id (FK → users)    │                       │
│ demand_level             │                       │
└──────────────────────────┘                       │
                                                   │
┌──────────────────────────┐                       │
│ dynamic_pricing_history  │◄──────────────────────┘
├──────────────────────────┤
│ id (PK)                  │
│ product_id (FK)          │
│ admin_id (FK → users)    │
│ status (pricing_status)  │
└───────────┬──────────────┘
            │
            ▼
┌──────────────────────────┐
│   dynamic_promotions     │
├──────────────────────────┤
│ id (PK)                  │
│ dynamic_pricing_history_id│
│ product_id (FK)          │
│ status (promotion_status)│
└──────────────────────────┘
```

---

## Volumes

### Why Use Volumes?
Volumes persist data outside the container. When container is deleted, data survives.

### Volume Commands
```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect ecommerce_postgres_data

# Remove unused volumes
docker volume prune

# Remove specific volume (DELETES DATA!)
docker volume rm ecommerce_postgres_data
```

### Volume in docker-compose.yml
```yaml
services:
  postgres:
    volumes:
      - ecommerce_postgres_data:/var/lib/postgresql/data  # Named volume

volumes:
  ecommerce_postgres_data:  # Declare named volume
```

## Images

### Image Commands
```bash
# List images
docker images

# Pull image
docker pull postgres:15-alpine

# Remove image
docker rmi postgres:15-alpine

# Build custom image
docker build -t my-app:latest .
```

## docker-compose.yml Explained

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine          # Base image
    container_name: ecommerce-postgres # Container name
    environment:                       # Environment variables
      POSTGRES_USER: ecommerce_user
      POSTGRES_PASSWORD: ecommerce_pass
      POSTGRES_DB: ecommerce_db
    ports:
      - "5432:5432"                    # host:container port mapping
    volumes:
      - ecommerce_postgres_data:/var/lib/postgresql/data  # Persist data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql   # Init script
    restart: unless-stopped            # Auto-restart policy
    healthcheck:                       # Health monitoring
      test: ["CMD-SHELL", "pg_isready -U ecommerce_user -d ecommerce_db"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  ecommerce_postgres_data:             # Named volume declaration
```

## Common Scenarios

### Fresh Start (Reset Everything)
```bash
docker-compose down -v
docker-compose up -d
cd .. && alembic upgrade head
```

### Backup Before Reset
```bash
./backup.sh
docker-compose down -v
docker-compose up -d
./restore.sh backups/latest_backup.sql
```

### Check Database Connection
```bash
docker exec ecommerce-postgres psql -U ecommerce_user -d ecommerce_db -c "\dt"
```

### View Table Structure
```bash
docker exec ecommerce-postgres psql -U ecommerce_user -d ecommerce_db -c "\d products"
```

## Tips

1. **Always use named volumes** for production data
2. **Backup before `docker-compose down -v`** - this deletes volumes
3. **Use `docker-compose logs -f`** to debug startup issues
4. **Check container health** with `docker ps` (look for "healthy" status)
