"""Fix inventory status constraint to include RETURN_PENDING

Revision ID: 007
Revises: 006
Create Date: 2026-04-02

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    # Drop old constraint and create new one with RETURN_PENDING
    op.drop_constraint('check_status_valid', 'inventory', type_='check')
    op.create_check_constraint(
        'check_status_valid',
        'inventory',
        "status IN ('AVAILABLE', 'SOLD', 'RESERVED', 'RETURN_PENDING')"
    )


def downgrade():
    # Revert to old constraint without RETURN_PENDING
    op.drop_constraint('check_status_valid', 'inventory', type_='check')
    op.create_check_constraint(
        'check_status_valid',
        'inventory',
        "status IN ('AVAILABLE', 'SOLD', 'RESERVED')"
    )
