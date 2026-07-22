"""rename pending_sender_address to pending_pickup_address

Renames the prize_delivery_status enum value pending_sender_address ->
pending_pickup_address across the three columns that use it
(prize_deliveries.status, prize_delivery_logs.from_status, .to_status).

Safe for existing rows: widen the enum to include both the old and new values,
rewrite the data, then narrow to the final set.

Revision ID: f1a2b3c4d5e6
Revises: e1f2a3b4c5d6
Create Date: 2026-07-22 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f1a2b3c4d5e6"
down_revision = "e1f2a3b4c5d6"
branch_labels = None
depends_on = None


OLD = sa.Enum(
    "pending_delivery_address",
    "pending_sender_address",
    "waiting_for_shipment",
    "prize_sent",
    "prize_delivered",
    "prize_accepted",
    "contested",
    "delivery_failed",
    "delivery_timeout",
    "prize_rejected",
    name="prize_delivery_status",
)

# Union of old + new so existing rows stay valid while data is rewritten.
TRANSITIONAL = sa.Enum(
    "pending_delivery_address",
    "pending_sender_address",
    "pending_pickup_address",
    "waiting_for_shipment",
    "prize_sent",
    "prize_delivered",
    "prize_accepted",
    "contested",
    "delivery_failed",
    "delivery_timeout",
    "prize_rejected",
    name="prize_delivery_status",
)

NEW = sa.Enum(
    "pending_delivery_address",
    "pending_pickup_address",
    "waiting_for_shipment",
    "prize_sent",
    "prize_delivered",
    "prize_accepted",
    "contested",
    "delivery_failed",
    "delivery_timeout",
    "prize_rejected",
    name="prize_delivery_status",
)

COLUMNS = (
    ("prize_deliveries", "status", False),
    ("prize_delivery_logs", "from_status", True),
    ("prize_delivery_logs", "to_status", False),
)


def _alter_all(from_type, to_type):
    for table, column, nullable in COLUMNS:
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.alter_column(
                column,
                existing_type=from_type,
                type_=to_type,
                existing_nullable=nullable,
            )


def upgrade():
    # 1. Widen to the union so 'pending_sender_address' rows remain valid.
    _alter_all(OLD, TRANSITIONAL)

    # 2. Rewrite the renamed value.
    for table, column, _ in COLUMNS:
        op.execute(
            f"UPDATE {table} SET {column} = 'pending_pickup_address' "
            f"WHERE {column} = 'pending_sender_address'"
        )

    # 3. Narrow to the final set.
    _alter_all(TRANSITIONAL, NEW)


def downgrade():
    # 1. Widen to the union so 'pending_pickup_address' rows remain valid.
    _alter_all(NEW, TRANSITIONAL)

    # 2. Rewrite back to the old value.
    for table, column, _ in COLUMNS:
        op.execute(
            f"UPDATE {table} SET {column} = 'pending_sender_address' "
            f"WHERE {column} = 'pending_pickup_address'"
        )

    # 3. Narrow to the original set.
    _alter_all(TRANSITIONAL, OLD)
