from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length


class PickupAddressForm(FlaskForm):
    pickup_name = StringField("Full Name", validators=[DataRequired(), Length(min=3)])
    pickup_address = StringField("Address", validators=[DataRequired(), Length(min=6)])
    pickup_country = SelectField("Country", choices=[], validators=[DataRequired()])
    pickup_phone = StringField("Phone", validators=[DataRequired(), Length(min=6)])

    submit = SubmitField("Confirm pickup address")
