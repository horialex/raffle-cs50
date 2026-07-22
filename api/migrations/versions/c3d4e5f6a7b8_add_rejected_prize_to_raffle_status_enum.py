"""add rejected_prize to raffle status enum

Revision ID: c3d4e5f6a7b8
Revises: fa6d098142bf
Create Date: 2026-07-20 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3d4e5f6a7b8'
down_revision = 'fa6d098142bf'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('raffles', schema=None) as batch_op:
        batch_op.alter_column(
            'status',
            existing_type=sa.Enum('draft', 'active', 'won', 'completed', 'cancelled', 'contested', name='raffle_status'),
            type_=sa.Enum('draft', 'active', 'won', 'completed', 'cancelled', 'contested', 'rejected_prize', name='raffle_status'),
            existing_nullable=False,
        )


def downgrade():
    with op.batch_alter_table('raffles', schema=None) as batch_op:
        batch_op.alter_column(
            'status',
            existing_type=sa.Enum('draft', 'active', 'won', 'completed', 'cancelled', 'contested', 'rejected_prize', name='raffle_status'),
            type_=sa.Enum('draft', 'active', 'won', 'completed', 'cancelled', 'contested', name='raffle_status'),
            existing_nullable=False,
        )
