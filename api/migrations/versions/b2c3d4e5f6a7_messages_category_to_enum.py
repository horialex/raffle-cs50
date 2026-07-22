"""convert messages.category to a native enum

The category column was added as VARCHAR; convert it to a native ENUM matching the
MessageCategory enum ("win" | "loss" | "info") for consistency with the other
status columns. Existing values are already valid members, so the conversion is safe.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-22 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


ENUM = sa.Enum("win", "loss", "info", name="message_category")
VARCHAR = sa.String(length=20)


def upgrade():
    with op.batch_alter_table("messages", schema=None) as batch_op:
        batch_op.alter_column(
            "category",
            existing_type=VARCHAR,
            type_=ENUM,
            existing_nullable=True,
        )


def downgrade():
    with op.batch_alter_table("messages", schema=None) as batch_op:
        batch_op.alter_column(
            "category",
            existing_type=ENUM,
            type_=VARCHAR,
            existing_nullable=True,
        )
