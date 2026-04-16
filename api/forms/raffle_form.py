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
from wtforms.validators import InputRequired, Length, NumberRange, ValidationError

from forms.prize_form import PrizeForm


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

    prizes = FieldList(FormField(PrizeForm), min_entries=1)

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
