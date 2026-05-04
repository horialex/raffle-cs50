from flask_wtf import FlaskForm
from wtforms import BooleanField, HiddenField


class ProductImageForm(FlaskForm):
    id = HiddenField()
    delete = BooleanField("Delete")
