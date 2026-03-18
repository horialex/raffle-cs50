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
from constants.countries import COUNTRIES
from forms.user_form import UserForm
from db import db
from models.user_model import User
from utils.helpers import (
    allowed_file,
    is_valid_email,
    is_valid_phone_number,
    login_required,
)
from utils.files import delete_profile_picture

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
    form = UserForm()
    form.country.choices = COUNTRIES
    form.submit.label.text = "Create user"
    upload_folder = current_app.config["PROFILE_PICS_FOLDER"]

    if form.validate_on_submit():
        hashed_password = hashlib.sha256(form.password.data.encode()).hexdigest()

        # Handle form data
        pic_name = None
        if form.profile_picture.data:
            pic_file = form.profile_picture.data
            filename = secure_filename(pic_file.filename)
            pic_name = f"{uuid.uuid1()}_{filename}"
            pic_file.save(os.path.join(upload_folder, pic_name))

        user = User(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            username=form.username.data,
            email=form.email.data,
            password=hashed_password,
            phone=form.phone.data,
            country=form.country.data,
            address=form.address.data,
            profile_picture=pic_name,
            last_login_at=datetime.now(timezone.utc),
        )

        # ----------------------------
        # Commit changes
        # ----------------------------
        try:
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            if "Duplicate entry" in str(e):
                flash("Username or email already exists", "error")
                return render_template("register_user.html", form=form)
            else:
                flash(f"Error creating user: {str(e)}", "error")
                return render_template("register_user.html", form=form)

        # ----------------------------
        # Log user in
        # ----------------------------
        session["user_id"] = user.id
        session["username"] = user.username
        session["first_name"] = user.first_name

        flash("Registration successful! You are now logged in.", "success")
        return redirect("/")

    return render_template("register_user.html", form=form)


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
    user: User = User.query.get_or_404(id)
    form = UserForm(obj=user)
    form.country.choices = COUNTRIES
    form.submit.label.text = "Update user"
    upload_folder = current_app.config["PROFILE_PICS_FOLDER"]

    if form.validate_on_submit():

        # Validate uniqueness
        # ----------------------------
        if not validate_updated_user(user, form):
            return render_template("update_user.html", form=form, user=user)

        # ----------------------------
        # Update basic fields
        # ----------------------------
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.username = form.username.data
        user.email = form.email.data
        user.phone = form.phone.data
        user.country = form.country.data
        user.address = form.address.data

        # ----------------------------
        # Update password (optional)
        # ----------------------------
        if form.password.data:
            user.password = hashlib.sha256(form.password.data.encode()).hexdigest()
            # recommended:
            # user.password = generate_password_hash(form.password.data)

        # ----------------------------
        # Picture handling
        # ----------------------------
        remove_requested = request.form.get("remove_picture")
        new_picture = form.profile_picture.data

        if new_picture:
            filename = secure_filename(new_picture.filename)
            pic_name = f"{uuid.uuid1()}_{filename}"

            save_path = os.path.join(upload_folder, pic_name)
            new_picture.save(save_path)

            delete_profile_picture(user.profile_picture)
            user.profile_picture = pic_name

        elif remove_requested:
            delete_profile_picture(user.profile_picture)
            user.profile_picture = None

        # ----------------------------
        # Commit changes
        # ----------------------------
        try:
            db.session.commit()
            flash("User updated successfully", "success")
            return redirect(f"/update/{user.id}")
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating user: {str(e)}", "error")

    # ----------------------------
    # Validation errors
    # ----------------------------
    if form.is_submitted():
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", "error")

    return render_template("update_user.html", form=form, user=user)


# ---------------
# HELPER METHDOS
# ---------------


def validate_updated_user(user: User, form: UserForm) -> bool:
    """
    Checks if username or email are unique before updating.
    If a value is not unique, flashes a message and resets the form field.
    Returns True if validation passed, False if there was a conflict.
    """
    if form.username.data != user.username:
        if User.query.filter_by(username=form.username.data).first():
            flash("Username already taken.", "error")
            form.username.data = user.username
            return False

    if form.email.data != user.email:
        if User.query.filter_by(email=form.email.data).first():
            form.email.data = user.email
            flash("Email already in use.", "error")
            return False

    return True
