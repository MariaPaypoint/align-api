"""merge_heads

Revision ID: 2fd325322e29
Revises: 001_reorder_mfa, 4ab3bf5ca347
Create Date: 2025-08-17 15:39:30.386474

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2fd325322e29'
down_revision: Union[str, None] = ('001_reorder_mfa', '4ab3bf5ca347')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
