"""lowercase ticket status values

Revision ID: ae8430d7bfe3
Revises: 019663c6da81
Create Date: 2026-07-07 10:05:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ae8430d7bfe3'
down_revision = '019663c6da81'
branch_labels = None
depends_on = None

OLD_VALUES = ('PENDING', 'WINNER', 'LOST', 'CANCELLED')
NEW_VALUES = ('pending', 'winner', 'lost', 'cancelled')


def upgrade():
    # The column's collation (utf8mb4_0900_ai_ci) is case-insensitive, so MySQL
    # matches each row's old value to its new spelling by this ALTER alone -
    # no intermediate widened enum or UPDATE is needed (and a widened enum
    # containing both cases would itself be rejected as having duplicate values).
    with op.batch_alter_table('tickets', schema=None) as batch_op:
        batch_op.alter_column(
            'status',
            existing_type=sa.Enum(*OLD_VALUES, name='ticketstatus'),
            type_=sa.Enum(*NEW_VALUES, name='ticket_status'),
            existing_nullable=False,
        )


def downgrade():
    with op.batch_alter_table('tickets', schema=None) as batch_op:
        batch_op.alter_column(
            'status',
            existing_type=sa.Enum(*NEW_VALUES, name='ticket_status'),
            type_=sa.Enum(*OLD_VALUES, name='ticketstatus'),
            existing_nullable=False,
        )
