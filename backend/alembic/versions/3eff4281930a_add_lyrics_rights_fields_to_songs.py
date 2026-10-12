"""add lyrics rights fields to songs

Revision ID: 3eff4281930a
Revises: 081ee9eb8082
Create Date: 2026-10-12 00:00:00.000000

Purely additive, nullable columns. `lyrics_license` records whether the
stored `lyrics` text (used for semantic-search embeddings regardless of
license) may ever be displayed verbatim to a user:
  - "public_domain" / "licensed" -> displayable, `lyrics_rights_note` holds
    attribution.
  - "restricted" or NULL (unset) -> never displayed verbatim. Application
    code treats missing/unrecognized values as restricted -- display
    rights are never assumed.

Backfills the one pre-existing song that already has real lyrics text
(id 146, "انت عمري") as "restricted", since no license grant exists for
it. No lyrics text is modified or removed.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '3eff4281930a'
down_revision: Union[str, Sequence[str], None] = '081ee9eb8082'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('songs', sa.Column('lyrics_license', sa.String(length=30), nullable=True))
    op.add_column('songs', sa.Column('lyrics_rights_note', sa.Text(), nullable=True))

    op.execute(
        """
        UPDATE songs
        SET lyrics_license = 'restricted',
            lyrics_rights_note = 'حقوق النشر محفوظة لأصحابها؛ لا يوجد ترخيص عرض لهذا النص في قاعدة البيانات، وهو محفوظ لأغراض البحث الدلالي (embeddings) فقط.'
        WHERE lyrics IS NOT NULL
        """
    )


def downgrade() -> None:
    op.drop_column('songs', 'lyrics_rights_note')
    op.drop_column('songs', 'lyrics_license')
