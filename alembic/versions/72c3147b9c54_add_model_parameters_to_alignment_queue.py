"""add_model_parameters_to_alignment_queue

Revision ID: 72c3147b9c54
Revises: 09509e76bf21
Create Date: 2025-08-04 04:05:04.660849

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '72c3147b9c54'
down_revision: Union[str, None] = '09509e76bf21'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add model parameter columns to alignment_queue table
    op.add_column('alignment_queue', sa.Column('acoustic_model_name', sa.String(255), nullable=True))
    op.add_column('alignment_queue', sa.Column('acoustic_model_version', sa.String(50), nullable=True))
    op.add_column('alignment_queue', sa.Column('dictionary_name', sa.String(255), nullable=True))
    op.add_column('alignment_queue', sa.Column('dictionary_version', sa.String(50), nullable=True))
    op.add_column('alignment_queue', sa.Column('g2p_model_name', sa.String(255), nullable=True))
    op.add_column('alignment_queue', sa.Column('g2p_model_version', sa.String(50), nullable=True))
    
    # After adding columns, we need to make acoustic_model_name, acoustic_model_version,
    # dictionary_name, and dictionary_version NOT NULL for new records
    # But first we need to update existing records with default values
    
    # Update existing records with placeholder values
    op.execute("""
        UPDATE alignment_queue 
        SET acoustic_model_name = 'default_acoustic',
            acoustic_model_version = '1.0',
            dictionary_name = 'default_dictionary',
            dictionary_version = '1.0'
        WHERE acoustic_model_name IS NULL
    """)
    
    # Now make the required columns NOT NULL
    op.alter_column('alignment_queue', 'acoustic_model_name', 
                   existing_type=sa.String(255), nullable=False)
    op.alter_column('alignment_queue', 'acoustic_model_version', 
                   existing_type=sa.String(50), nullable=False)
    op.alter_column('alignment_queue', 'dictionary_name', 
                   existing_type=sa.String(255), nullable=False)
    op.alter_column('alignment_queue', 'dictionary_version', 
                   existing_type=sa.String(50), nullable=False)


def downgrade() -> None:
    # Remove model parameter columns
    op.drop_column('alignment_queue', 'g2p_model_version')
    op.drop_column('alignment_queue', 'g2p_model_name')
    op.drop_column('alignment_queue', 'dictionary_version')
    op.drop_column('alignment_queue', 'dictionary_name')
    op.drop_column('alignment_queue', 'acoustic_model_version')
    op.drop_column('alignment_queue', 'acoustic_model_name')
