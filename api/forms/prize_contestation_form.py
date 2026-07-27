from flask import current_app
from flask_wtf import FlaskForm
from wtforms import (
    MultipleFileField,
    SelectField,
    SubmitField,
    TextAreaField,
    ValidationError,
)
from wtforms.validators import DataRequired, Length

from utils.file_helpers import get_valid_images
from forms.product_form import file_size_limit
from constants.contestation_reason import ContestationReason


class PrizeContestationForm(FlaskForm):
    reason = SelectField(
        "Reason",
        choices=[
            (reason.name, reason.name.replace("_", " ").title())
            for reason in ContestationReason
        ],
        validators=[DataRequired()],
    )

    description = TextAreaField(
        "Description",
        validators=[DataRequired(), Length(min=8, max=1000)],
    )

    images = MultipleFileField(
        "Evidence images",
        render_kw={
            "multiple": True,
            "accept": "image/jpeg,image/png",
        },
        validators=[
            DataRequired(),
            file_size_limit(5),  # 5 MB per file
        ],
    )

    submit = SubmitField("Submit contestation")

    def validate_images(self, field):
        min_count = current_app.config["MIN_CONTESTATION_IMAGES"]
        max_count = current_app.config["MAX_CONTESTATION_IMAGES"]

        files = get_valid_images(field.data)

        if len(files) < min_count:
            raise ValidationError(f"You must upload at least {min_count} images.")

        if len(files) > max_count:
            raise ValidationError(f"You can upload at most {max_count} images.")
