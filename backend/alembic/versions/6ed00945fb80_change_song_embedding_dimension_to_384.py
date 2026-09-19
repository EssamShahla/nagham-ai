"""change song embedding dimension to 384

Revision ID: 6ed00945fb80
Revises: f09290082e5e
Create Date: 2026-09-16 15:07:39.392383
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


revision: str = "6ed00945fb80"
down_revision: Union[str, Sequence[str], None] = "f09290082e5e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("songs", "embedding")

    op.add_column(
        "songs",
        sa.Column(
            "embedding",
            Vector(384),
            nullable=True
        )
    )


def downgrade() -> None:
    op.drop_column("songs", "embedding")

    op.add_column(
        "songs",
        sa.Column(
            "embedding",
            Vector(1536),
            nullable=True
        )
    )