"""add agent requests table

Revision ID: 012
Revises: 011
Create Date: 2026-04-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '012'
down_revision = '011'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create agent_requests table (using String instead of Enum for simplicity)
    op.create_table('agent_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('request_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('agent_name', sa.String(length=255), nullable=False),
        sa.Column('entity_type', sa.String(length=100), nullable=True),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('request_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('proposed_action', sa.Text(), nullable=False),
        sa.Column('impact_summary', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, default='pending'),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('executed_at', sa.DateTime(), nullable=True),
        sa.Column('execution_result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.utcnow()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_requests_id'), 'agent_requests', ['id'], unique=False)
    op.create_index(op.f('ix_agent_requests_status'), 'agent_requests', ['status'], unique=False)
    op.create_index(op.f('ix_agent_requests_entity_id'), 'agent_requests', ['entity_id'], unique=False)
    op.create_index(op.f('ix_agent_requests_created_at'), 'agent_requests', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_agent_requests_created_at'), table_name='agent_requests')
    op.drop_index(op.f('ix_agent_requests_entity_id'), table_name='agent_requests')
    op.drop_index(op.f('ix_agent_requests_status'), table_name='agent_requests')
    op.drop_index(op.f('ix_agent_requests_id'), table_name='agent_requests')
    op.drop_table('agent_requests')
