"""add dynamic pricing fields and history table

Revision ID: add_dynamic_pricing
Revises: 92735c1b0068
Create Date: 2025-11-27

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_dynamic_pricing'
down_revision = '92735c1b0068'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to products table
    op.add_column('products', sa.Column('base_price', sa.Float(), nullable=True))
    op.add_column('products', sa.Column('dynamic_price', sa.Float(), nullable=True))
    op.add_column('products', sa.Column('is_dynamic_pricing_active', sa.Boolean(), 
                                        server_default='false', nullable=False))
    
    # Create pricing_status enum (with IF NOT EXISTS)
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'pricing_status') THEN CREATE TYPE pricing_status AS ENUM ('pending', 'approved', 'rejected'); END IF; END $$;")
    
    # Create dynamic_pricing_history table with String for status first
    op.create_table(
        'dynamic_pricing_history',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('admin_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        
        # Prediction results
        sa.Column('predicted_price', sa.Float(), nullable=False),
        sa.Column('original_price', sa.Float(), nullable=False),
        sa.Column('discount_from_original', sa.Float(), nullable=False),
        
        # Status - using String first to avoid enum creation
        sa.Column('status', sa.String(), nullable=False),
        
        # ML Input Features
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('brand_tier', sa.String(), nullable=False),
        sa.Column('msrp', sa.Float(), nullable=False),
        sa.Column('cogs', sa.Float(), nullable=False),
        sa.Column('min_margin_req', sa.Float(), nullable=False),
        sa.Column('inventory_qty', sa.Integer(), nullable=False),
        sa.Column('weeks_of_cover', sa.Float(), nullable=False),
        sa.Column('sell_through_rate', sa.Float(), nullable=False),
        sa.Column('stock_age_days', sa.Integer(), nullable=False),
        sa.Column('daily_sales_velocity', sa.Float(), nullable=False),
        sa.Column('conversion_rate', sa.Float(), nullable=False),
        sa.Column('cart_abandon_rate', sa.Float(), nullable=False),
        sa.Column('competitor_price', sa.Float(), nullable=False),
        sa.Column('competitor_price_diff_pct', sa.Float(), nullable=False),
        sa.Column('competitor_stock_status', sa.Integer(), nullable=False),
        sa.Column('market_saturation', sa.Float(), nullable=False),
        sa.Column('season', sa.String(), nullable=False),
        sa.Column('holiday_event', sa.Integer(), nullable=False),
        sa.Column('marketing_spend_boost', sa.Integer(), nullable=False),
        
        # Timestamps
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('decided_at', sa.TIMESTAMP(timezone=True), nullable=True),
    )
    
    # Convert status column to enum type and set default
    op.execute("ALTER TABLE dynamic_pricing_history ALTER COLUMN status TYPE pricing_status USING status::pricing_status;")
    op.execute("ALTER TABLE dynamic_pricing_history ALTER COLUMN status SET DEFAULT 'pending';")
    
    # Create index for faster lookups
    op.create_index('ix_dynamic_pricing_history_product_id', 'dynamic_pricing_history', ['product_id'])
    op.create_index('ix_dynamic_pricing_history_status', 'dynamic_pricing_history', ['status'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_dynamic_pricing_history_status', table_name='dynamic_pricing_history')
    op.drop_index('ix_dynamic_pricing_history_product_id', table_name='dynamic_pricing_history')
    
    # Drop dynamic_pricing_history table
    op.drop_table('dynamic_pricing_history')
    
    # Drop pricing_status enum
    sa.Enum(name='pricing_status').drop(op.get_bind(), checkfirst=True)
    
    # Remove columns from products table
    op.drop_column('products', 'is_dynamic_pricing_active')
    op.drop_column('products', 'dynamic_price')
    op.drop_column('products', 'base_price')
