from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    TextAreaField,
)
from wtforms.validators import InputRequired, Length


class PrizeForm(FlaskForm):
    product_name = StringField(
        "Product name",
        # validators=[InputRequired(), Length(min=2, max=100)],
    )

    product_description = TextAreaField(
        "Product description",
        # validators=[InputRequired(), Length(min=8, max=500)],
    )
