from datetime import datetime, timezone

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
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
    raffle = Raffle.query.get_or_404(raffle_id)

    if not raffle.is_active:
        flash("This raffle is not open for ticket purchases.", "error")
        return redirect(url_for("raffle_bp.get_raffle", id=raffle_id))

    already_bought = Ticket.query.filter_by(
        raffle_id=raffle_id, user_id=session.get("user_id")
    ).count()

    form = CheckoutForm()
    total_price = raffle.ticket_price

    return render_template(
        "raffle/checkout.html",
        form=form,
        raffle=raffle,
        already_bought=already_bought,
        total_price=total_price,
    )


@checkout_bp.route("/<int:raffle_id>/create-payment", methods=["POST"])
@login_required
def create_payment(raffle_id):
    raffle = Raffle.query.get_or_404(raffle_id)

    if not raffle.is_active:
        flash("This raffle is not open for ticket purchases.", "error")
        return redirect(url_for("raffle_bp.get_raffle", id=raffle_id))

    form = CheckoutForm()
    if not form.validate_on_submit():
        flash("Invalid form submission.", "error")
        return redirect(url_for("checkout_bp.checkout", raffle_id=raffle_id))

    user_id = session.get("user_id")
    quantity = form.quantity.data

    already_bought = Ticket.query.filter_by(
        raffle_id=raffle_id, user_id=user_id
    ).count()

    if quantity > raffle.maximum_tickets_per_user - already_bought:
        flash(
            f"You can only buy {raffle.maximum_tickets_per_user - already_bought} more ticket(s) for this raffle.",
            "error",
        )
        return redirect(url_for("checkout_bp.checkout", raffle_id=raffle_id))

    # For now we simmulate the payment
    if current_app.config["SIMULATE_PAYMENT"]:
        session["pending_payment"] = {
            "raffle_id": raffle_id,
            "user_id": user_id,
            "quantity": quantity,
        }
        return redirect(url_for("checkout_bp.payment_success"))

    # TODO: Stripe integration or other payment system integeration - eg Vinted users: Mangopay
    flash("Payment system not configured.", "error")
    return redirect(url_for("checkout_bp.checkout", raffle_id=raffle_id))


@checkout_bp.route("/payment-success", methods=["GET"])
@login_required
def payment_success():
    pending = session.pop("pending_payment", None)
    if not pending:
        flash("No pending payment found.", "error")
        return redirect(url_for("raffle_bp.get_raffles"))

    raffle_id = pending["raffle_id"]
    user_id = pending["user_id"]
    quantity = pending["quantity"]

    raffle = Raffle.query.get_or_404(raffle_id)

    if raffle.due_date < datetime.now(timezone.utc):
        flash("This raffle has already ended.", "error")
        return redirect(url_for("raffle_bp.get_raffle", id=raffle_id))

    tickets = []
    for _ in range(quantity):
        ticket = Ticket(user_id=user_id, raffle_id=raffle_id, price=raffle.ticket_price)
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
