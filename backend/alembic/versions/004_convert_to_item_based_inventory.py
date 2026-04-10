"""Convert to item-based inventory model

Revision ID: 004
Revises: 003
Create Date: 2026-03-31

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # Add new status column
    op.add_column('inventory', sa.Column('status', sa.String(20), nullable=True))

    # Set default status based on existing quantity
    # Items with quantity > 0 become AVAILABLE, otherwise AVAILABLE (for restock)
    op.execute("""
        UPDATE inventory
        SET status = CASE
            WHEN quantity > 0 THEN 'AVAILABLE'
            ELSE 'AVAILABLE'
        END
    """)

    # Make status non-nullable with default
    op.alter_column('inventory', 'status', nullable=False, server_default='AVAILABLE')

    # Add status check constraint
    op.create_check_constraint(
        'check_status_valid',
        'inventory',
        "status IN ('AVAILABLE', 'SOLD', 'RESERVED')"
    )

    # Update inventory_transactions table
    op.add_column('inventory_transactions', sa.Column('status_before', sa.String(20), nullable=True))
    op.add_column('inventory_transactions', sa.Column('status_after', sa.String(20), nullable=True))

    # Migrate existing transaction records (set placeholder values)
    op.execute("""
        UPDATE inventory_transactions
        SET status_before = 'AVAILABLE', status_after = 'AVAILABLE'
        WHERE status_before IS NULL
    """)

    # Make new columns non-nullable
    op.alter_column('inventory_transactions', 'status_before', nullable=False)
    op.alter_column('inventory_transactions', 'status_after', nullable=False)

    # Drop old quantity columns
    op.drop_constraint('check_quantity_non_negative', 'inventory', type_='check')
    op.drop_constraint('check_reserved_non_negative', 'inventory', type_='check')
    op.drop_column('inventory', 'quantity')
    op.drop_column('inventory', 'reserved_quantity')

    # Drop old quantity columns from transactions
    op.drop_column('inventory_transactions', 'quantity_change')
    op.drop_column('inventory_transactions', 'quantity_before')
    op.drop_column('inventory_transactions', 'quantity_after')

    # Create index on status for faster filtering
    op.create_index('ix_inventory_status', 'inventory', ['status'], unique=False)


def downgrade():
    # Drop status index
    op.drop_index('ix_inventory_status', table_name='inventory')

    # Re-add quantity columns
    op.add_column('inventory', sa.Column('quantity', sa.Numeric(12, 2), nullable=True, default=0))
    op.add_column('inventory', sa.Column('reserved_quantity', sa.Numeric(12, 2), nullable=True, default=0))

    # Set default quantities based on status
    op.execute("""
        UPDATE inventory
        SET quantity = CASE
            WHEN status = 'AVAILABLE' THEN 1
            WHEN status = 'SOLD' THEN 0
            WHEN status = 'RESERVED' THEN 1
            ELSE 0
        END,
        reserved_quantity = CASE
            WHEN status = 'RESERVED' THEN 1
            ELSE 0
        END
    """)

    # Make quantity columns non-nullable
    op.alter_column('inventory', 'quantity', nullable=False)
    op.alter_column('inventory', 'reserved_quantity', nullable=False)

    # Re-add quantity constraints
    op.create_check_constraint(
        'check_quantity_non_negative',
        'inventory',
        'quantity >= 0'
    )
    op.create_check_constraint(
        'check_reserved_non_negative',
        'inventory',
        'reserved_quantity >= 0'
    )

    # Drop status column
    op.drop_constraint('check_status_valid', 'inventory', type_='check')
    op.drop_column('inventory', 'status')

    # Re-add quantity columns to transactions
    op.add_column('inventory_transactions', sa.Column('quantity_change', sa.Numeric(12, 2), nullable=True))
    op.add_column('inventory_transactions', sa.Column('quantity_before', sa.Numeric(12, 2), nullable=True))
    op.add_column('inventory_transactions', sa.Column('quantity_after', sa.Numeric(12, 2), nullable=True))

    # Set placeholder values for transaction quantity fields
    op.execute("""
        UPDATE inventory_transactions
        SET quantity_change = 0, quantity_before = 0, quantity_after = 0
        WHERE quantity_change IS NULL
    """)

    # Make transaction quantity columns non-nullable
    op.alter_column('inventory_transactions', 'quantity_change', nullable=False)
    op.alter_column('inventory_transactions', 'quantity_before', nullable=False)
    op.alter_column('inventory_transactions', 'quantity_after', nullable=False)

    # Drop status columns from transactions
    op.drop_column('inventory_transactions', 'status_before')
    op.drop_column('inventory_transactions', 'status_after')
