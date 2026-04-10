"""Initial migration - Create all core tables

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create products table
    op.create_table(
        'products',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sku', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('cost_price', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('retail_price', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('wholesale_price', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('attributes', postgresql.JSONB(astext_type=sa.Text()), nullable=True, default={}),
        sa.Column('default_reorder_threshold', sa.Numeric(precision=10, scale=2), nullable=True, default=10),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_products_id'), 'products', ['id'], unique=False)
    op.create_index(op.f('ix_products_sku'), 'products', ['sku'], unique=True)
    op.create_index(op.f('ix_products_category'), 'products', ['category'], unique=False)
    op.create_index(op.f('ix_products_created_at'), 'products', ['created_at'], unique=False)

    # Create inventory table
    op.create_table(
        'inventory',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=12, scale=2), nullable=False, default=0),
        sa.Column('reserved_quantity', sa.Numeric(precision=12, scale=2), nullable=False, default=0),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('warehouse_code', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('quantity >= 0', name='check_quantity_non_negative'),
        sa.CheckConstraint('reserved_quantity >= 0', name='check_reserved_non_negative'),
    )
    op.create_index(op.f('ix_inventory_id'), 'inventory', ['id'], unique=False)
    op.create_index(op.f('ix_inventory_product_id'), 'inventory', ['product_id'], unique=True)

    # Create inventory_transactions table
    op.create_table(
        'inventory_transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('inventory_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('transaction_type', sa.String(length=50), nullable=False),
        sa.Column('quantity_change', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('quantity_before', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('quantity_after', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('reference_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reference_type', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.Column('performed_by', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['inventory_id'], ['inventory.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_inventory_transactions_id'), 'inventory_transactions', ['id'], unique=False)
    op.create_index(op.f('ix_inventory_transactions_inventory_id'), 'inventory_transactions', ['inventory_id'], unique=False)
    op.create_index(op.f('ix_inventory_transactions_transaction_type'), 'inventory_transactions', ['transaction_type'], unique=False)
    op.create_index(op.f('ix_inventory_transactions_created_at'), 'inventory_transactions', ['created_at'], unique=False)

    # Create sales table
    op.create_table(
        'sales',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sale_number', sa.String(length=50), nullable=False),
        sa.Column('customer_name', sa.String(length=255), nullable=True),
        sa.Column('customer_email', sa.String(length=255), nullable=True),
        sa.Column('customer_phone', sa.String(length=50), nullable=True),
        sa.Column('sale_type', sa.String(length=20), nullable=False, default='RETAIL'),
        sa.Column('subtotal', sa.Numeric(precision=12, scale=2), nullable=False, default=0),
        sa.Column('tax_amount', sa.Numeric(precision=12, scale=2), nullable=False, default=0),
        sa.Column('discount_amount', sa.Numeric(precision=12, scale=2), nullable=False, default=0),
        sa.Column('total_amount', sa.Numeric(precision=12, scale=2), nullable=False, default=0),
        sa.Column('payment_method', sa.String(length=50), nullable=True),
        sa.Column('payment_status', sa.String(length=20), nullable=True, default='COMPLETED'),
        sa.Column('status', sa.String(length=20), nullable=False, default='COMPLETED'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('sale_date', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_sales_id'), 'sales', ['id'], unique=False)
    op.create_index(op.f('ix_sales_sale_number'), 'sales', ['sale_number'], unique=True)
    op.create_index(op.f('ix_sales_sale_date'), 'sales', ['sale_date'], unique=False)

    # Create sale_items table
    op.create_table(
        'sale_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sale_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_name', sa.String(length=255), nullable=False),
        sa.Column('product_sku', sa.String(length=100), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('subtotal', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['sale_id'], ['sales.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('quantity > 0', name='check_sale_item_quantity_positive'),
    )
    op.create_index(op.f('ix_sale_items_id'), 'sale_items', ['id'], unique=False)
    op.create_index(op.f('ix_sale_items_sale_id'), 'sale_items', ['sale_id'], unique=False)
    op.create_index(op.f('ix_sale_items_product_id'), 'sale_items', ['product_id'], unique=False)

    # Create reorder_rules table
    op.create_table(
        'reorder_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('min_threshold', sa.Numeric(precision=10, scale=2), nullable=False, default=5),
        sa.Column('target_stock', sa.Numeric(precision=10, scale=2), nullable=False, default=50),
        sa.Column('velocity_days', sa.Numeric(precision=5, scale=2), nullable=False, default=30),
        sa.Column('velocity_multiplier', sa.Numeric(precision=5, scale=2), nullable=False, default=1.0),
        sa.Column('preferred_supplier', sa.String(length=255), nullable=True),
        sa.Column('supplier_lead_time_days', sa.Numeric(precision=5, scale=2), nullable=True, default=7),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_reorder_rules_id'), 'reorder_rules', ['id'], unique=False)
    op.create_index(op.f('ix_reorder_rules_product_id'), 'reorder_rules', ['product_id'], unique=True)


def downgrade() -> None:
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('reorder_rules')
    op.drop_table('sale_items')
    op.drop_table('sales')
    op.drop_table('inventory_transactions')
    op.drop_table('inventory')
    op.drop_table('products')
