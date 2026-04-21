from flask_wtf import Form
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


class ProductForm(Form):
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

    condition = SelectField(
        "Condition",
        choices=[
            (cond.name, cond.name.replace("_", " ").title())
            for cond in ProductCondition
        ],
        validators=[DataRequired()],
    )

    image = FileField(
        "Product image",
        # validators=[FileAllowed(["jpg", "jpeg", "png", "webp"], "Images only!")],
    )
