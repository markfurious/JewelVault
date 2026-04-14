"""add agent audit logs

Revision ID: 011
Revises: 010
Create Date: 2026-04-13

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create agent_audit_logs table
    op.create_table('agent_audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_name', sa.String(length=255), nullable=False),
        sa.Column('action_type', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('entity_type', sa.String(length=100), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False, default=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('dry_run', sa.Boolean(), nullable=False, default=False),
        sa.Column('executed_at', sa.DateTime(), nullable=False, default=sa.func.utcnow()),
        sa.Column('reference_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reference_type', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_audit_logs_agent_name'), 'agent_audit_logs', ['agent_name'], unique=False)
    op.create_index(op.f('ix_agent_audit_logs_entity_id'), 'agent_audit_logs', ['entity_id'], unique=False)
    op.create_index(op.f('ix_agent_audit_logs_executed_at'), 'agent_audit_logs', ['executed_at'], unique=False)
    op.create_index(op.f('ix_agent_audit_logs_id'), 'agent_audit_logs', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_agent_audit_logs_executed_at'), table_name='agent_audit_logs')
    op.drop_index(op.f('ix_agent_audit_logs_id'), table_name='agent_audit_logs')
    op.drop_index(op.f('ix_agent_audit_logs_entity_id'), table_name='agent_audit_logs')
    op.drop_index(op.f('ix_agent_audit_logs_agent_name'), table_name='agent_audit_logs')
    op.drop_table('agent_audit_logs')
