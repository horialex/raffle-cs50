from db import db
from datetime import datetime, timezone
from sqlalchemy import Enum as SqlEnum

from constants.delivery_status import PrizeDeliveryStatus


class PrizeDeliveryLogModel(db.Model):
    __tablename__ = "prize_delivery_logs"

    id = db.Column(db.Integer, primary_key=True)
    prize_delivery_id = db.Column(
        db.Integer, db.ForeignKey("prize_deliveries.id"), nullable=False
    )
