import hashlib

from flask import Blueprint, flash, redirect, render_template, request, session
from db import get_db_connection

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    session.clear()

    if request.method == "POST":
        if not request.form.get("username"):
            flash("Must provide username", "error")
            return render_template("login.html")

        if not request.form.get("password"):
            flash("Must provide password", "error")
            return render_template("login.html")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(
                "SELECT * FROM users WHERE username = %s",
                (request.form.get("username"),),
            )

            row = cursor.fetchone()

            if row is None:
                flash("Invalid username or password", "error")
                return render_template("login.html")

            password = request.form.get("password")
            hashed_input = hashlib.sha256(password.encode()).hexdigest()

            if row["password"] != hashed_input:
                flash("Invalid username or password", "error")
                return render_template("login.html")

            print(row)
            session["user_id"] = row["id"]
            session["username"] = row["username"]
            session["first_name"] = row["first_name"]

            return redirect("/")

        finally:
            cursor.close()
            conn.close()

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    """Log user out"""
    session.clear()
    return redirect("/login")
