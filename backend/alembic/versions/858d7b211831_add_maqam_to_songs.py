"""add maqam to songs

Revision ID: 858d7b211831
Revises: 7350f58bea4c
Create Date: 2026-09-13 14:44:10.921985

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '858d7b211831'
down_revision: Union[str, Sequence[str], None] = '7350f58bea4c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "songs",
        sa.Column("maqam_id", sa.Integer(), nullable=True)
    )

    op.create_foreign_key(
        "fk_songs_maqam_id_maqamat",
        "songs",
        "maqamat",
        ["maqam_id"],
        ["id"],
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_constraint(
        "fk_songs_maqam_id_maqamat",
        "songs",
        type_="foreignkey"
    )

    op.drop_column("songs", "maqam_id")
