"""add degree_names to maqamat and ajnas

Revision ID: b84e6375e4a9
Revises: 0917822f5f24
Create Date: 2026-10-10 14:01:01.877528

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b84e6375e4a9'
down_revision: Union[str, Sequence[str], None] = '0917822f5f24'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# NOTE: autogenerate again picked up unrelated pre-existing drift (see
# 0917822f5f24) -- left untouched. Scoped to the two new, purely-additive
# nullable columns only.


def upgrade() -> None:
    op.add_column('ajnas', sa.Column('degree_names', sa.JSON(), nullable=True))
    op.add_column('maqamat', sa.Column('degree_names', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('maqamat', 'degree_names')
    op.drop_column('ajnas', 'degree_names')
