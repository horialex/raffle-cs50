from flask_wtf import FlaskForm
from wtforms import (
    FileField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    ValidationError,
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional
from flask_wtf.file import FileAllowed


class UserForm(FlaskForm):
    first_name = StringField("First Name", validators=[DataRequired(), Length(min=3)])
    last_name = StringField("Last Name", validators=[DataRequired(), Length(min=3)])
    username = StringField("Username", validators=[DataRequired(), Length(min=3)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    phone = StringField("Phone", validators=[DataRequired(), Length(min=6)])
    country = SelectField("Country", choices=[], validators=[DataRequired()])
    address = StringField("Address", validators=[DataRequired(), Length(min=6)])

    # Password is required for registration, optional for update
    password = PasswordField("Password", validators=[Optional(), Length(min=6)])
    confirm_password = PasswordField("Confirm Password")

    # Profile picture (optional for update)
    profile_picture = FileField(
        "Profile Picture",
        validators=[FileAllowed(["jpg", "jpeg", "png"], "Images only!")],
    )

    submit = SubmitField("Submit")

    def validate_confirm_password(self, field):
        if self.password.data:
            if not field.data:
                raise ValidationError("Confirm Password is required")
            if field.data != self.password.data:
                raise ValidationError("Passwords must match")


class UserSelfUpdateForm(UserForm):
    old_password = PasswordField("Old Password", validators=[Optional()])
