"""Add companies table and company_id to users

Revision ID: 006
Revises: 005
Create Date: 2026-04-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    # Create companies table
    op.create_table(
        'companies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('tax_id', sa.String(100), nullable=True),
        sa.Column('currency', sa.String(10), nullable=False, default='USD'),
        sa.Column('timezone', sa.String(50), nullable=False, default='UTC'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.utcnow()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.utcnow(), onupdate=sa.func.utcnow()),
    )

    # Create indexes
    op.create_index('ix_companies_name', 'companies', ['name'], unique=True)
    op.create_index('ix_companies_code', 'companies', ['code'], unique=True)

    # Add company_id to users table
    op.add_column('users', sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index('ix_users_company_id', 'users', ['company_id'])
    op.create_foreign_key('fk_users_company_id', 'users', 'companies', ['company_id'], ['id'])


def downgrade():
    # Remove company_id from users
    op.drop_constraint('fk_users_company_id', 'users', type_='foreignkey')
    op.drop_index('ix_users_company_id', 'users')
    op.drop_column('users', 'company_id')

    # Drop companies table
    op.drop_index('ix_companies_code', 'companies')
    op.drop_index('ix_companies_name', 'companies')
    op.drop_table('companies')
