from datetime import datetime, timezone

from constants.ticket_status import TicketStatus
from db import db
from sqlalchemy import Enum as SqlEnum


class Ticket(db.Model):
    __tablename__ = "tickets"

    id = db.Column(db.Integer, primary_key=True)
    raffle_id = db.Column(db.Integer, db.ForeignKey("raffles.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    status = db.Column(
        SqlEnum(TicketStatus), nullable=False, default=TicketStatus.PENDING
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    price = db.Column(db.Integer, nullable=False, default=1)
