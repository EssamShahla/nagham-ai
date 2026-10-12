"""add maqam ajnas breakdown table

Revision ID: 0917822f5f24
Revises: a1b2c3d4e5f6
Create Date: 2026-10-10 13:51:51.928877

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0917822f5f24'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# NOTE: autogenerate also picked up unrelated pre-existing drift between the
# models and the DB (dropping users.profile_image_url, index changes on
# song_sections) -- that drift is left untouched here. This migration is
# intentionally scoped to only the new, purely-additive maqam_ajnas table.


def upgrade() -> None:
    op.create_table(
        'maqam_ajnas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('maqam_id', sa.Integer(), nullable=False),
        sa.Column('jins_id', sa.Integer(), nullable=False),
        sa.Column('start_degree', sa.Integer(), nullable=False),
        sa.Column('is_primary_alternative', sa.Boolean(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['jins_id'], ['ajnas.id']),
        sa.ForeignKeyConstraint(['maqam_id'], ['maqamat.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_maqam_ajnas_id'), 'maqam_ajnas', ['id'], unique=False)
    op.create_index(op.f('ix_maqam_ajnas_maqam_id'), 'maqam_ajnas', ['maqam_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_maqam_ajnas_maqam_id'), table_name='maqam_ajnas')
    op.drop_index(op.f('ix_maqam_ajnas_id'), table_name='maqam_ajnas')
    op.drop_table('maqam_ajnas')
