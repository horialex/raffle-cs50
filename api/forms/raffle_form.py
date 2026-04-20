from flask import current_app
from datetime import date, datetime, time, timezone
from flask_wtf import FlaskForm
from wtforms import (
    FieldList,
    FormField,
    StringField,
    IntegerField,
    SubmitField,
    SelectField,
    DateField,
    TextAreaField,
)
from wtforms.validators import (
    DataRequired,
    InputRequired,
    Length,
    NumberRange,
    ValidationError,
)
from forms.product_form import ProductForm


class CreateRaffleForm(FlaskForm):
    title = StringField(
        "Title",
        validators=[InputRequired(), Length(min=3, max=50)],
    )

    description = TextAreaField(
        "Description",
        validators=[InputRequired(), Length(min=8, max=100)],
    )

    ticket_price = IntegerField(
        "Ticket price",
        validators=[InputRequired(), NumberRange(min=1)],
    )

    minimum_required_tickets = IntegerField(
        "Minimum required tickets",
        validators=[InputRequired(), NumberRange(min=2)],
    )

    maximum_tickets_per_user = IntegerField(
        "Maximum tickets per user",
        validators=[InputRequired(), NumberRange(min=1)],
    )

    due_date_date = DateField(
        "Due date",
        validators=[InputRequired()],
        format="%Y-%m-%d",
    )

    due_date_hour = SelectField(
        "Due hour",
        validators=[InputRequired()],
        choices=[(str(hour), f"{hour:02d}:00") for hour in range(24)],
    )

    product_count = SelectField(
        "Number of products",
        choices=[("1", "1"), ("2", "2"), ("3", "3"), ("4", "4"), ("5", "5")],
        default="1",
        validators=[DataRequired()],
    )

    # be careful here
    products = FieldList(FormField(ProductForm), min_entries=5, max_entries=5)

    submit = SubmitField("Submit")

    def validate_due_date_date(self, field):
        if field.data and field.data < date.today():
            raise ValidationError("Due date cannot be in the past.")

    def validate_maximum_tickets_per_user(self, field):
        if (
            field.data is not None
            and self.minimum_required_tickets.data is not None
            and field.data > self.minimum_required_tickets.data
        ):
            raise ValidationError(
                "Maximum tickets per user cannot be greater than minimum required tickets."
            )

    def validate_due_date_hour(self, field):
        if not self.due_date_date.data or field.data in (None, ""):
            return

        selected_hour = int(field.data)

        due_datetime = datetime.combine(
            self.due_date_date.data,
            time(hour=selected_hour, minute=0),
        ).replace(tzinfo=timezone.utc)

        if due_datetime <= datetime.now(timezone.utc):
            raise ValidationError("Due date must be in the future.")

    def validate_products(self, field):
        min_count = current_app.config["MIN_PRODUCTS_PER_RAFFLE"]
        max_count = current_app.config["MAX_PRODUCTS_PER_RAFFLE"]

        count = len(field.entries)

        if count < min_count:
            raise ValidationError(f"At least {min_count} product is required.")

        if count > max_count:
            raise ValidationError(f"You can add at most {max_count} products.")
