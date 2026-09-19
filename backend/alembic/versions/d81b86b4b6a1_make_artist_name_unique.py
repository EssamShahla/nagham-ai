"""make artist name unique

Revision ID: d81b86b4b6a1
Revises: 6ed00945fb80
Create Date: 2026-09-16 15:45:14.836938

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd81b86b4b6a1'
down_revision: Union[str, Sequence[str], None] = '6ed00945fb80'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_artists_name_ar",
        "artists",
        ["name_ar"]
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_artists_name_ar",
        "artists",
        type_="unique"
    )
