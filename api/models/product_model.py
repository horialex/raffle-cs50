from constants.product_condition import ProductCondition
from db import db
from sqlalchemy import Enum as SqlEnum


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    raffle_id = db.Column(db.Integer, db.ForeignKey("raffles.id"), nullable=False)

    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))

    condition = db.Column(
        SqlEnum(ProductCondition), nullable=False, default=ProductCondition.NEW
    )
    estimated_value = db.Column(db.Numeric(10, 2), nullable=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    images = db.relationship(
        "ProductImage",
        cascade="all, delete-orphan",
        lazy=True,
    )
    # raffle = db.relationship("Raffle", back_populates="products")
