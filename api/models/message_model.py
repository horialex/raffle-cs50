from datetime import datetime, timezone
from sqlalchemy import Enum as SqlEnum
from constants.message_category import MessageCategory
from db import db


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    # Owner of the message: deleted with the user (see User.messages cascade).
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    # Context references: nulled when the referenced row is deleted, so the message
    # (which may belong to another user) survives with a dangling-free null reference.
    raffle_id = db.Column(
        db.Integer, db.ForeignKey("raffles.id", ondelete="SET NULL"), nullable=True
    )
    ticket_id = db.Column(
        db.Integer, db.ForeignKey("tickets.id", ondelete="SET NULL"), nullable=True
    )
    prize_delivery_id = db.Column(
        db.Integer,
        db.ForeignKey("prize_deliveries.id", ondelete="SET NULL"),
        nullable=True,
    )

    body = db.Column(db.String(400), nullable=False)
    # Sentiment of the message, set by the sender at creation (see MessageCategory).
    # Drives the row tint in the UI so it never has to be inferred from the message's
    # other fields. NULL renders neutral.
    category = db.Column(
        SqlEnum(
            MessageCategory,
            name="message_category",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=True,
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    is_read = db.Column(db.Boolean, nullable=False, default=False)

    # Relations
    raffle = db.relationship("Raffle")
    ticket = db.relationship("Ticket")
    prize_delivery = db.relationship("PrizeDelivery")
