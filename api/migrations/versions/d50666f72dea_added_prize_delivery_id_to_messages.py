"""added prize delivery id to messages

Revision ID: d50666f72dea
Revises: d5e6f7a8b9c0
Create Date: 2026-07-21 09:54:29.441879

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd50666f72dea'
down_revision = 'd5e6f7a8b9c0'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('messages', schema=None) as batch_op:
        batch_op.add_column(sa.Column('prize_delivery_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_messages_prize_delivery_id', 'prize_deliveries', ['prize_delivery_id'], ['id']
        )


def downgrade():
    with op.batch_alter_table('messages', schema=None) as batch_op:
        batch_op.drop_constraint('fk_messages_prize_delivery_id', type_='foreignkey')
        batch_op.drop_column('prize_delivery_id')
