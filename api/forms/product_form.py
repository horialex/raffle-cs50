from flask_wtf import FlaskForm
from wtforms.validators import InputRequired, Length
from wtforms import (
    FileField,
    StringField,
    SelectField,
    DecimalField,
    IntegerField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from flask_wtf.file import FileAllowed
from constants.product_condition import ProductCondition


class ProductForm(FlaskForm):
    name = StringField(
        "Product name",
        # validators=[DataRequired(), Length(min=2, max=100)],
    )

    description = TextAreaField(
        "Description",
        # validators=[Optional(), Length(max=255)],
    )

    estimated_value = DecimalField(
        "Estimated value",
        # validators=[Optional(), NumberRange(min=0)],
        # places=2,
    )

    quantity = IntegerField(
        "Quantity",
        # validators=[DataRequired(), NumberRange(min=1, max=999)],
        # default=1,
    )

    image = FileField(
        "Product image",
        # validators=[FileAllowed(["jpg", "jpeg", "png", "webp"], "Images only!")],
    )
