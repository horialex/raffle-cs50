from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from services.prize_delivery_service import transition
from constants.countries import COUNTRIES
from constants.delivery_status import PrizeDeliveryStatus
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
            new_status=PrizeDeliveryStatus.PENDING_SENDER_ADDRESS,
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

        try:
            db.session.commit()
            flash("Delivery address saved successfully", "success")
            return redirect(
                url_for("raffle_bp.get_raffle", id=prize_delivery.raffle_id)
            )
        except Exception as e:
            db.session.rollback()
            flash(f"Error saving delivery address: {str(e)}", "error")

    if form.is_submitted():
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", "error")

    return render_template(
        "delivery_address.html", form=form, prize_delivery=prize_delivery
    )


# ----------------------------
# Creatoer provides / confirms the pickup address
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

    form = DeliveryAddressForm(obj=prize_delivery)
    form.delivery_country.choices = COUNTRIES

    if prize_delivery.status != PrizeDeliveryStatus.PENDING_SENDER_ADDRESS:
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
            new_status=PrizeDeliveryStatus.WAITING_FOR_SHIPMENT,
            actor_id=user_id,
            note="Raffle creator has set the delivery address",
        ):
            flash("You are not allowed to change the delivery status.", "error")
            return render_template(
                "delivery_address.html", form=form, prize_delivery=prize_delivery
            )

        prize_delivery.delivery_name = form.delivery_name.data
        prize_delivery.delivery_address = form.delivery_address.data
        prize_delivery.delivery_phone = form.delivery_phone.data
        prize_delivery.delivery_country = form.delivery_country.data

        # TODO: Call Coureier delivery methods from here onwards

        try:
            db.session.commit()
            flash("Pickup address saved successfully", "success")
            return redirect(
                url_for("raffle_bp.get_raffle", id=prize_delivery.raffle_id)
            )
        except Exception as e:
            db.session.rollback()
            flash(f"Error saving delivery address: {str(e)}", "error")

    if form.is_submitted():
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", "error")

    return render_template(
        "delivery_address.html", form=form, prize_delivery=prize_delivery
    )


def get_current_user_id() -> int:
    return session.get("user_id")
