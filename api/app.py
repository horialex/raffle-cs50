from flask import (
    Flask,
    redirect,
    request,
    render_template,
    session,
    flash,
)

from db import get_db_connection
import os
from dotenv import load_dotenv
from pathlib import Path
from flask_session import Session
from helpers.helpers import (
    usd,
)

from werkzeug.exceptions import RequestEntityTooLarge
import uuid as uuid

from auth import auth_bp
from users import users_bp

MAX_FILE_UPLOAD_SIZE = 3 * 1024 * 1024  # 3MB

BASE_DIR = Path(__file__).resolve().parent.parent
env_path = Path(__file__).resolve().parent.parent / ".env"


load_dotenv(dotenv_path=env_path)


app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
)

app.secret_key = os.getenv("APP_SECRET")
UPLOAD_FOLDER = "static/uploads/"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_UPLOAD_SIZE


PROFILE_PICS_FOLDER = os.path.join(app.static_folder, "uploads", "images")
app.config["PROFILE_PICS_FOLDER"] = PROFILE_PICS_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROFILE_PICS_FOLDER, exist_ok=True)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


app.register_blueprint(auth_bp)
app.register_blueprint(users_bp)


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.context_processor
def inject_user():
    return {"username": session.get("username")}


@app.route("/")
def home():
    return {"message": "Flask + MySQL running"}


@app.route("/health")
def health():
    try:
        conn = get_db_connection()
        conn.close()
        return {"status": "database connected"}
    except Exception as e:
        return {"error": str(e)}, 500


@app.errorhandler(404)
@app.errorhandler(405)
def page_not_found(e):
    return render_template("404.html")


@app.errorhandler(500)
def server_error(e):
    return render_template("500.html")


@app.errorhandler(RequestEntityTooLarge)
def handle_large_file(e):
    max_mb = MAX_FILE_UPLOAD_SIZE // (1024 * 1024)
    flash(f"File is too large. Maximum size is {max_mb}MB.", "error")
    return redirect(request.url)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
