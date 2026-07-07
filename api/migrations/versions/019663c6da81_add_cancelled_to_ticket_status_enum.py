"""add cancelled to ticket status enum

Revision ID: 019663c6da81
Revises: 53a782c55ab4
Create Date: 2026-07-07 09:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '019663c6da81'
down_revision = '53a782c55ab4'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('tickets', schema=None) as batch_op:
        batch_op.alter_column(
            'status',
            existing_type=sa.Enum('PENDING', 'WINNER', 'LOST', name='ticketstatus'),
            type_=sa.Enum('PENDING', 'WINNER', 'LOST', 'CANCELLED', name='ticketstatus'),
            existing_nullable=False,
        )


def downgrade():
    with op.batch_alter_table('tickets', schema=None) as batch_op:
        batch_op.alter_column(
            'status',
            existing_type=sa.Enum('PENDING', 'WINNER', 'LOST', 'CANCELLED', name='ticketstatus'),
            type_=sa.Enum('PENDING', 'WINNER', 'LOST', name='ticketstatus'),
            existing_nullable=False,
        )
