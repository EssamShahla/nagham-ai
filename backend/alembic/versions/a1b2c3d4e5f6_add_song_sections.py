"""add song sections and profile image url

Revision ID: a1b2c3d4e5f6
Revises: d81b86b4b6a1
Create Date: 2026-09-19 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'd81b86b4b6a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'song_sections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('song_id', sa.Integer(), nullable=False),
        sa.Column('sequence_order', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('section_type', sa.String(length=50), nullable=True),
        sa.Column('maqam_id', sa.Integer(), nullable=True),
        sa.Column('rhythm_id', sa.Integer(), nullable=True),
        sa.Column('tonic', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['song_id'],
            ['songs.id'],
            ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['maqam_id'],
            ['maqamat.id'],
        ),
        sa.ForeignKeyConstraint(
            ['rhythm_id'],
            ['rhythms.id'],
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_song_sections_song_id', 'song_id'),
        sa.Index('ix_song_sections_maqam_id', 'maqam_id'),
    )

    op.add_column(
        'users',
        sa.Column(
            'profile_image_url',
            sa.String(length=500),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column('users', 'profile_image_url')

    op.drop_table('song_sections')
