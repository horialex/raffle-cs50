from sqlalchemy import Enum, func

from db import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    country = db.Column(db.String(50))
    address = db.Column(db.String(255))
    profile_picture = db.Column(db.String(255))
    role = db.Column(
        Enum("admin", "user", name="user_roles"), nullable=False, default="user"
    )
    created_at = db.Column(
        db.DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    # last_login_at = db.Column(db.DateTime(timezone=True), nullable=True) # add this with a migration

    @property
    def is_admin(self):
        return self.role == "admin"
