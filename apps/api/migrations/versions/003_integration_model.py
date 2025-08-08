"""Add Integration model

Revision ID: 003
Revises: 002_project_document_queries
Create Date: 2025-07-22 01:35:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002_project_document_queries'
branch_labels = None
depends_on = None


def upgrade():
    # Create integrations table
    op.create_table('integrations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('type', sa.String(), nullable=False, index=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('status', sa.String(), server_default='disconnected'),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.Column('config', sa.JSON(), server_default='{}'),
        sa.Column('last_sync', sa.DateTime(), nullable=True),
        sa.Column('last_sync_status', sa.String(), nullable=True),
        sa.Column('next_scheduled_sync', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('auto_sync', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
    )
    
    # Create indexes for common query patterns
    op.create_index('idx_integrations_project_id_type', 'integrations', ['project_id', 'type'], unique=True)
    op.create_index('idx_integrations_status', 'integrations', ['status'])


def downgrade():
    # Drop integrations table
    op.drop_index('idx_integrations_status', table_name='integrations')
    op.drop_index('idx_integrations_project_id_type', table_name='integrations')
    op.drop_table('integrations')
