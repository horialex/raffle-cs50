from db import db


class PrizeContestationImage(db.Model):
    __tablename__ = "prize_contestation_images"

    id = db.Column(db.Integer, primary_key=True)

    prize_contestation_id = db.Column(
        db.Integer,
        db.ForeignKey("prize_contestations.id"),
        nullable=False,
    )

    image_url = db.Column(db.String(255), nullable=False)
