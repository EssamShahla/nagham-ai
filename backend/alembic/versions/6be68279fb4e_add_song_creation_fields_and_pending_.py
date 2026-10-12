"""add song creation fields and pending_song_creations table

Revision ID: 6be68279fb4e
Revises: 3eff4281930a
Create Date: 2026-10-12 00:00:00.000000

Purely additive. Two new nullable columns on `songs` (`lyricist_name`,
`musical_key`) and a new table `pending_song_creations` -- the
server-authoritative, single-use record the conversational song-creation
agent (app/ai/song_creation.py) uses to authorize a confirmed write,
modeled directly on the existing `login_exchange_codes`/
`pending_google_links` pattern.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '6be68279fb4e'
down_revision: Union[str, Sequence[str], None] = '3eff4281930a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('songs', sa.Column('lyricist_name', sa.String(length=255), nullable=True))
    op.add_column('songs', sa.Column('musical_key', sa.String(length=100), nullable=True))

    op.create_table(
        'pending_song_creations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_used', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        'ix_pending_song_creations_id', 'pending_song_creations', ['id']
    )
    op.create_index(
        'ix_pending_song_creations_token', 'pending_song_creations', ['token'], unique=True
    )


def downgrade() -> None:
    op.drop_index('ix_pending_song_creations_token', table_name='pending_song_creations')
    op.drop_index('ix_pending_song_creations_id', table_name='pending_song_creations')
    op.drop_table('pending_song_creations')
    op.drop_column('songs', 'musical_key')
    op.drop_column('songs', 'lyricist_name')
