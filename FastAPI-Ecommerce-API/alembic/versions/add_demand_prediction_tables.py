"""add demand prediction tables

Revision ID: add_demand_prediction
Revises: add_prompt_fields
Create Date: 2024-12-10 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_demand_prediction'
down_revision = 'add_prompt_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Create product_sales_data table for historical sales data
    op.create_table(
        'product_sales_data',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('product_id', sa.String(), nullable=False),
        sa.Column('time_idx', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('week', sa.Integer(), nullable=False),
        sa.Column('Holiday', sa.String(), nullable=False, server_default='No Holiday'),
        sa.Column('weather', sa.String(), nullable=False, server_default='Overcast'),
        sa.Column('total_sales', sa.Float(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create demand_prediction_history table
    op.create_table(
        'demand_prediction_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('admin_id', sa.Integer(), nullable=True),
        sa.Column('holiday_input', sa.String(), nullable=False, server_default='No Holiday'),
        sa.Column('weather_input', sa.String(), nullable=False, server_default='Overcast'),
        sa.Column('base_forecast', sa.Float(), nullable=False),
        sa.Column('trend_score', sa.Float(), nullable=True),
        sa.Column('sentiment_score', sa.Float(), nullable=True),
        sa.Column('multiplier', sa.Float(), nullable=True, server_default='1.0'),
        sa.Column('adjusted_forecast', sa.Float(), nullable=False),
        sa.Column('demand_level', sa.String(), nullable=False),
        sa.Column('demand_change_pct', sa.Float(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('acknowledged_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['admin_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for efficient querying
    op.create_index('ix_product_sales_data_product_id', 'product_sales_data', ['product_id'])
    op.create_index('ix_product_sales_data_time_idx', 'product_sales_data', ['time_idx'])
    op.create_index('ix_demand_prediction_history_product_id', 'demand_prediction_history', ['product_id'])
    op.create_index('ix_demand_prediction_history_demand_level', 'demand_prediction_history', ['demand_level'])


def downgrade():
    op.drop_index('ix_demand_prediction_history_demand_level', table_name='demand_prediction_history')
    op.drop_index('ix_demand_prediction_history_product_id', table_name='demand_prediction_history')
    op.drop_index('ix_product_sales_data_time_idx', table_name='product_sales_data')
    op.drop_index('ix_product_sales_data_product_id', table_name='product_sales_data')
    op.drop_table('demand_prediction_history')
    op.drop_table('product_sales_data')
