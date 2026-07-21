from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length


class DeliveryAddressForm(FlaskForm):
    delivery_name = StringField("Full Name", validators=[DataRequired(), Length(min=6)])
    delivery_address = StringField(
        "Address", validators=[DataRequired(), Length(min=6)]
    )
    delivery_country = SelectField("Country", choices=[], validators=[DataRequired()])
    delivery_phone = StringField("Phone", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("Confirm address")
