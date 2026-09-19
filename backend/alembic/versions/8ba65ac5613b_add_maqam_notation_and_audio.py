"""add maqam notation and audio

Revision ID: 8ba65ac5613b
Revises: 3ec79182974e
Create Date: 2026-09-12 15:52:29.052797

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8ba65ac5613b"
down_revision: Union[str, Sequence[str], None] = "3ec79182974e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "maqamat",
        sa.Column(
            "notation_format",
            sa.String(length=50),
            nullable=False,
            server_default="musicxml",
        ),
    )

    op.add_column(
        "maqamat",
        sa.Column(
            "musicxml_data",
            sa.Text(),
            nullable=True,
        ),
    )

    op.add_column(
        "maqamat",
        sa.Column(
            "audio_sample_url",
            sa.String(length=500),
            nullable=True,
        ),
    )

    # Remove the temporary database default.
    # The SQLAlchemy model will still default to "musicxml".
    op.alter_column(
        "maqamat",
        "notation_format",
        server_default=None,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column("maqamat", "audio_sample_url")
    op.drop_column("maqamat", "musicxml_data")
    op.drop_column("maqamat", "notation_format")