"""Add sale returns and RETURN_PENDING status

Revision ID: 005
Revises: 004
Create Date: 2026-04-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    # Check if sale_returns table already exists
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)

    # Check if table exists
    table_exists = 'sale_returns' in inspector.get_table_names()

    # Check if index exists
    index_exists = 'ix_sale_returns_status' in [idx['name'] for idx in inspector.get_indexes('sale_returns')] if table_exists else False

    if not table_exists:
        # Update inventory status constraint to include RETURN_PENDING
        op.drop_constraint('check_status_valid', 'inventory', type_='check')
        op.create_check_constraint(
            'check_status_valid',
            'inventory',
            "status IN ('AVAILABLE', 'SOLD', 'RESERVED', 'RETURN_PENDING')"
        )

        # Create sale_returns table
        op.create_table(
            'sale_returns',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column('sale_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
            sa.Column('product_ids', sa.String(500), nullable=False),
            sa.Column('reason', sa.String(500), nullable=False),
            sa.Column('refund_amount', sa.Numeric(12, 2), nullable=False),
            sa.Column('status', sa.String(20), nullable=False, default='PENDING', index=True),
            sa.Column('requested_by', sa.String(100), nullable=False),
            sa.Column('requested_at', sa.DateTime(), nullable=False, default=sa.func.utcnow()),
            sa.Column('approved_by', sa.String(100), nullable=True),
            sa.Column('approved_at', sa.DateTime(), nullable=True),
            sa.Column('rejected_by', sa.String(100), nullable=True),
            sa.Column('rejected_at', sa.DateTime(), nullable=True),
            sa.Column('rejection_reason', sa.String(500), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.utcnow()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.utcnow(), onupdate=sa.func.utcnow()),
            sa.ForeignKeyConstraint(['sale_id'], ['sales.id'], ondelete='CASCADE'),
        )

    # Create index on status for filtering if not exists
    if not index_exists:
        op.create_index('ix_sale_returns_status', 'sale_returns', ['status'], unique=False)


def downgrade():
    # Drop sale_returns table
    op.drop_table('sale_returns')

    # Revert inventory status constraint
    op.drop_constraint('check_status_valid', 'inventory', type_='check')
    op.create_check_constraint(
        'check_status_valid',
        'inventory',
        "status IN ('AVAILABLE', 'SOLD', 'RESERVED')"
    )
