"""add SKU column to jewelry table

Revision ID: add_jewelry_001
Revises: 007
Create Date: 2026-04-02

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_jewelry_001'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add SKU column to existing jewelry table (nullable to allow existing rows)
    op.add_column('jewelry', sa.Column('sku', sa.String(length=100), nullable=True))

    # Create unique index on SKU
    op.create_index(op.f('ix_jewelry_sku'), 'jewelry', ['sku'], unique=True)

    # Make description NOT NULL (set empty string for existing NULLs first)
    op.execute("UPDATE jewelry SET description = '' WHERE description IS NULL")
    op.alter_column('jewelry', 'description', existing_type=sa.VARCHAR(length=1000), nullable=False)


def downgrade() -> None:
    # Make description nullable again
    op.alter_column('jewelry', 'description', existing_type=sa.VARCHAR(length=1000), nullable=True)

    # Drop unique index on SKU
    op.drop_index(op.f('ix_jewelry_sku'), table_name='jewelry')

    # Drop SKU column
    op.drop_column('jewelry', 'sku')
