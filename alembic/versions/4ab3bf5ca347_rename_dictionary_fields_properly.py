"""rename_dictionary_fields_properly

Revision ID: 4ab3bf5ca347
Revises: 72c3147b9c54
Create Date: 2025-08-04 04:55:46.845184

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4ab3bf5ca347'
down_revision: Union[str, None] = '72c3147b9c54'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns
    op.add_column('alignment_queue', sa.Column('dictionary_model_name', sa.String(255), nullable=True))
    op.add_column('alignment_queue', sa.Column('dictionary_model_version', sa.String(50), nullable=True))
    
    # Copy data from old columns to new columns
    op.execute("""
        UPDATE alignment_queue 
        SET dictionary_model_name = dictionary_name,
            dictionary_model_version = dictionary_version
    """)
    
    # Make new columns NOT NULL
    op.alter_column('alignment_queue', 'dictionary_model_name', nullable=False, existing_type=sa.String(255))
    op.alter_column('alignment_queue', 'dictionary_model_version', nullable=False, existing_type=sa.String(50))
    
    # Drop old columns
    op.drop_column('alignment_queue', 'dictionary_name')
    op.drop_column('alignment_queue', 'dictionary_version')
    

def downgrade() -> None:
    # Add old columns back
    op.add_column('alignment_queue', sa.Column('dictionary_name', sa.String(255), nullable=True))
    op.add_column('alignment_queue', sa.Column('dictionary_version', sa.String(50), nullable=True))
    
    # Copy data back
    op.execute("""
        UPDATE alignment_queue 
        SET dictionary_name = dictionary_model_name,
            dictionary_version = dictionary_model_version
    """)
    
    # Make old columns NOT NULL
    op.alter_column('alignment_queue', 'dictionary_name', nullable=False, existing_type=sa.String(255))
    op.alter_column('alignment_queue', 'dictionary_version', nullable=False, existing_type=sa.String(50))
    
    # Drop new columns
    op.drop_column('alignment_queue', 'dictionary_model_name')
    op.drop_column('alignment_queue', 'dictionary_model_version')
    