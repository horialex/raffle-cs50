import hashlib
from flask import Blueprint, flash, redirect, render_template, request, session
from db import db
from models.user_model import User

auth_bp = Blueprint("auth_bp", __name__)


# ----------------------------
# Login
# ----------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    session.clear()

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username:
            flash("Must provide username", "error")
            return render_template("login.html")
        if not password:
            flash("Must provide password", "error")
            return render_template("login.html")

        # ----------------------------
        # Query user
        # ----------------------------
        user = User.query.filter_by(username=username).first()

        if user is None:
            flash("Invalid username or password", "error")
            return render_template("login.html")

        hashed_input = hashlib.sha256(password.encode()).hexdigest()
        if user.password != hashed_input:
            flash("Invalid username or password", "error")
            return render_template("login.html")

        # ----------------------------
        # Log user in
        # ----------------------------
        session["user_id"] = user.id
        session["username"] = user.username
        session["first_name"] = user.first_name

        return redirect("/")

    return render_template("login.html")


# ----------------------------
# Logout
# ----------------------------
@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/login")
