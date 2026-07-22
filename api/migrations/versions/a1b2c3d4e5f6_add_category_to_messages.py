"""add category to messages

Adds a nullable messages.category column ("win" | "loss" | "info"). The sender sets
it when the message is created; the UI uses it to tint the row instead of inferring
sentiment from the message's other fields. Existing rows stay NULL (neutral).

Revision ID: a1b2c3d4e5f6
Revises: f1a2b3c4d5e6
Create Date: 2026-07-22 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("messages", schema=None) as batch_op:
        batch_op.add_column(sa.Column("category", sa.String(length=20), nullable=True))


def downgrade():
    with op.batch_alter_table("messages", schema=None) as batch_op:
        batch_op.drop_column("category")
