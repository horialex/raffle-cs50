"""update prize delivery status enum

Renames pending_address -> pending_delivery_address and adds
pending_sender_address, delivery_timeout and prize_rejected to the
prize_delivery_status enum. The enum backs three columns:
prize_deliveries.status, prize_delivery_logs.from_status and
prize_delivery_logs.to_status.

The rename is done safely for existing rows by first widening the enum to
include both the old and new values, rewriting the data, then narrowing to
the final set.

Revision ID: d5e6f7a8b9c0
Revises: c3d4e5f6a7b8
Create Date: 2026-07-20 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "d5e6f7a8b9c0"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


OLD = sa.Enum(
    "pending_address",
    "waiting_for_shipment",
    "prize_sent",
    "prize_delivered",
    "prize_accepted",
    "contested",
    "delivery_failed",
    name="prize_delivery_status",
)

# Union of old + new values so existing rows stay valid while data is rewritten.
TRANSITIONAL = sa.Enum(
    "pending_address",
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

NEW = sa.Enum(
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


def _alter_all(from_type, to_type):
    with op.batch_alter_table("prize_deliveries", schema=None) as batch_op:
        batch_op.alter_column(
            "status",
            existing_type=from_type,
            type_=to_type,
            existing_nullable=False,
        )
    with op.batch_alter_table("prize_delivery_logs", schema=None) as batch_op:
        batch_op.alter_column(
            "from_status",
            existing_type=from_type,
            type_=to_type,
            existing_nullable=True,
        )
        batch_op.alter_column(
            "to_status",
            existing_type=from_type,
            type_=to_type,
            existing_nullable=False,
        )


def upgrade():
    # 1. Widen to the union so 'pending_address' rows remain valid.
    _alter_all(OLD, TRANSITIONAL)

    # 2. Rewrite the renamed value.
    op.execute(
        "UPDATE prize_deliveries SET status = 'pending_delivery_address' "
        "WHERE status = 'pending_address'"
    )
    op.execute(
        "UPDATE prize_delivery_logs SET from_status = 'pending_delivery_address' "
        "WHERE from_status = 'pending_address'"
    )
    op.execute(
        "UPDATE prize_delivery_logs SET to_status = 'pending_delivery_address' "
        "WHERE to_status = 'pending_address'"
    )

    # 3. Narrow to the final set.
    _alter_all(TRANSITIONAL, NEW)


def downgrade():
    # 1. Widen to the union so new-only values remain valid.
    _alter_all(NEW, TRANSITIONAL)

    # 2. Map values back to those the old enum can represent.
    for table, column in (
        ("prize_deliveries", "status"),
        ("prize_delivery_logs", "from_status"),
        ("prize_delivery_logs", "to_status"),
    ):
        op.execute(
            f"UPDATE {table} SET {column} = 'pending_address' "
            f"WHERE {column} IN ('pending_delivery_address', 'pending_sender_address')"
        )
        op.execute(
            f"UPDATE {table} SET {column} = 'delivery_failed' "
            f"WHERE {column} = 'delivery_timeout'"
        )
        op.execute(
            f"UPDATE {table} SET {column} = 'contested' "
            f"WHERE {column} = 'prize_rejected'"
        )

    # 3. Narrow back to the original set.
    _alter_all(TRANSITIONAL, OLD)
