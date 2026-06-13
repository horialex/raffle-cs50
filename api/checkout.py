from datetime import date, datetime, timezone

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    session,
    url_for,
)

from db import db
from forms.checkout_form import CheckoutForm
from models.raffle_model import Raffle
from models.ticket_model import Ticket
from utils.helpers import login_required

checkout_bp = Blueprint("checkout_bp", __name__, url_prefix="/raffles")


@checkout_bp.route("/<int:raffle_id>/checkout", methods=["GET"])
@login_required
def checkout(raffle_id):
    raffle: Raffle = Raffle.query.get_or_404(raffle_id)

    if not raffle.is_active:
        flash("This raffle is not open for ticket purchases.", "error")
        return redirect(url_for("raffle_bp.get_raffle", id=raffle_id))

    user_tickets_count = Ticket.query.filter_by(
        raffle_id=raffle_id, user_id=session.get("user_id")
    ).count()

    if user_tickets_count >= raffle.maximum_tickets_per_user:
        flash("You can't buy more tickets for this raffle", "error")
        return redirect(url_for("raffle_bp.get_raffle", id=raffle_id))

    form = CheckoutForm()

    return render_template(
        "raffle/checkout.html",
        form=form,
        raffle=raffle,
        already_bought=user_tickets_count,
    )


@checkout_bp.route("/<int:raffle_id>/create-payment", methods=["POST"])
@login_required
def create_payment(raffle_id):
    raffle: Raffle = Raffle.query.get_or_404(raffle_id)
    form = CheckoutForm()
    quantity = form.quantity.data
    user_id = session.get("user_id")

    user_tickets_count = Ticket.query.filter_by(
        raffle_id=raffle_id, user_id=user_id
    ).count()

    if not raffle.is_active:
        flash("This raffle is not open for ticket purchases.", "error")
        return redirect(url_for("raffle_bp.get_raffle", id=raffle_id))

        # Check raffle has not reached due date
    if raffle.due_date_utc < datetime.now(timezone.utc):
        flash("This raffle has already ended.", "error")
        return redirect(url_for("raffle_bp.get_raffle", id=raffle_id))

    remaining_available_tickets_conut = (
        raffle.maximum_tickets_per_user - user_tickets_count
    )

    if remaining_available_tickets_conut <= 0:
        flash("You reached the maximum tickets for this raffle", "danger")
        return redirect(url_for("raffle_bp.get_raffle", id=raffle_id))

    # Check maximum tickets per user not reached
    if quantity > remaining_available_tickets_conut:
        flash(
            f"You can only buy {remaining_available_tickets_conut} more ticket(s) for this raffle.",
            "error",
        )
        return redirect(url_for("checkout_bp.checkout", raffle_id=raffle_id))

    # Check for simmulated payment config
    if current_app.config["SIMULATE_PAYMENT"]:
        # Create session object
        session["pending_payment"] = {
            "raffle_id": raffle.id,
            "user_id": user_id,
            "quantity": quantity,
        }
        return redirect(url_for("checkout_bp.payment_success"))

    # TODO: Payment system integration - eg Vinted users: Mangopay
    flash("Payment system not configured.", "error")
    return redirect(url_for("checkout_bp.checkout", raffle_id=raffle_id))


@checkout_bp.route("/payment-success", methods=["GET"])
@login_required
def payment_success():
    pending_payment_obj = session.pop("pending_payment", None)

    if not pending_payment_obj:
        flash("No pending payment found.", "error")
        return redirect(url_for("raffle_bp.get_raffles"))

    raffle_id = pending_payment_obj["raffle_id"]
    user_id = pending_payment_obj["user_id"]
    quantity = pending_payment_obj["quantity"]

    raffle: Raffle = Raffle.query.get_or_404(raffle_id)

    tickets = []
    for _ in range(quantity):
        ticket = Ticket(raffle_id=raffle_id, user_id=user_id, price=raffle.ticket_price)
        tickets.append(ticket)

    try:
        db.session.add_all(tickets)
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash(
            "Something went wrong while saving your tickets. Please contact support.",
            "error",
        )
        return redirect(url_for("raffle_bp.get_raffle", id=raffle_id))

    flash(f"Payment successful! {quantity} ticket(s) purchased.", "success")
    return redirect(url_for("raffle_bp.get_raffle", id=raffle_id))
