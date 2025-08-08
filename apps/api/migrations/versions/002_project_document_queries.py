"""
Add project, document, and AI query tables
Revision ID: 002_project_document_queries
Revises: 001_initial_schema
Create Date: 2025-07-21
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid

# revision identifiers, used by Alembic
revision = '002_project_document_queries'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    # Create projects table
    op.create_table(
        'projects',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), server_default='active'),
        sa.Column('progress', sa.Integer(), server_default='0'),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.Column('project_metadata', sa.JSON(), nullable=True),
    )
    
    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('content_type', sa.String(), server_default='text/plain'),
        sa.Column('source', sa.String(), nullable=True),
        sa.Column('external_id', sa.String(), nullable=True),
        sa.Column('status', sa.String(), server_default='synced'),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='SET NULL'), nullable=True),
        sa.Column('file_size', sa.BigInteger(), server_default='0'),
        sa.Column('word_count', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.Column('synced_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('document_metadata', sa.JSON(), nullable=True),
    )
    
    # Create AI queries table
    op.create_table(
        'ai_queries',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('response', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), server_default='completed'),
        sa.Column('tokens_used', sa.Integer(), server_default='0'),
        sa.Column('duration_ms', sa.Integer(), server_default='0'),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('query_metadata', sa.JSON(), nullable=True),
    )
    
    # Create indexes for common query patterns
    op.create_index('ix_projects_user_id', 'projects', ['user_id'])
    op.create_index('ix_documents_user_id', 'documents', ['user_id'])
    op.create_index('ix_documents_project_id', 'documents', ['project_id'])
    op.create_index('ix_ai_queries_user_id', 'ai_queries', ['user_id'])
    op.create_index('ix_ai_queries_project_id', 'ai_queries', ['project_id'])
    op.create_index('ix_ai_queries_created_at', 'ai_queries', ['created_at'])


def downgrade():
    op.drop_table('ai_queries')
    op.drop_table('documents')
    op.drop_table('projects')
