import hashlib
import os
import uuid

from flask import (
    Blueprint,
    app,
    flash,
    redirect,
    render_template,
    request,
    session,
    current_app,
)
import mysql
from helpers.helpers import (
    allowed_file,
    is_valid_email,
    is_valid_phone_number,
    login_required,
)
from db import get_db_connection
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

USER_ROLE = "user"
ADMIN_ROLE = "admin"

users_bp = Blueprint("users", __name__)


@users_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form.get("firstName")
        last_name = request.form.get("lastName")
        country = request.form.get("country")
        email = request.form.get("email")
        phone = request.form.get("phone")
        address = request.form.get("address")
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirmation")
        profile_picture = request.files.get("profilePicture")

        # Fields validation
        if not first_name:
            flash("Must provide first name", "error")
            return render_template("register.html")

        if len(first_name.strip()) < 3:
            flash("First name must be at least 3 characters long", "error")
            return render_template("register.html")

        if not last_name:
            flash("Must provide last name", "error")
            return render_template("register.html")

        if len(last_name.strip()) < 3:
            flash("Last name must be at least 3 characters long", "error")
            return render_template("register.html")

        print("USERNAME: ", username)
        if not username:
            flash("Must provide username", "error")
            return render_template("register.html")

        if len(username.strip()) < 3:
            flash("username must be at least 3 characters long", "error")
            return render_template("register.html")

        if not password:
            flash("Must provide password", "error")
            return render_template("register.html")

        if len(password.strip()) < 6:
            flash("password must be at least 6 characters", "error")
            return render_template("register.html")

        if password != confirm_password:
            flash("confirm password must match the password", "error")
            return render_template("register.html")

        if not country:
            flash("Must provide country", "error")
            return render_template("register.html")

        if not email:
            flash("Must provide email", "error")
            return render_template("register.html")

        if not address:
            flash("Must provide address", "error")
            return render_template("register.html")

        if len(address.strip()) < 6:
            flash("Address must be at least 6 characters", "error")
            return render_template("register.html")

        valid_email, message = is_valid_email(email)
        if not valid_email:
            flash(message, "error")
            return render_template("register.html")

        if not phone:
            flash("Must provide phone number", "error")
            return render_template("register.html")

        valid_phone, message = is_valid_phone_number(phone)
        if not valid_phone:
            flash(message, "error")
            return render_template("register.html")

        if not profile_picture or profile_picture.filename == "":
            flash("Must provide profile picture", "error")
            return render_template("register.html")

        pic_filename = secure_filename(profile_picture.filename)

        if not allowed_file(pic_filename):
            flash(
                "We only allow the following formats for profile pic: png, jpg, jpeg",
                "error",
            )
            return render_template("register.html")
        pic_name = str(uuid.uuid1()) + "_" + pic_filename
        save_path = os.path.join(current_app.config["PROFILE_PICS_FOLDER"], pic_name)
        profile_picture.save(save_path)

        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(
                """
                INSERT INTO users (first_name, last_name, username, email, password, phone, country, address, role, profile_picture, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()) 
                """,
                (
                    first_name,
                    last_name,
                    username,
                    email,
                    hashed_password,
                    phone,
                    country,
                    address,
                    USER_ROLE,
                    pic_name,
                ),
            )
            conn.commit()

            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            row = cursor.fetchone()

            if not row:
                flash("Unable to login, user was not properly created.", "error")
                return render_template("register.html")

            # Log user in
            session["user_id"] = row["id"]
            session["username"] = row["username"]

        except mysql.connector.IntegrityError as err:
            if err.errno == 1062:  # Duplicate entry
                flash("Username or email already exists. Please use another.", "error")
                return render_template("register.html")
            else:
                raise
        finally:
            cursor.close()
            conn.close()

        flash("Registration successful! You are now logged in.", "success")
        return redirect("/users")

    return render_template("register.html")


@users_bp.route("/users", methods=["GET"])
@login_required
def get_users():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    # Safety validation
    if page < 1:
        return {"error": "page must be >= 1"}, 400

    per_page = min(per_page, 100)
    offset = (page - 1) * per_page

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT COUNT(*) AS total FROM users WHERE role !=%s", (ADMIN_ROLE,)
        )
        total = cursor.fetchone()["total"]

        cursor.execute(
            "SELECT id, first_name, last_name, username, email, phone, country, address, profile_picture FROM users WHERE role  != %s ORDER BY id LIMIT %s OFFSET %s",
            (ADMIN_ROLE, per_page, offset),
        )

        rows = cursor.fetchall()

        users = [
            {
                "id": row["id"],
                "firstName": row["first_name"],
                "lastName": row["last_name"],
                "username": row["username"],
                "email": row["email"],
                "phone": row["phone"],
                "country": row["country"],
                "address": row["address"],
                "profilePicture": row["profile_picture"],
            }
            for row in rows
        ]
        return render_template("users.html", users=users)
    finally:
        cursor.close()
        conn.close()
