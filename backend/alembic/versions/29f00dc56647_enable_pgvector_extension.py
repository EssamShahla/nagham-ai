"""enable pgvector extension

Revision ID: 29f00dc56647
Revises: 4e0b9f87717d
Create Date: 2026-09-16 14:25:58.612239

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '29f00dc56647'
down_revision: Union[str, Sequence[str], None] = '4e0b9f87717d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP EXTENSION IF EXISTS vector")
