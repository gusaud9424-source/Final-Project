"""add rewards (pending reward box)

Revision ID: 752399d75810
Revises: f07d2a4eadc5
Create Date: 2026-09-29 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '752399d75810'
down_revision = 'f07d2a4eadc5'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('rewards',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('type', sa.Enum('xp', 'point', name='reward_type'), nullable=False),
    sa.Column('amount', sa.Integer(), nullable=False),
    sa.Column('source', sa.String(length=30), nullable=False),
    sa.Column('ref', sa.String(length=60), nullable=False),
    sa.Column('reason', sa.String(length=120), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('claimed_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'source', 'ref', 'type', name='uq_rewards_user_source_ref_type')
    )
    op.create_index('ix_rewards_user_claimed', 'rewards', ['user_id', 'claimed_at'], unique=False)


def downgrade():
    op.drop_index('ix_rewards_user_claimed', table_name='rewards')
    op.drop_table('rewards')
