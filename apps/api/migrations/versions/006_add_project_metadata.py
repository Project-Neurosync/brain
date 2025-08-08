"""
Add project_metadata column to projects table
This column stores additional metadata about projects for analytics and configuration
"""

import uuid
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# Revision identifiers
revision = '006'
down_revision = 'e72fab1cc7ee'
branch_labels = None
depends_on = None


def upgrade():
    # Add project_metadata column to projects table
    op.add_column('projects', sa.Column('project_metadata', JSON, nullable=True))


def downgrade():
    # Remove project_metadata column from projects table
    op.drop_column('projects', 'project_metadata')
