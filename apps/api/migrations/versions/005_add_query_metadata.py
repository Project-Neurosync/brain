"""
Add query_metadata column to ai_queries table
This column stores additional metadata about AI queries for analytics and debugging
"""

import uuid
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# Revision identifiers
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    # Add query_metadata column to ai_queries table
    op.add_column('ai_queries', sa.Column('query_metadata', JSON, nullable=True))


def downgrade():
    # Remove query_metadata column from ai_queries table
    op.drop_column('ai_queries', 'query_metadata')
