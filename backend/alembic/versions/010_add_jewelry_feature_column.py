"""add jewelry feature column

Revision ID: 010
Revises: 009_add_metal_prices
Create Date: 2026-04-02

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '010'
down_revision = '009_add_metal_prices'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('jewelry', sa.Column('feature', sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column('jewelry', 'feature')
