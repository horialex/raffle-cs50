"""add return statuses to prize delivery status enum

Adds prize_return_sent and prize_returned to the prize_delivery_status enum,
so the courier return leg (winner ships the prize back to the raffle
creator after an accepted contestation) can be tracked through its own
transitions instead of stopping at prize_rejected. The enum backs three
columns: prize_deliveries.status, prize_delivery_logs.from_status and
prize_delivery_logs.to_status.

Revision ID: 55228977aba2
Revises: 69ff605045d5
Create Date: 2026-09-04 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "55228977aba2"
down_revision = "69ff605045d5"
branch_labels = None
depends_on = None


OLD = sa.Enum(
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
    "prize_return_sent",
    "prize_returned",
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
    _alter_all(OLD, NEW)


def downgrade():
    _alter_all(NEW, OLD)
