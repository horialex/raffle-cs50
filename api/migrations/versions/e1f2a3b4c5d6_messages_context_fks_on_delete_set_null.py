"""messages context FKs on delete set null

Makes messages.raffle_id / ticket_id / prize_delivery_id use ON DELETE SET NULL so
that deleting a raffle/ticket/prize_delivery (e.g. via the User cascade on account
deletion) nulls the reference instead of failing the FK constraint. The message,
which may belong to a different user, survives. messages.user_id is intentionally
left unchanged (RESTRICT) - the owner's messages are removed via the ORM
User.messages cascade.

Revision ID: e1f2a3b4c5d6
Revises: d50666f72dea
Create Date: 2026-07-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e1f2a3b4c5d6'
down_revision = 'd50666f72dea'
branch_labels = None
depends_on = None


# (column, referenced table, name to (re)create the FK with)
SPECS = [
    ('raffle_id', 'raffles', 'fk_messages_raffle_id'),
    ('ticket_id', 'tickets', 'fk_messages_ticket_id'),
    ('prize_delivery_id', 'prize_deliveries', 'fk_messages_prize_delivery_id'),
]


def _current_fk_name(conn, column):
    row = conn.execute(
        sa.text(
            "SELECT CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'messages' "
            "AND COLUMN_NAME = :col AND REFERENCED_TABLE_NAME IS NOT NULL"
        ),
        {"col": column},
    ).fetchone()
    return row[0] if row else None


def upgrade():
    conn = op.get_bind()
    for column, ref_table, name in SPECS:
        existing = _current_fk_name(conn, column)
        if existing:
            op.drop_constraint(existing, 'messages', type_='foreignkey')
        op.create_foreign_key(
            name, 'messages', ref_table, [column], ['id'], ondelete='SET NULL'
        )


def downgrade():
    conn = op.get_bind()
    for column, ref_table, name in SPECS:
        existing = _current_fk_name(conn, column)
        if existing:
            op.drop_constraint(existing, 'messages', type_='foreignkey')
        # Recreate without ON DELETE SET NULL (restores default RESTRICT behavior).
        op.create_foreign_key(name, 'messages', ref_table, [column], ['id'])
