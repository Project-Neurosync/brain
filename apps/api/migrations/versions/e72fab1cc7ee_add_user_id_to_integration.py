"""add_user_id_to_integration

Revision ID: e72fab1cc7ee
Revises: 004
Create Date: 2025-07-23 17:43:52.654048

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e72fab1cc7ee'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add user_id column to integrations table
    op.add_column('integrations',
        sa.Column('user_id', sa.UUID(), nullable=True)
    )
    
    # Create foreign key constraint
    op.create_foreign_key(
        'fk_integration_user_id', 'integrations', 'users',
        ['user_id'], ['id']
    )
    
    # Create index for user_id
    op.create_index(op.f('ix_integrations_user_id'), 'integrations', ['user_id'], unique=False)
    
    # Connect to the database and update existing records
    conn = op.get_bind()
    # Get all integrations that have a project_id
    integrations = conn.execute(sa.text(
        "SELECT i.id, p.user_id FROM integrations i JOIN projects p ON i.project_id = p.id"
    )).fetchall()
    
    # Update integrations with project's user_id
    for integration_id, user_id in integrations:
        conn.execute(
            sa.text("UPDATE integrations SET user_id = :user_id WHERE id = :id"),
            {"user_id": user_id, "id": integration_id}
        )
    
    # Make user_id not nullable after backfilling data
    op.alter_column('integrations', 'user_id', nullable=False)


def downgrade() -> None:
    # Drop foreign key constraint first
    op.drop_constraint('fk_integration_user_id', 'integrations', type_='foreignkey')
    
    # Drop index
    op.drop_index(op.f('ix_integrations_user_id'), table_name='integrations')
    
    # Drop user_id column
    op.drop_column('integrations', 'user_id')
