from datetime import datetime, timezone

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
)

from constants.raffle_status import RaffleStatus
from utils.helpers import login_required
from forms.raffle_form import CreateRaffleForm
from models.raffle_model import Raffle
from db import db
from models.product_model import Product


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
@login_required
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
            "description": r.description,
            "status": r.status.value,
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
@login_required
def create_raffle():
    current_user_id = session.get("user_id")
    # current_user_id = get_current_user().id
    form = CreateRaffleForm()
    # min_due_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:00")
    # min_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if form.validate_on_submit():
        due_date = datetime.combine(
            form.due_date_date.data, datetime.min.time()
        ).replace(
            hour=int(form.due_date_hour.data),
            tzinfo=timezone.utc,  # adjust if you use another timezone
        )

        if due_date <= datetime.now(timezone.utc):
            flash("Due date must be in the future.", "error")
            return render_template("create_raffle.html", form=form)

        # Raffle part
        raffle = Raffle(
            creator_id=current_user_id,
            title=form.title.data,
            description=form.description.data,
            status=RaffleStatus.DRAFT,  # not needed necesarley
            minimum_required_tickets=form.minimum_required_tickets.data,
            maximum_tickets_per_user=form.maximum_tickets_per_user.data,
            ticket_price=form.ticket_price.data,
            due_date=due_date,
        )

        # Prize part
        products_to_save = []

        # Save raffle in the db
        try:
            db.session.add(raffle)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating raffle: {str(e)}", "error")
            return render_template("create_raffle.html", form=form)

        flash("Raffle created.", "success")
        return redirect("/")

    # if form.is_submitted():
    #     for field, errors in form.errors.items():
    #         for error in errors:
    #             flash(f"{field}: {error}", "error")

    return render_template("create_raffle.html", form=form)
