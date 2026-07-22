from db import db
from datetime import datetime, timezone
from sqlalchemy import Enum as SqlEnum

from constants.delivery_status import PrizeDeliveryStatus


class PrizeDeliveryLog(db.Model):
    __tablename__ = "prize_delivery_logs"

    id = db.Column(db.Integer, primary_key=True)
    prize_delivery_id = db.Column(
        db.Integer, db.ForeignKey("prize_deliveries.id"), nullable=False
    )

    # Null actor means the transition was made by the system (e.g. the timeout job)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    from_status = db.Column(
        SqlEnum(
            PrizeDeliveryStatus,
            name="prize_delivery_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=True,
    )
    to_status = db.Column(
        SqlEnum(
            PrizeDeliveryStatus,
            name="prize_delivery_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )

    note = db.Column(db.String(255), nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    delivery = db.relationship("PrizeDelivery", back_populates="logs")
    actor = db.relationship("User", foreign_keys=[actor_user_id])
