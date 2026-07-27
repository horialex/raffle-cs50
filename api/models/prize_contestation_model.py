from db import db
from datetime import datetime, timezone
from sqlalchemy import Enum as SqlEnum

from constants.contestation_status import ContestationStatus
from constants.contestation_reason import ContestationReason


class PrizeContestation(db.Model):
    __tablename__ = "prize_contestations"

    id = db.Column(db.Integer, primary_key=True)
    prize_delivery_id = db.Column(
        db.Integer, db.ForeignKey("prize_deliveries.id"), nullable=False
    )

    reason = db.Column(
        SqlEnum(
            ContestationReason,
            name="contestation_reason",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    description = db.Column(db.Text, nullable=False)

    status = db.Column(
        SqlEnum(
            ContestationStatus,
            name="contestation_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=ContestationStatus.PENDING,
    )

    # Resolution — populated once an admin reviews the contestation
    resolved_by_user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )
    resolved_at = db.Column(db.DateTime(timezone=True), nullable=True)
    resolution_note = db.Column(db.String(255), nullable=True)

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

    prize_delivery = db.relationship(
        "PrizeDelivery",
        backref=db.backref(
            "contestation",
            uselist=False,
            cascade="all, delete-orphan",
        ),
    )

    resolved_by = db.relationship("User", foreign_keys=[resolved_by_user_id])

    images = db.relationship(
        "PrizeContestationImage",
        backref="prize_contestation",
        cascade="all, delete-orphan",
        lazy=True,
    )
