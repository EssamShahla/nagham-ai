"""add song source details

Revision ID: 7b063b248c76
Revises: 858d7b211831
Create Date: 2026-09-13 15:15:19.468836

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b063b248c76'
down_revision: Union[str, Sequence[str], None] = '858d7b211831'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "song_sources",
        sa.Column("title", sa.String(length=255), nullable=True)
    )

    op.add_column(
        "song_sources",
        sa.Column("created_by", sa.Integer(), nullable=False)
    )

    op.create_foreign_key(
        "fk_song_sources_created_by_users",
        "song_sources",
        "users",
        ["created_by"],
        ["id"],
    )

    op.alter_column(
        "song_sources",
        "source_type",
        existing_type=sa.VARCHAR(length=100),
        type_=sa.String(length=50),
        existing_nullable=True,
        nullable=False
    )

    op.alter_column(
        "song_sources",
        "source_url",
        existing_type=sa.VARCHAR(length=500),
        existing_nullable=False,
        nullable=True
    )

    op.drop_constraint(
        "song_sources_song_id_fkey",
        "song_sources",
        type_="foreignkey"
    )

    op.create_foreign_key(
        "fk_song_sources_song_id_songs_cascade",
        "song_sources",
        "songs",
        ["song_id"],
        ["id"],
        ondelete="CASCADE"
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.execute(
        "UPDATE song_sources SET source_url = '' WHERE source_url IS NULL"
    )

    op.drop_constraint(
        "fk_song_sources_song_id_songs_cascade",
        "song_sources",
        type_="foreignkey"
    )

    op.create_foreign_key(
        "song_sources_song_id_fkey",
        "song_sources",
        "songs",
        ["song_id"],
        ["id"],
    )

    op.alter_column(
        "song_sources",
        "source_url",
        existing_type=sa.VARCHAR(length=500),
        existing_nullable=True,
        nullable=False
    )

    op.alter_column(
        "song_sources",
        "source_type",
        existing_type=sa.String(length=50),
        type_=sa.VARCHAR(length=100),
        existing_nullable=False,
        nullable=True
    )

    op.drop_constraint(
        "fk_song_sources_created_by_users",
        "song_sources",
        type_="foreignkey"
    )

    op.drop_column("song_sources", "created_by")
    op.drop_column("song_sources", "title")
