from datetime import datetime, timezone
from sqlalchemy import Enum as SqlEnum

from constants.raffle_status import RaffleStatus
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
        SqlEnum(
            RaffleStatus,
            name="raffle_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=RaffleStatus.DRAFT,
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
        return (
            f'<Raffle id={self.id} title="{self.title}" status="{self.status.value}">'
        )

    @property
    def is_draft(self):
        return self.status == RaffleStatus.DRAFT

    @property
    def is_active(self):
        return self.status == RaffleStatus.ACTIVE

    @property
    def is_completed(self):
        return self.status == RaffleStatus.COMPLETED

    @property
    def is_cancelled(self):
        return self.status == RaffleStatus.CANCELLED
