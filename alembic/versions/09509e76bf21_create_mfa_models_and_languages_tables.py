"""create_mfa_models_and_languages_tables

Revision ID: 09509e76bf21
Revises: 001
Create Date: 2025-08-03 23:59:51.937903

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '09509e76bf21'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create languages table
    op.create_table('languages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_languages_code'), 'languages', ['code'], unique=True)
    op.create_index(op.f('ix_languages_id'), 'languages', ['id'], unique=False)
    
    # Create mfa_models table (final version with variant, without download_url)
    op.create_table('mfa_models',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('model_type', sa.Enum('ACOUSTIC', 'G2P', 'DICTIONARY', name='modeltype'), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('variant', sa.String(length=100), nullable=True),
        sa.Column('language_id', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['language_id'], ['languages.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mfa_models_id'), 'mfa_models', ['id'], unique=False)


def downgrade() -> None:
    # Drop mfa_models table
    op.drop_index(op.f('ix_mfa_models_id'), table_name='mfa_models')
    op.drop_table('mfa_models')
    
    # Drop languages table
    op.drop_index(op.f('ix_languages_id'), table_name='languages')
    op.drop_index(op.f('ix_languages_code'), table_name='languages')
    op.drop_table('languages')
