"""add won and contested to raffle status enum

Revision ID: b1c2d3e4f5a6
Revises: ae8430d7bfe3
Create Date: 2026-07-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b1c2d3e4f5a6'
down_revision = 'ae8430d7bfe3'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('raffles', schema=None) as batch_op:
        batch_op.alter_column(
            'status',
            existing_type=sa.Enum('draft', 'active', 'completed', 'cancelled', name='raffle_status'),
            type_=sa.Enum('draft', 'active', 'won', 'completed', 'cancelled', 'contested', name='raffle_status'),
            existing_nullable=False,
        )


def downgrade():
    with op.batch_alter_table('raffles', schema=None) as batch_op:
        batch_op.alter_column(
            'status',
            existing_type=sa.Enum('draft', 'active', 'won', 'completed', 'cancelled', 'contested', name='raffle_status'),
            type_=sa.Enum('draft', 'active', 'completed', 'cancelled', name='raffle_status'),
            existing_nullable=False,
        )
