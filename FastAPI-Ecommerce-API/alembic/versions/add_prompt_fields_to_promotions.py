"""Add prompt fields to dynamic_promotions table

Revision ID: add_prompt_fields
Revises: add_dynamic_promotions
Create Date: 2025-12-04

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_prompt_fields'
down_revision = 'add_dynamic_promotions'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add text_prompt_used column
    op.add_column('dynamic_promotions', 
        sa.Column('text_prompt_used', sa.Text(), nullable=True)
    )
    
    # Add image_prompt_used column
    op.add_column('dynamic_promotions', 
        sa.Column('image_prompt_used', sa.Text(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('dynamic_promotions', 'text_prompt_used')
    op.drop_column('dynamic_promotions', 'image_prompt_used')
