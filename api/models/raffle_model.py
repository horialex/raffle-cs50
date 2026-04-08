from datetime import datetime, timezone
from sqlalchemy import Enum

from db import db


class Raffle(db.Model):
    __tablename__ = "raffles"

    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )  # fk to users.id
    title = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(100), nullable=False)
    status = db.Column(
        Enum("draft", "active", "completed", "cancelled", name="raffle_status"),
        nullable=False,
        default="draft",
    )
    ticket_price = db.Column(db.Integer, nullable=False)
    minimum_required_tickets = db.Column(db.Integer, nullable=False, default=5)  # TBD
    maximum_tickets_per_user = db.Column(db.Integer, nullable=False, default=1)
    due_date = db.Column(db.DateTime(timezone=True), nullable=False)
    # winner_ticket_id = db.Column(db.Integer, db.ForeignKey("ticket.id"), nullable=True) fk to tickets.id
    # winner_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True) # fk to users.id #  TBD
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self):
        return f'<Raffle title: "{self.title}">'

    @property
    def is_active(self):
        return self.status == "active"

    @property
    def is_completed(self):
        return self.status == "completed"

    @property
    def is_cancelled(self):
        return self.status == "cancelled"
