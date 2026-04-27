from flask import current_app
from flask_wtf import Form
from wtforms.validators import DataRequired, Length
from wtforms import (
    HiddenField,
    MultipleFileField,
    StringField,
    SelectField,
    IntegerField,
    TextAreaField,
    ValidationError,
)
from wtforms.validators import Length, NumberRange
from utils.file_helpers import get_valid_images, validate_file_size
from constants.product_condition import ProductCondition


def file_size_limit(max_size_mb):
    max_bytes = max_size_mb * 1024 * 1024

    def _file_size_limit(_form, field):
        for file in field.data:
            if file:
                validate_file_size(file, max_bytes)

    return _file_size_limit


def max_file_count(limit):
    def _max_file_count(_form, field):
        files = get_valid_images(field.data)

        if len(files) > limit:
            raise ValidationError(f"You can upload at most {limit} files.")

    return _max_file_count


def minimum_images():
    def _minimum_images(_form, field):
        files = get_valid_images(field.data)
        if not files:
            raise ValidationError(
                f"You need to uplaod at least one image for the product"
            )

    return _minimum_images


class ProductForm(Form):
    active = HiddenField(default="0")

    name = StringField(
        "Product name",
        validators=[DataRequired(), Length(min=3, max=100)],
    )

    description = TextAreaField(
        "Description",
        validators=[DataRequired(), Length(min=8, max=255)],
    )

    estimated_value = IntegerField(
        "Estimated value",
        validators=[DataRequired(), NumberRange(min=1, max=100_000)],
        default=1,
    )

    quantity = IntegerField(
        "Quantity",
        validators=[DataRequired(), NumberRange(min=1, max=99)],
        default=1,
    )

    condition = SelectField(
        "Condition",
        choices=[
            (cond.name, cond.name.replace("_", " ").title())
            for cond in ProductCondition
        ],
        validators=[DataRequired()],
    )

    images = MultipleFileField(
        "Product image",
        render_kw={
            "multiple": True,
            "accept": "image/jpeg,image/png",
        },
        validators=[
            DataRequired(),
            minimum_images(),
            max_file_count(3),
            file_size_limit(5),  # e.g. 5 MB per file
        ],
    )
