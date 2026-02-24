import requests

from flask import redirect, render_template, session
from functools import wraps
from email_validator import validate_email, EmailNotValidError
import phonenumbers
from phonenumbers import carrier
from phonenumbers.phonenumberutil import (
    number_type,
    NumberParseException,
    PhoneNumberType,
)

ALLOWED_PROFILE_PIC_EXTENSIONS = {"png", "jpg", "jpeg"}


def allowed_file(filename: str) -> bool:
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_PROFILE_PIC_EXTENSIONS
    )


def is_valid_phone_number(phone: str, country_code: str = "RO") -> tuple[bool, str]:
    if not phone:
        return False, "Must provide a phone number"

    try:
        # Always parse as Romanian
        parsed_number = phonenumbers.parse(phone, country_code)
    except NumberParseException:
        return False, "Invalid phone number format"

    # Must be a Romanian number
    if phonenumbers.region_code_for_number(parsed_number) != "RO":
        return False, "Phone number must be Romanian"

    if not phonenumbers.is_valid_number(parsed_number):
        return False, "Phone number is not valid"

    # Optional: enforce mobile only
    if number_type(parsed_number) not in (
        PhoneNumberType.MOBILE,
        PhoneNumberType.FIXED_LINE_OR_MOBILE,
    ):
        return False, "Phone number must be a mobile number"

    return True, ""


def is_valid_email(email: str) -> tuple[bool, str]:
    """
    Validates an email string.

    Returns a tuple:
    - bool: True if valid, False if invalid
    - str: error message if invalid, empty string if valid
    """
    if not email:
        return False, "Must provide a valid email"

    try:
        valid = validate_email(email)
        return True, ""
    except EmailNotValidError as e:
        return False, str(e)


def apology(message, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


def lookup(symbol):
    """Look up quote for symbol."""
    url = f"https://finance.cs50.io/quote?symbol={symbol.upper()}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for HTTP error responses
        quote_data = response.json()
        return {
            "name": quote_data["companyName"],
            "price": quote_data["latestPrice"],
            "symbol": symbol.upper(),
        }
    except requests.RequestException as e:
        print(f"Request error: {e}")
    except (KeyError, ValueError) as e:
        print(f"Data parsing error: {e}")
    return None


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"
