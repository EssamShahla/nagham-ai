"""change scale patterns to json

Revision ID: 7350f58bea4c
Revises: 8ba65ac5613b
Create Date: 2026-09-12 16:31:43.684747
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7350f58bea4c"
down_revision: Union[str, Sequence[str], None] = "8ba65ac5613b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.alter_column(
        "ajnas",
        "scale_pattern",
        existing_type=sa.VARCHAR(length=255),
        type_=sa.JSON(),
        existing_nullable=True,
        postgresql_using="scale_pattern::json"
    )

    op.alter_column(
        "maqamat",
        "scale_pattern",
        existing_type=sa.VARCHAR(length=255),
        type_=sa.JSON(),
        existing_nullable=True,
        postgresql_using="scale_pattern::json"
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.alter_column(
        "maqamat",
        "scale_pattern",
        existing_type=sa.JSON(),
        type_=sa.VARCHAR(length=255),
        existing_nullable=True,
        postgresql_using="scale_pattern::text"
    )

    op.alter_column(
        "ajnas",
        "scale_pattern",
        existing_type=sa.JSON(),
        type_=sa.VARCHAR(length=255),
        existing_nullable=True,
        postgresql_using="scale_pattern::text"
    )