"""
Allow projectless integrations by making project_id nullable
This enables OAuth-first flow where users authorize integrations before linking them to projects
"""

import uuid
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# Revision identifiers
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # Modify integrations table to allow projectless integrations
    op.alter_column('integrations', 'project_id',
                   existing_type=UUID(as_uuid=True),
                   nullable=True)
    
    # Drop the unique constraint that includes project_id since it could be null
    op.drop_index('idx_integrations_project_id_type', table_name='integrations')
    
    # Create a new index without uniqueness constraint
    op.create_index('idx_integrations_project_type', 'integrations', ['project_id', 'type'])
    
    # Create index on type alone for queries that find integrations without projects
    op.create_index('idx_integrations_type', 'integrations', ['type'])


def downgrade():
    # Revert changes (note: this will fail if there are any projectless integrations)
    
    # First ensure all integrations have a project_id (would need manual cleanup)
    
    # Drop the new indexes
    op.drop_index('idx_integrations_type', table_name='integrations')
    op.drop_index('idx_integrations_project_type', table_name='integrations')
    
    # Recreate the original unique constraint
    op.create_index('idx_integrations_project_id_type', 'integrations', ['project_id', 'type'], unique=True)
    
    # Make project_id non-nullable again
    op.alter_column('integrations', 'project_id',
                   existing_type=UUID(as_uuid=True),
                   nullable=False)
