"""create users table

The users table was created before migrations were introduced, so the first
migration (28e1a32d43ca) assumed it already existed. This base migration lets a
fresh database be built from scratch. Databases that already have the table are
past this revision and never run it.

Revision ID: 7c1e9a4b2d30
Revises:
Create Date: 2026-11-07 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7c1e9a4b2d30"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("first_name", sa.String(length=50), nullable=False),
        sa.Column("last_name", sa.String(length=50), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=100), nullable=False),
        sa.Column("password", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("country", sa.String(length=50), nullable=True),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("profile_picture", sa.String(length=255), nullable=True),
        sa.Column(
            "role",
            sa.Enum("admin", "user", name="user_roles"),
            server_default="user",
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username", name="username"),
        sa.UniqueConstraint("email", name="email"),
    )


def downgrade():
    op.drop_table("users")
