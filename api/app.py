import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, render_template, request, flash, redirect, session
from flask_session import Session
from sqlalchemy import text
from flask_migrate import Migrate
from werkzeug.exceptions import RequestEntityTooLarge

from models.user_model import User
from models.raffle_model import Raffle
from db import db
from users import users_bp
from auth import auth_bp
from utils.helpers import login_required
from flask_wtf.csrf import CSRFProtect


# ----------------------------
# Config
# ----------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

MAX_FILE_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_MB", 3)) * 1024 * 1024

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
)

app.config["SECRET_KEY"] = os.getenv("APP_SECRET")
csrf = CSRFProtect(app)

# ----------------------------
# SQLAlchemy setup + Migrations
# ----------------------------
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}"
    f"@{os.getenv('MYSQL_HOST', '127.0.0.1')}:{os.getenv('MYSQL_PORT', 3306)}"
    f"/{os.getenv('MYSQL_DATABASE')}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)
migrate = Migrate(app, db)

# ----------------------------
# App secret, uploads, session
# ----------------------------

UPLOAD_FOLDER = os.path.join(app.static_folder, "uploads")
PROFILE_PICS_FOLDER = os.path.join(UPLOAD_FOLDER, "images")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["PROFILE_PICS_FOLDER"] = PROFILE_PICS_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_UPLOAD_SIZE

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROFILE_PICS_FOLDER, exist_ok=True)


# Flask-Session config
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

Session(app)

# ----------------------------
# Blueprints
# ----------------------------
app.register_blueprint(users_bp)
app.register_blueprint(auth_bp)  # Uncomment if auth blueprint exists


# ----------------------------
# Request / context hooks
# ----------------------------
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.context_processor
def inject_user():
    user_id = session.get("user_id")
    user = None
    if user_id:
        user = User.query.get(user_id)

    return {"current_user": user}


# ----------------------------
# Routes
# ----------------------------
@app.route("/", methods=["GET"])
@login_required
def home():
    return render_template("index.html")


@app.route("/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))
        return {"status": "database connected"}
    except Exception as e:
        return {"error": str(e)}, 500


# ----------------------------
# Error handlers
# ----------------------------
@app.errorhandler(404)
@app.errorhandler(405)
def page_not_found(e):
    return render_template("404.html")


@app.errorhandler(403)
def forbidden(e):
    return render_template("403.html")


@app.errorhandler(500)
def server_error(e):
    return render_template("500.html")


@app.errorhandler(RequestEntityTooLarge)
def handle_large_file(e):
    max_mb = MAX_FILE_UPLOAD_SIZE // (1024 * 1024)
    flash(f"File is too large. Maximum size is {max_mb}MB.", "error")
    return redirect(request.url)


# ----------------------------
# Run
# ----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
