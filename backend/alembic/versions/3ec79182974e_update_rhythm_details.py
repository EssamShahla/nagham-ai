"""update rhythm details

Revision ID: 3ec79182974e
Revises: 7028d4afcdc1
Create Date: 2026-09-12 15:44:30.667916

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3ec79182974e"
down_revision: Union[str, Sequence[str], None] = "7028d4afcdc1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Rename old name column to name_ar
    # This preserves any existing rhythm names.
    op.alter_column(
        "rhythms",
        "name",
        new_column_name="name_ar",
        existing_type=sa.String(length=100),
        existing_nullable=False,
    )

    # Add English name
    op.add_column(
        "rhythms",
        sa.Column(
            "name_en",
            sa.String(length=100),
            nullable=True,
        ),
    )

    # Musical meter, e.g. 4/4, 6/8, 10/8
    op.add_column(
        "rhythms",
        sa.Column(
            "time_signature",
            sa.String(length=20),
            nullable=True,
        ),
    )

    # Human / AI readable rhythm pattern
    # Example: D T - T D - T -
    op.add_column(
        "rhythms",
        sa.Column(
            "pattern_text",
            sa.String(length=255),
            nullable=True,
        ),
    )

    # Format used for musical notation
    # Existing rows temporarily receive "musicxml"
    op.add_column(
        "rhythms",
        sa.Column(
            "notation_format",
            sa.String(length=50),
            nullable=False,
            server_default="musicxml",
        ),
    )

    # Full MusicXML notation data
    op.add_column(
        "rhythms",
        sa.Column(
            "musicxml_data",
            sa.Text(),
            nullable=True,
        ),
    )

    # URL/path for rhythm audio sample
    op.add_column(
        "rhythms",
        sa.Column(
            "audio_sample_url",
            sa.String(length=500),
            nullable=True,
        ),
    )

    # BPM of the stored audio sample
    op.add_column(
        "rhythms",
        sa.Column(
            "sample_bpm",
            sa.Integer(),
            nullable=True,
        ),
    )

    # Extra musical notes
    op.add_column(
        "rhythms",
        sa.Column(
            "notes",
            sa.Text(),
            nullable=True,
        ),
    )

    # Remove database-level temporary default.
    # The Python model will still default to "musicxml".
    op.alter_column(
        "rhythms",
        "notation_format",
        server_default=None,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column("rhythms", "notes")
    op.drop_column("rhythms", "sample_bpm")
    op.drop_column("rhythms", "audio_sample_url")
    op.drop_column("rhythms", "musicxml_data")
    op.drop_column("rhythms", "notation_format")
    op.drop_column("rhythms", "pattern_text")
    op.drop_column("rhythms", "time_signature")
    op.drop_column("rhythms", "name_en")

    # Rename name_ar back to the original name column
    op.alter_column(
        "rhythms",
        "name_ar",
        new_column_name="name",
        existing_type=sa.String(length=100),
        existing_nullable=False,
    )