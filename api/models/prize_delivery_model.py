from db import db
from datetime import datetime, timezone
from sqlalchemy import Enum as SqlEnum

from constants.delivery_status import PrizeDeliveryStatus


class PrizeDelivery(db.Model):
    __tablename__ = "prize_deliveries"

    id = db.Column(db.Integer, primary_key=True)

    raffle_id = db.Column(db.Integer, db.ForeignKey("raffles.id"), nullable=False)
    winner_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    creator_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    tracking_code = db.Column(db.String(100), nullable=True)

    status = db.Column(
        SqlEnum(
            PrizeDeliveryStatus,
            name="prize_delivery_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=PrizeDeliveryStatus.PENDING_ADDRESS,
    )

    pickup_name = db.Column(db.String(100), nullable=False)
    pickup_address = db.Column(db.String(255))
    pickup_country = db.Column(db.String(50))
    pickup_phone = db.Column(db.String(20))
    pickup_email = db.Column(db.String(100), nullable=False, unique=False)

    delivery_name = db.Column(db.String(100), nullable=False)
    delivery_address = db.Column(db.String(255))
    delivery_country = db.Column(db.String(50))
    delivery_phone = db.Column(db.String(20))
    delivery_email = db.Column(db.String(100), nullable=False, unique=False)

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

    raffle = db.relationship("Raffle", back_populates="prize_delivery")

    winner = db.relationship(
        "User", foreign_keys=[winner_user_id], back_populates="winner_deliveries"
    )

    creator = db.relationship(
        "User", foreign_keys=[creator_user_id], back_populates="creator_deliveries"
    )

    logs = db.relationship(
        "PrizeDeliveryLog",
        back_populates="delivery",
        cascade="all, delete-orphan",
        order_by="PrizeDeliveryLog.created_at",
        lazy=True,
    )
