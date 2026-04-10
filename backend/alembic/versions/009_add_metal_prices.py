"""Add metal prices tables

Revision ID: 009
Revises: add_jewelry_001
Create Date: 2026-04-02

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '009'
down_revision = 'add_jewelry_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create metal_prices table
    op.create_table(
        'metal_prices',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('metal_type', sa.String(length=50), nullable=False),
        sa.Column('price_per_gram', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, default='USD'),
        sa.Column('unit', sa.String(length=20), nullable=False, default='gram'),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_metal_prices_metal_type', 'metal_prices', ['metal_type'])
    op.create_index('ix_metal_prices_created_at', 'metal_prices', ['created_at'])

    # Create jewelry_price_logs table
    op.create_table(
        'jewelry_price_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('jewelry_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('old_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('new_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('reason', sa.String(length=255), nullable=True),
        sa.Column('metal_type', sa.String(length=50), nullable=True),
        sa.Column('metal_price_change', sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_jewelry_price_logs_jewelry_id', 'jewelry_price_logs', ['jewelry_id'])
    op.create_index('ix_jewelry_price_logs_created_at', 'jewelry_price_logs', ['created_at'])


def downgrade() -> None:
    op.drop_table('jewelry_price_logs')
    op.drop_index('ix_jewelry_price_logs_created_at', table_name='jewelry_price_logs')
    op.drop_index('ix_jewelry_price_logs_jewelry_id', table_name='jewelry_price_logs')

    op.drop_table('metal_prices')
    op.drop_index('ix_metal_prices_created_at', table_name='metal_prices')
    op.drop_index('ix_metal_prices_metal_type', table_name='metal_prices')
