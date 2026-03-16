import uuid
import hashlib
import os
from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    current_app,
)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from datetime import datetime, timezone
from db import db
from models.user_model import User
from helpers.helpers import (
    allowed_file,
    is_valid_email,
    is_valid_phone_number,
    login_required,
)

USER_ROLE = "user"
ADMIN_ROLE = "admin"

users_bp = Blueprint("users_bp", __name__)


# ----------------------------
# Test route
# ----------------------------
@users_bp.route("/count-users")
def test():
    users = User.query.all()
    return {"count": len(users)}


# ----------------------------
# Registration
# ----------------------------
@users_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form.get("firstName", "").strip()
        last_name = request.form.get("lastName", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        country = request.form.get("country", "").strip()
        address = request.form.get("address", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirmation", "")
        profile_picture = request.files.get("profilePicture")

        # ----------------------------
        # Validation
        # ----------------------------
        if len(first_name) < 3:
            flash("First name must be at least 3 characters", "error")
            return render_template("register.html")
        if len(last_name) < 3:
            flash("Last name must be at least 3 characters", "error")
            return render_template("register.html")
        if len(username) < 3:
            flash("Username must be at least 3 characters", "error")
            return render_template("register.html")
        if len(password) < 6:
            flash("Password must be at least 6 characters", "error")
            return render_template("register.html")
        if password != confirm_password:
            flash("Passwords do not match", "error")
            return render_template("register.html")
        if not country:
            flash("Must provide country", "error")
            return render_template("register.html")
        if not email or not is_valid_email(email)[0]:
            flash("Invalid email", "error")
            return render_template("register.html")
        if not phone or not is_valid_phone_number(phone)[0]:
            flash("Invalid phone number", "error")
            return render_template("register.html")
        if len(address) < 6:
            flash("Address must be at least 6 characters", "error")
            return render_template("register.html")
        if not profile_picture or profile_picture.filename == "":
            flash("Must provide profile picture", "error")
            return render_template("register.html")

        # ----------------------------
        # Save profile picture
        # ----------------------------
        pic_filename = secure_filename(profile_picture.filename)
        if not allowed_file(pic_filename):
            flash("Allowed profile pic formats: png, jpg, jpeg", "error")
            return render_template("register.html")

        pic_name = f"{uuid.uuid1()}_{pic_filename}"
        save_path = os.path.join(current_app.config["PROFILE_PICS_FOLDER"], pic_name)
        profile_picture.save(save_path)

        # ----------------------------
        # Hash password
        # ----------------------------
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        # hashed_password = generate_password_hash(password)

        # ----------------------------
        # Create user
        # ----------------------------
        user = User(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            password=hashed_password,
            phone=phone,
            country=country,
            address=address,
            profile_picture=pic_name,
            last_login_at=datetime.now(timezone.utc),
        )

        try:
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            if "Duplicate entry" in str(e):
                flash("Username or email already exists", "error")
                return render_template("register.html")
            else:
                flash(f"Error creating user: {str(e)}", "error")
                return render_template("register.html")

        # ----------------------------
        # Log user in
        # ----------------------------
        session["user_id"] = user.id
        session["username"] = user.username
        session["first_name"] = user.first_name

        flash("Registration successful! You are now logged in.", "success")
        return redirect("/")

    return render_template("register.html")


# ----------------------------
# Get users list
# ----------------------------
@users_bp.route("/users", methods=["GET"])
@login_required
def get_users():
    user = User.query.get(session["user_id"])
    if not user.is_admin:
        abort(403)

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 100)

    pagination = (
        User.query.filter(User.role != "admin")
        .order_by(User.id)
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    users: User = [
        {
            "id": u.id,
            "firstName": u.first_name,
            "lastName": u.last_name,
            "username": u.username,
            "email": u.email,
            "phone": u.phone,
            "country": u.country,
            "address": u.address,
            "profilePicture": u.profile_picture,
            "createdAt": u.created_at,
            "lastLogin": u.last_login_at,
        }
        for u in pagination.items
    ]

    return render_template(
        "users.html",
        users=users,
        total=pagination.total,
        page=page,
        per_page=per_page,
    )


# ----------------------------
# Edit user
# ----------------------------
@users_bp.route("/update/<int:id>", methods=["GET", "POST"])
def update(id):
    user: User = User.query.get_or_404(id)  # fetch user or 404 if not found
    if request.method == "POST":
        # handle form submission here
        ...
    return render_template("update-user.html", user=user)
