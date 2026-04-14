from flask import (
    Blueprint,
    redirect,
    render_template,
    request,
)

from models.raffle_model import Raffle
from db import db


USER_ROLE = "user"
ADMIN_ROLE = "admin"

raffle_bp = Blueprint("raffle_bp", __name__, url_prefix="/raffles")


# -----------------------------------
# Count raffles route - test endpoint
# -----------------------------------
@raffle_bp.route("/count_raffles")
def test():
    raffles = Raffle.query.all()
    return {"count": len(raffles)}


# ----------------------------
# List raffles
# GET /raffles
# ----------------------------
@raffle_bp.route("/", methods=["GET"])
def list_raffles():
    # TODO: Finish this
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 100)

    paginated_raffles = Raffle.query.order_by(Raffle.id).paginate(
        page=page, per_page=per_page, error_out=False
    )

    raffles: Raffle = [
        {
            "id": r.id,
            "creator_id": r.creator_id,
            "title": r.title,
            "description": r.last_name,
            "status": r.status,
            "ticket_price": r.ticket_price,
            "created_date": r.created_at,
            "due_date": r.due_date,
        }
        for r in paginated_raffles.items
    ]

    return render_template(
        "raffles.html",
        raffles=raffles,
        total=paginated_raffles.total,
        page=page,
        per_page=per_page,
    )


# ----------------------------
# Create Raffle
# ----------------------------
@raffle_bp.route("/create", methods=["GET", "POST"])
def create_raffle():
    # TODO: Implement this
    return redirect("/")
