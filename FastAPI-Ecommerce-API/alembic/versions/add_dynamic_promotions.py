"""add_dynamic_promotions_table

Revision ID: add_dynamic_promotions
Revises: add_dynamic_pricing
Create Date: 2025-12-03

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_dynamic_promotions'
down_revision = 'add_dynamic_pricing'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create promotion_status enum (with IF NOT EXISTS)
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'promotion_status') THEN CREATE TYPE promotion_status AS ENUM ('pending', 'active', 'expired'); END IF; END $$;")
    
    # Create dynamic_promotions table with String for status first
    op.create_table(
        'dynamic_promotions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('dynamic_pricing_history_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('product_title', sa.String(), nullable=False),
        sa.Column('product_description', sa.Text(), nullable=False),
        sa.Column('product_thumbnail', sa.String(), nullable=False),
        sa.Column('product_brand', sa.String(), nullable=False),
        sa.Column('category_name', sa.String(), nullable=False),
        sa.Column('original_price', sa.Float(), nullable=False),
        sa.Column('dynamic_price', sa.Float(), nullable=False),
        sa.Column('discount_percentage', sa.Float(), nullable=False),
        sa.Column('savings_amount', sa.Float(), nullable=False),
        sa.Column('promotion_image_url', sa.String(), nullable=True),
        sa.Column('promotion_text', sa.Text(), nullable=True),
        sa.Column('headline', sa.String(), nullable=True),
        sa.Column('tagline', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['dynamic_pricing_history_id'], ['dynamic_pricing_history.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id')
    )
    
    # Convert status column to enum type and set default
    op.execute("ALTER TABLE dynamic_promotions ALTER COLUMN status TYPE promotion_status USING status::promotion_status;")
    op.execute("ALTER TABLE dynamic_promotions ALTER COLUMN status SET DEFAULT 'pending';")
    
    # Create index for faster lookups
    op.create_index('ix_dynamic_promotions_product_id', 'dynamic_promotions', ['product_id'])
    op.create_index('ix_dynamic_promotions_is_active', 'dynamic_promotions', ['is_active'])
    op.create_index('ix_dynamic_promotions_status', 'dynamic_promotions', ['status'])


def downgrade() -> None:
    op.drop_index('ix_dynamic_promotions_status', 'dynamic_promotions')
    op.drop_index('ix_dynamic_promotions_is_active', 'dynamic_promotions')
    op.drop_index('ix_dynamic_promotions_product_id', 'dynamic_promotions')
    op.drop_table('dynamic_promotions')
    
    # Drop the enum
    sa.Enum(name='promotion_status').drop(op.get_bind(), checkfirst=True)
