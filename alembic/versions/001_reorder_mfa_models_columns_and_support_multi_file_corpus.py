"""reorder_mfa_models_columns_and_support_multi_file_corpus

Revision ID: 001_reorder_mfa
Revises: 72c3147b9c54
Create Date: 2025-08-17 14:56:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_reorder_mfa'
down_revision: Union[str, None] = '72c3147b9c54'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE mfa_models MODIFY COLUMN variant VARCHAR(100) AFTER model_type")


def downgrade() -> None:
    pass
    