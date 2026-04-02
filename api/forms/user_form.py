from flask_wtf import FlaskForm
from wtforms import FileField, PasswordField, SelectField, StringField, SubmitField
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
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[Optional(), EqualTo("password", message="Passwords must match")],
    )

    # Profile picture (optional for update)
    profile_picture = FileField(
        "Profile Picture",
        validators=[FileAllowed(["jpg", "jpeg", "png"], "Images only!")],
    )

    submit = SubmitField("Submit")


class UserSelfUpdateForm(UserForm):
    old_password = PasswordField("Old Password", validators=[DataRequired()])
