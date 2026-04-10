"""Add jewelry-specific fields to products table

Revision ID: 002
Revises: 001
Create Date: 2026-03-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new jewelry-specific columns to products table

    # Sub-category field
    op.add_column('products', sa.Column('sub_category', sa.String(length=100), nullable=True))
    op.create_index(op.f('ix_products_sub_category'), 'products', ['sub_category'], unique=False)

    # Jewelry-specific fields
    op.add_column('products', sa.Column('style_number', sa.String(length=50), nullable=True))
    op.add_column('products', sa.Column('st_carat', sa.Numeric(precision=10, scale=4), nullable=True))
    op.add_column('products', sa.Column('product_weight', sa.Numeric(precision=10, scale=4), nullable=True))
    op.add_column('products', sa.Column('gold_purity', sa.String(length=20), nullable=True))
    op.add_column('products', sa.Column('certified', sa.Boolean(), nullable=True, default=False))

    # Additional pricing field
    op.add_column('products', sa.Column('online_price', sa.Numeric(precision=12, scale=2), nullable=True))

    # Modify existing SKU column to have stricter length constraint
    # Note: In production, you may want to validate existing data first
    op.alter_column('products', 'sku',
                    existing_type=sa.String(length=100),
                    type_=sa.String(length=20),
                    existing_nullable=False)


def downgrade() -> None:
    # Remove new columns in reverse order

    # Remove online_price
    op.drop_column('products', 'online_price')

    # Remove jewelry-specific fields
    op.drop_column('products', 'certified')
    op.drop_column('products', 'gold_purity')
    op.drop_column('products', 'product_weight')
    op.drop_column('products', 'st_carat')
    op.drop_column('products', 'style_number')

    # Drop sub_category index and column
    op.drop_index(op.f('ix_products_sub_category'), table_name='products')
    op.drop_column('products', 'sub_category')

    # Revert SKU column length
    op.alter_column('products', 'sku',
                    existing_type=sa.String(length=20),
                    type_=sa.String(length=100),
                    existing_nullable=False)
