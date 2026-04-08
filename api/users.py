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
    url_for,
)

from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from datetime import datetime, timezone
from exceptions.user_exceptions import OldPasswordIncorrect, OldPasswordRequired
from constants.countries import COUNTRIES
from forms.user_form import DeleteSelfAccountForm, UserForm, UserSelfUpdateForm
from db import db
from models.user_model import User
from utils.helpers import (
    allowed_file,
    is_safe_url,
    is_valid_email,
    is_valid_phone_number,
    login_required,
)
from utils.files import delete_profile_picture
from werkzeug.security import check_password_hash
from werkzeug.exceptions import Forbidden

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
        hashed_password = generate_password_hash(form.password.data)

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
@login_required
def update(id):
    current_user_id = session.get("user_id")

    actor: User = User.query.get_or_404(current_user_id)
    target_user: User = User.query.get_or_404(id)

    is_self = actor.id == target_user.id
    is_admin = actor.is_admin

    if not is_self and not is_admin:
        abort(403)

    # Choose the right form
    if is_self:
        form = UserSelfUpdateForm(obj=target_user)
    else:
        form = UserForm(obj=target_user)

    form.country.choices = COUNTRIES
    form.submit.label.text = "Update user"
    upload_folder = current_app.config["PROFILE_PICS_FOLDER"]

    # Get next URL
    # Get next from GET or POST
    next_url = request.args.get("next") or request.form.get("next")

    # Fallback if missing or unsafe
    if not next_url or not is_safe_url(next_url):
        next_url = url_for("home")

    if form.validate_on_submit():

        # Validate uniqueness
        # ----------------------------
        if not validate_updated_user(target_user, form):
            return render_template(
                "update_user.html", form=form, user=target_user, next=next_url
            )

        # ----------------------------
        # Update basic fields
        # ----------------------------
        target_user.first_name = form.first_name.data
        target_user.last_name = form.last_name.data
        target_user.username = form.username.data
        target_user.email = form.email.data
        target_user.phone = form.phone.data
        target_user.country = form.country.data
        target_user.address = form.address.data

        if form.password.data:
            old_password = form.old_password.data if is_self else None
            try:
                update_password(
                    actor=actor,
                    target_user=target_user,
                    new_password=form.password.data,
                    old_password=old_password,
                )
            except OldPasswordRequired:
                form.old_password.errors.append("Old password is required")
            except OldPasswordIncorrect:
                form.old_password.errors.append("Old password is not correct")
            except Forbidden:
                abort(403)

            if form.errors:
                return render_template(
                    "update_user.html", form=form, user=target_user, next=next_url
                )

        remove_photo_requested = request.form.get("remove_picture")
        new_picture = form.profile_picture.data

        if new_picture:
            filename = secure_filename(new_picture.filename)
            pic_name = f"{uuid.uuid1()}_{filename}"

            save_path = os.path.join(upload_folder, pic_name)
            new_picture.save(save_path)

            delete_profile_picture(target_user.profile_picture)
            target_user.profile_picture = pic_name

        elif remove_photo_requested:
            delete_profile_picture(target_user.profile_picture)
            target_user.profile_picture = None

        try:
            db.session.commit()
            flash("User updated successfully", "success")
            # ✅ THIS is the important redirect
            return redirect(next_url)
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating user: {str(e)}", "error")

    if form.is_submitted():
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", "error")

    return render_template(
        "update_user.html", form=form, user=target_user, next=next_url
    )


# ------------------------
# DELETE ACCOUNT AS ADMIN
# ------------------------
@users_bp.route("/users/delete/<int:id>", methods=["POST"])
@login_required
def delete(id):
    current_user_id = session.get("user_id")
    actor: User = User.query.get_or_404(current_user_id)
    if not actor.is_admin:
        abort(403)

    user_to_delete: User = User.query.get_or_404(id)
    profile_picture = user_to_delete.profile_picture

    try:
        db.session.delete(user_to_delete)
        db.session.commit()

        if profile_picture:
            delete_profile_picture(profile_picture)

        flash("User deleted successfully", "success")
        return redirect(url_for("users_bp.get_users"))

    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting user: {str(e)}", "danger")
        return redirect(url_for("users_bp.get_users"))


# -----------------------
# DELETE ACCOUNT AS SELF
# -----------------------
@users_bp.route("/account/delete", methods=["POST"])
@login_required
def delete_account():
    current_user_id = session.get("user_id")
    form = DeleteSelfAccountForm()

    if not form.validate_on_submit():
        for field, errors in form.errors.items():
            for error in errors:
                flash(error, "danger")
        return redirect(url_for("users_bp.update", id=current_user_id))

    user_to_delete: User = User.query.get_or_404(current_user_id)
    picture_to_delete = user_to_delete.profile_picture

    if not check_password_hash(user_to_delete.password, form.password.data):
        flash("Incorrect password,", "danger")
        return redirect(url_for("users_bp.update", id=current_user_id))

    try:
        db.session.delete(user_to_delete)
        db.session.commit()

        if picture_to_delete:
            delete_profile_picture(picture_to_delete)

        flash("User deleted succesfully,", "success")
        return redirect(url_for("auth_bp.login"))
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting account: {str(e)}", "danger")
        return redirect(url_for("users_bp.update", id=current_user_id))


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


# Update password helper
def update_password(
    actor: User, target_user: User, new_password: str, old_password: str | None = None
):
    if actor.id == target_user.id:
        if not old_password:
            raise OldPasswordRequired()
        if not check_password_hash(target_user.password, old_password):
            raise OldPasswordIncorrect()
    elif not actor.is_admin:
        raise Forbidden()

    target_user.password = generate_password_hash(new_password)
