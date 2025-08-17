"""step2_create_user_system

Revision ID: step2_users
Revises: 72c3147b9c54
Create Date: 2025-08-17 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'step2_users'
down_revision: Union[str, None] = '72c3147b9c54'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create subscription_types table
    op.create_table('subscription_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=False),
        sa.Column('total_storage_limit', sa.BigInteger(), nullable=False),
        sa.Column('max_concurrent_tasks', sa.Integer(), nullable=False),
        sa.Column('price_monthly', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_subscription_types_name'), 'subscription_types', ['name'], unique=True)
    
    # Insert default subscription types
    op.execute("""
        INSERT INTO subscription_types (name, display_name, total_storage_limit, max_concurrent_tasks, price_monthly, is_active)
        VALUES 
        ('free', 'Free', 1073741824, 1, 0.00, true),
        ('basic', 'Basic', 10737418240, 3, 9.99, true),
        ('pro', 'Pro', 107374182400, 10, 29.99, true),
        ('enterprise', 'Enterprise', 1099511627776, 50, 99.99, true)
    """)
    
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.Enum('user', 'admin', name='userrole'), nullable=False, default='user'),
        sa.Column('subscription_type_id', sa.Integer(), nullable=False),
        sa.Column('used_storage', sa.BigInteger(), nullable=False, default=0),
        sa.Column('subscription_ends_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['subscription_type_id'], ['subscription_types.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    
    # Create file_storage_metadata table
    op.create_table('file_storage_metadata',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=True),
        sa.Column('file_type', sa.Enum('audio', 'text', 'result', name='filetype'), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('storage_path', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_accessed', sa.DateTime(timezone=True), nullable=True),
        sa.Column('access_count', sa.Integer(), nullable=False, default=0),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['task_id'], ['alignment_queue.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_file_storage_metadata_user_id'), 'file_storage_metadata', ['user_id'])
    op.create_index(op.f('ix_file_storage_metadata_task_id'), 'file_storage_metadata', ['task_id'])
    op.create_index(op.f('ix_file_storage_metadata_file_type'), 'file_storage_metadata', ['file_type'])
    
    # Add user_id and celery_task_id to alignment_queue
    op.add_column('alignment_queue', sa.Column('user_id', sa.Integer(), nullable=True))
    op.add_column('alignment_queue', sa.Column('celery_task_id', sa.String(length=155), nullable=True))
    
    # Add foreign key constraint for user_id
    op.create_foreign_key('fk_alignment_queue_user_id', 'alignment_queue', 'users', ['user_id'], ['id'])
    
    # Add model FK columns to replace string fields
    op.add_column('alignment_queue', sa.Column('acoustic_model_id', sa.Integer(), nullable=True))
    op.add_column('alignment_queue', sa.Column('dictionary_model_id', sa.Integer(), nullable=True))
    op.add_column('alignment_queue', sa.Column('g2p_model_id', sa.Integer(), nullable=True))
    
    # Add foreign key constraints for models
    op.create_foreign_key('fk_alignment_queue_acoustic_model_id', 'alignment_queue', 'mfa_models', ['acoustic_model_id'], ['id'])
    op.create_foreign_key('fk_alignment_queue_dictionary_model_id', 'alignment_queue', 'mfa_models', ['dictionary_model_id'], ['id'])
    op.create_foreign_key('fk_alignment_queue_g2p_model_id', 'alignment_queue', 'mfa_models', ['g2p_model_id'], ['id'])


def downgrade() -> None:
    # Drop foreign key constraints
    op.drop_constraint('fk_alignment_queue_g2p_model_id', 'alignment_queue', type_='foreignkey')
    op.drop_constraint('fk_alignment_queue_dictionary_model_id', 'alignment_queue', type_='foreignkey')
    op.drop_constraint('fk_alignment_queue_acoustic_model_id', 'alignment_queue', type_='foreignkey')
    op.drop_constraint('fk_alignment_queue_user_id', 'alignment_queue', type_='foreignkey')
    
    # Drop added columns
    op.drop_column('alignment_queue', 'g2p_model_id')
    op.drop_column('alignment_queue', 'dictionary_model_id')
    op.drop_column('alignment_queue', 'acoustic_model_id')
    op.drop_column('alignment_queue', 'celery_task_id')
    op.drop_column('alignment_queue', 'user_id')
    
    # Drop file_storage_metadata table
    op.drop_index(op.f('ix_file_storage_metadata_file_type'), table_name='file_storage_metadata')
    op.drop_index(op.f('ix_file_storage_metadata_task_id'), table_name='file_storage_metadata')
    op.drop_index(op.f('ix_file_storage_metadata_user_id'), table_name='file_storage_metadata')
    op.drop_table('file_storage_metadata')
    
    # Drop users table
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    
    # Drop subscription_types table
    op.drop_index(op.f('ix_subscription_types_name'), table_name='subscription_types')
    op.drop_table('subscription_types')
