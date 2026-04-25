from flask_wtf import Form
from wtforms.validators import Length, Optional
from wtforms import (
    HiddenField,
    MultipleFileField,
    StringField,
    SelectField,
    IntegerField,
    TextAreaField,
)
from wtforms.validators import Length, NumberRange
from constants.product_condition import ProductCondition


class ProductForm(Form):
    active = HiddenField(default="0")

    name = StringField(
        "Product name",
        validators=[Optional(), Length(min=3, max=100)],
    )

    description = TextAreaField(
        "Description",
        validators=[Optional(), Length(min=8, max=255)],
    )

    estimated_value = IntegerField(
        "Estimated value",
        validators=[Optional(), NumberRange(min=1, max=100_000)],
        default=1,
    )

    quantity = IntegerField(
        "Quantity",
        validators=[Optional(), NumberRange(min=1, max=99)],
        default=1,
    )

    condition = SelectField(
        "Condition",
        choices=[
            (cond.name, cond.name.replace("_", " ").title())
            for cond in ProductCondition
        ],
        validators=[Optional()],
    )

    images = MultipleFileField(
        "Product image",
        render_kw={
            "multiple": True,
            "accept": "image/jpeg,image/png",
        },
        validators=[Optional()],
    )
