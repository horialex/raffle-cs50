from flask_wtf import Form
from wtforms.validators import Length, Optional
from wtforms import (
    MultipleFileField,
    StringField,
    SelectField,
    DecimalField,
    IntegerField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length, NumberRange
from flask_wtf.file import FileAllowed, FileRequired
from constants.product_condition import ProductCondition


class ProductForm(Form):
    name = StringField(
        "Product name",
        validators=[Optional(), Length(min=3, max=100)],
    )

    description = TextAreaField(
        "Description",
        validators=[Optional(), Length(min=8, max=255)],
    )

    estimated_value = DecimalField(
        "Estimated value",
        validators=[Optional(), NumberRange(min=1)],
        places=2,
    )

    quantity = IntegerField(
        "Quantity",
        validators=[Optional(), NumberRange(min=1, max=999)],
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

    image = MultipleFileField(
        "Product image",
        render_kw={"multiple": True},
        validators=[
            Optional(),
            FileAllowed(["jpg", "jpeg", "png"], "Images only!"),
        ],
    )
