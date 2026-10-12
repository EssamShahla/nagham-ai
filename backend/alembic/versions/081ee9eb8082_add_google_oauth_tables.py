"""add google oauth tables

Revision ID: 081ee9eb8082
Revises: b84e6375e4a9
Create Date: 2026-10-10 16:21:05.753991

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '081ee9eb8082'
down_revision: Union[str, Sequence[str], None] = 'b84e6375e4a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# NOTE: autogenerate again picked up unrelated pre-existing drift (see
# 0917822f5f24 / b84e6375e4a9) -- left untouched. Scoped to the 3 new,
# purely-additive Google OAuth tables only.


def upgrade() -> None:
    op.create_table('login_exchange_codes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=255), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('is_used', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_login_exchange_codes_code'), 'login_exchange_codes', ['code'], unique=True)
    op.create_index(op.f('ix_login_exchange_codes_id'), 'login_exchange_codes', ['id'], unique=False)
    op.create_table('oauth_states',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('state', sa.String(length=255), nullable=False),
    sa.Column('nonce', sa.String(length=255), nullable=False),
    sa.Column('code_verifier', sa.String(length=255), nullable=False),
    sa.Column('purpose', sa.String(length=20), nullable=False),
    sa.Column('linking_user_id', sa.Integer(), nullable=True),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('is_used', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['linking_user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_oauth_states_id'), 'oauth_states', ['id'], unique=False)
    op.create_index(op.f('ix_oauth_states_state'), 'oauth_states', ['state'], unique=True)
    op.create_table('pending_google_links',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('link_token', sa.String(length=255), nullable=False),
    sa.Column('google_id', sa.String(length=255), nullable=False),
    sa.Column('google_email', sa.String(length=255), nullable=False),
    sa.Column('google_name', sa.String(length=255), nullable=True),
    sa.Column('existing_user_id', sa.Integer(), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('is_used', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['existing_user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pending_google_links_id'), 'pending_google_links', ['id'], unique=False)
    op.create_index(op.f('ix_pending_google_links_link_token'), 'pending_google_links', ['link_token'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_pending_google_links_link_token'), table_name='pending_google_links')
    op.drop_index(op.f('ix_pending_google_links_id'), table_name='pending_google_links')
    op.drop_table('pending_google_links')
    op.drop_index(op.f('ix_oauth_states_state'), table_name='oauth_states')
    op.drop_index(op.f('ix_oauth_states_id'), table_name='oauth_states')
    op.drop_table('oauth_states')
    op.drop_index(op.f('ix_login_exchange_codes_id'), table_name='login_exchange_codes')
    op.drop_index(op.f('ix_login_exchange_codes_code'), table_name='login_exchange_codes')
    op.drop_table('login_exchange_codes')
