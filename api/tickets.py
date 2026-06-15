from flask import Blueprint, render_template, session

from utils.helpers import login_required

USER_ROLE = "user"
ADMIN_ROLE = "admin"

tickets_bp = Blueprint("tickets_bp", __name__, url_prefix="/tickets")


# ----------------------------
# My Tickets
# ----------------------------
@tickets_bp.route("/")
@login_required
def my_tickets():
    current_user_id = session.get("user_id")

    return render_template(
        "/tickets/my_tickets.html",
    )
