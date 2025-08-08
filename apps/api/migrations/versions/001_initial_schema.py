"""
Initial database schema for NeuroSync API
Creates users, user_sessions, token_usage, and subscriptions tables
"""

import uuid
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from datetime import datetime

# revision identifiers, used by Alembic
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('email', sa.String(), nullable=False, unique=True, index=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_admin', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow),
        sa.Column('monthly_token_quota', sa.Integer(), default=5000),
        sa.Column('bonus_tokens', sa.Integer(), default=0),
        sa.Column('user_metadata', postgresql.JSON, nullable=True),
    )
    
    # Create user_sessions table
    op.create_table(
        'user_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('refresh_token', sa.String(), unique=True, nullable=False),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
    )
    
    # Create token_usage table
    op.create_table(
        'token_usage',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tokens_used', sa.Integer(), default=0),
        sa.Column('request_type', sa.String(), nullable=False),
        sa.Column('endpoint', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), default=datetime.utcnow),
    )
    
    # Create subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('plan_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('started_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('ends_at', sa.DateTime(), nullable=True),
        sa.Column('payment_id', sa.String(), nullable=True),
        sa.Column('payment_provider', sa.String(), default='razorpay'),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('billing_cycle', sa.String(), default='monthly'),
    )

def downgrade():
    # Drop tables in reverse order of creation to respect foreign key constraints
    op.drop_table('subscriptions')
    op.drop_table('token_usage')
    op.drop_table('user_sessions')
    op.drop_table('users')
