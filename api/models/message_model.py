from datetime import datetime, timezone
from db import db


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    raffle_id = db.Column(db.Integer, db.ForeignKey("raffles.id"), nullable=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), nullable=True)
    body = db.Column(db.String(400), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    is_read = db.Column(db.Boolean, nullable=False, default=False)

    # Relations
    raffle = db.relationship("Raffle")
    ticket = db.relationship("Ticket")
