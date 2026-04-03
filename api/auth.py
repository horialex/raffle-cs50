import hashlib
from flask import Blueprint, flash, redirect, render_template, request, session
from forms.login_form import LoginForm
from db import db
from models.user_model import User
from datetime import datetime, timezone
from werkzeug.security import check_password_hash

auth_bp = Blueprint("auth_bp", __name__)


# ----------------------------
# Login
# ----------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data

        # ----------------------------
        # Query user
        # ----------------------------
        user: User = User.query.filter_by(username=username).first()

        if user is None:
            flash("Invalid username or password", "error")
            return render_template("login.html", form=form)

        if not check_password_hash(user.password, password):
            flash("Invalid username or password", "error")
            return render_template("login.html", form=form)

        session.clear()
        # ----------------------------
        # Log user in
        # ----------------------------
        user.last_login_at = datetime.now(timezone.utc)
        session["user_id"] = user.id
        session["username"] = user.username
        session["first_name"] = user.first_name

        db.session.commit()
        flash(f"Welcome back, {user.first_name}!", "success")
        return redirect("/")

    return render_template("login.html", form=form)


# ----------------------------
# Logout
# ----------------------------
@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/login")
