from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from constants.raffle_status import RaffleStatus
from jobs.raffles_processor import transfer_moeny
from models.ticket_model import Ticket
from models.raffle_model import Raffle
from services.courier_service import ship_prize
from forms.pickup_address_form import PickupAddressForm
from services.prize_delivery_service import transition
from services.notifications_service import (
    queue_message_for_raffle,
    send_external_notifications,
)
from constants.countries import COUNTRIES
from constants.delivery_status import PrizeDeliveryStatus
from constants.message_category import MessageCategory
from forms.delivery_address_form import DeliveryAddressForm
from models.prize_delivery_model import PrizeDelivery
from db import db
from utils.helpers import is_valid_phone_number, login_required

prize_delivery_bp = Blueprint(
    "prize_delivery_bp", __name__, url_prefix="/prize-deliveries"
)


# ----------------------------
# Winner provides / confirms the delivery address
# GET  -> show the prefilled form
# POST -> save the address and advance the delivery
# ----------------------------
@prize_delivery_bp.route("/<int:id>/delivery-address", methods=["GET", "POST"])
@login_required
def provide_delivery_address(id):
    user_id = get_current_user_id()
    prize_delivery: PrizeDelivery = PrizeDelivery.query.get_or_404(id)

    if user_id != prize_delivery.winner_user_id:
        flash("You are not allowed to access this delivery.", "error")
        return redirect(url_for("raffle_bp.get_raffles"))

    form = DeliveryAddressForm(obj=prize_delivery)
    form.delivery_country.choices = COUNTRIES

    if prize_delivery.status != PrizeDeliveryStatus.PENDING_DELIVERY_ADDRESS:
        flash("The delivery address can no longer be changed.", "error")
        return render_template(
            "delivery_address.html", form=form, prize_delivery=prize_delivery
        )

    if form.validate_on_submit():
        is_valid_phone, phone_error = is_valid_phone_number(form.delivery_phone.data)
        if not is_valid_phone:
            flash(phone_error, "error")
            return render_template(
                "delivery_address.html", form=form, prize_delivery=prize_delivery
            )

        if not transition(
            prize_delivery=prize_delivery,
            new_status=PrizeDeliveryStatus.PENDING_PICKUP_ADDRESS,
            actor_id=user_id,
            note="Winner user has set the delivery address",
        ):
            flash("You are not allowed to change the delivery status.", "error")
            return render_template(
                "delivery_address.html", form=form, prize_delivery=prize_delivery
            )

        prize_delivery.delivery_name = form.delivery_name.data
        prize_delivery.delivery_address = form.delivery_address.data
        prize_delivery.delivery_phone = form.delivery_phone.data
        prize_delivery.delivery_country = form.delivery_country.data

        # In-app message is DB state: stage it inside the transaction so it commits
        # atomically with the address + status change. It's the creator's turn now.
        creator_message = (
            f"The winner provided their delivery address for raffle "
            f"'{prize_delivery.raffle.title}'. Please provide your pickup address "
            f"so the courier can collect the prize."
        )
        queue_message_for_raffle(
            prize_delivery.creator,
            creator_message,
            prize_delivery.raffle,
            prize_delivery,
            category=MessageCategory.INFO,
        )

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f"Error saving delivery address: {str(e)}", "error")
            return render_template(
                "delivery_address.html", form=form, prize_delivery=prize_delivery
            )

        # External side effects: only after the state is durably committed.
        send_external_notifications(prize_delivery.creator, creator_message)

        flash("Delivery address saved successfully", "success")
        return redirect(url_for("raffle_bp.get_raffle", id=prize_delivery.raffle_id))

    if form.is_submitted():
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", "error")

    return render_template(
        "delivery_address.html", form=form, prize_delivery=prize_delivery
    )


# ----------------------------
# Creator of raffle provides / confirms the pickup address
# GET  -> show the prefilled form
# POST -> save the address and advance the delivery
# ----------------------------
@prize_delivery_bp.route("/<int:id>/pickup-address", methods=["GET", "POST"])
@login_required
def provide_pickup_address(id):
    user_id = get_current_user_id()
    prize_delivery: PrizeDelivery = PrizeDelivery.query.get_or_404(id)

    if user_id != prize_delivery.creator_user_id:
        flash("You are not allowed to access this delivery.", "error")
        return redirect(url_for("raffle_bp.get_raffles"))

    form = PickupAddressForm(obj=prize_delivery)
    form.pickup_country.choices = COUNTRIES

    if prize_delivery.status != PrizeDeliveryStatus.PENDING_PICKUP_ADDRESS:
        flash("The pickup address can no longer be changed.", "error")
        return render_template(
            "pickup_address.html", form=form, prize_delivery=prize_delivery
        )

    if form.validate_on_submit():
        is_valid_phone, phone_error = is_valid_phone_number(form.pickup_phone.data)
        if not is_valid_phone:
            flash(phone_error, "error")
            return render_template(
                "pickup_address.html", form=form, prize_delivery=prize_delivery
            )

        if not transition(
            prize_delivery=prize_delivery,
            new_status=PrizeDeliveryStatus.WAITING_FOR_SHIPMENT,
            actor_id=user_id,
            note="Raffle creator has set the pickup address",
        ):
            flash("You are not allowed to change the delivery status.", "error")
            return render_template(
                "pickup_address.html", form=form, prize_delivery=prize_delivery
            )

        prize_delivery.pickup_name = form.pickup_name.data
        prize_delivery.pickup_address = form.pickup_address.data
        prize_delivery.pickup_phone = form.pickup_phone.data
        prize_delivery.pickup_country = form.pickup_country.data

        winner_message = (
            f"The prize pickup for raffle '{prize_delivery.raffle.title}' has been "
            f"arranged. Your prize is on its way."
        )
        queue_message_for_raffle(
            prize_delivery.winner,
            winner_message,
            prize_delivery.raffle,
            category=MessageCategory.INFO,
        )

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f"Error saving pickup address: {str(e)}", "error")
            return render_template(
                "pickup_address.html", form=form, prize_delivery=prize_delivery
            )

        send_external_notifications(prize_delivery.winner, winner_message)

        if ship_prize(prize_delivery):
            delivered_message = (
                f"Your prize for raffle '{prize_delivery.raffle.title}' has been "
                f"delivered. Please confirm or contest it."
            )
            queue_message_for_raffle(
                prize_delivery.winner,
                delivered_message,
                prize_delivery.raffle,
                prize_delivery,
                category=MessageCategory.INFO,
            )
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                flash(f"Error notifying the winner: {str(e)}", "warning")
            else:
                send_external_notifications(prize_delivery.winner, delivered_message)

            flash("Pickup address saved successfully", "success")
        else:
            flash(
                "Pickup address saved, but shipping could not be arranged yet.",
                "warning",
            )
        return redirect(url_for("raffle_bp.get_raffle", id=prize_delivery.raffle_id))

    if form.is_submitted():
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", "error")

    return render_template(
        "pickup_address.html", form=form, prize_delivery=prize_delivery
    )


@prize_delivery_bp.route("/<int:id>/review", methods=["GET"])
@login_required
def review_prize(id):
    user_id = get_current_user_id()
    prize_delivery: PrizeDelivery = PrizeDelivery.query.get_or_404(id)

    raffle: Raffle = prize_delivery.raffle
    user_ticket_count = Ticket.query.filter_by(raffle_id=id, user_id=user_id).count()

    if user_id != prize_delivery.winner_user_id:
        flash("You are not allowed to access this delivery.", "error")
        return redirect(url_for("raffle_bp.get_raffles"))

    if prize_delivery.status != PrizeDeliveryStatus.PRIZE_DELIVERED:
        flash("The pickup address can no longer be changed.", "error")
        return redirect(url_for("raffle_bp.get_raffles"))

    return render_template(
        "review_prize.html",
        prize_delivery=prize_delivery,
        raffle=raffle,
        user_ticket_count=user_ticket_count,
    )


@prize_delivery_bp.route("/<int:id>/accept", methods=["POST"])
@login_required
def accept_prize(id):
    user_id = get_current_user_id()
    prize_delivery: PrizeDelivery = PrizeDelivery.query.get_or_404(id)
    raffle: Raffle = prize_delivery.raffle

    if user_id != prize_delivery.winner_user_id:
        flash("You are not allowed to access this delivery.", "error")
        return redirect(url_for("raffle_bp.get_raffles"))

    if prize_delivery.status != PrizeDeliveryStatus.PRIZE_DELIVERED:
        flash("This prize can no longer be accepted.", "error")
        return redirect(url_for("raffle_bp.get_raffles"))

    # 1. Change status of PrizeDelivery to: PRIZE_ACCEPTED
    if not transition(
        prize_delivery=prize_delivery,
        new_status=PrizeDeliveryStatus.PRIZE_ACCEPTED,
        actor_id=user_id,
        note="Prize accepted",
    ):
        flash(
            "You could not accept the prize - there was a problem while changing the status",
            "error",
        )
        return redirect(url_for("raffle_bp.get_raffles"))

    # 2. Message the raffle creator
    creator_message = (
        f"The winner accepted the delivery for raffle "
        f"'{prize_delivery.raffle.title}'. Please send us your bank account id at "
        f"raffle.winners@raffle.com so we can send you the prize."
    )
    queue_message_for_raffle(
        prize_delivery.creator,
        creator_message,
        prize_delivery.raffle,
        prize_delivery,
        category=MessageCategory.INFO,
    )

    # 3. Change status of Raffle to: COMPLETED
    raffle.status = RaffleStatus.COMPLETED

    # 4. Save the data
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print("Error: ", e)
        flash("Unable to accept the raffle prize", "error")
        return redirect(url_for("raffle_bp.get_raffles"))

    # 5. External side effects: only after the state is durably committed. The payout
    if not transfer_moeny(prize_delivery.creator):
        flash(
            "Prize accepted, but the payout could not be arranged yet.",
            "warning",
        )
    send_external_notifications(prize_delivery.creator, creator_message)

    # 6. Flash message and redirect
    flash("Prize accepted", "success")

    return redirect(url_for("raffle_bp.get_raffles"))


@prize_delivery_bp.route("/<int:id>/contest", methods=["POST"])
@login_required
def contest_prize(id):
    user_id = get_current_user_id()
    prize_delivery: PrizeDelivery = PrizeDelivery.query.get_or_404(id)

    if user_id != prize_delivery.winner_user_id:
        flash("You are not allowed to access this delivery.", "error")
        return redirect(url_for("raffle_bp.get_raffles"))

    if prize_delivery.status != PrizeDeliveryStatus.PRIZE_DELIVERED:
        flash("The pickup address can no longer be changed.", "error")
        return redirect(url_for("raffle_bp.get_raffles"))

    return render_template("contest_prize.html", prize_delivery=prize_delivery)


def get_current_user_id() -> int:
    return session.get("user_id")
