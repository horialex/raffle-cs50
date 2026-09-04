from flask import current_app
from db import db
from constants.delivery_status import PrizeDeliveryStatus
from services.prize_delivery_service import transition
from models.prize_delivery_model import PrizeDelivery


def call_courier(prize_delivery: PrizeDelivery) -> bool:
    if current_app.config["SIMULATE_SHIPPING"]:
        print("[Simmulated] Call courier")
        return True

    print("Shipping provider not configured - skipping courier.")
    return False


def deliver_package_to_courier(prize_delivery: PrizeDelivery) -> bool:
    if current_app.config["SIMULATE_SHIPPING"]:
        print("[Simulated] Courier arrived")
        print("[Simulated] Package given to courier")
        print("[Simulated] Courier on route")
        if not transition(
            prize_delivery=prize_delivery,
            new_status=PrizeDeliveryStatus.PRIZE_SENT,
            note="Courier collected the prize (simulated)",
        ):
            return False
        print(f"Delivery {prize_delivery.id}: prize marked SENT (simulated).")
        return True
    print("Shipping provider not configured - skipping courier.")
    return False


def prize_delivered(prize_delivery: PrizeDelivery) -> bool:
    if current_app.config["SIMULATE_SHIPPING"]:
        print("[Simulated] Package delivered")
        if not transition(
            prize_delivery=prize_delivery,
            new_status=PrizeDeliveryStatus.PRIZE_DELIVERED,
            note="Courier delivered the prize (simulated)",
        ):
            return False
        print(f"Delivery {prize_delivery.id}: prize marked DELIVERED (simulated).")
        return True
    print("Shipping provider not configured - skipping courier.")
    return False


def ship_prize(prize_delivery: PrizeDelivery) -> bool:
    if not current_app.config["SIMULATE_SHIPPING"]:
        print("Shipping provider not configured - skipping courier.")
        return False

    try:
        if not (
            call_courier(prize_delivery)
            and deliver_package_to_courier(prize_delivery)
            and prize_delivered(prize_delivery)
        ):
            db.session.rollback()
            return False
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Shipping failed for delivery {prize_delivery.id}: {e}")
        return False


def courier_collected_return(prize_delivery: PrizeDelivery) -> bool:
    if current_app.config["SIMULATE_SHIPPING"]:
        print("[Simulated] Courier arrived at winner's address")
        print("[Simulated] Package handed back to courier")
        print("[Simulated] Courier returning prize to raffle creator")
        if not transition(
            prize_delivery=prize_delivery,
            new_status=PrizeDeliveryStatus.PRIZE_RETURN_SENT,
            note="Courier collected the prize for return (simulated)",
        ):
            return False
        print(f"Delivery {prize_delivery.id}: return marked SENT (simulated).")
        return True
    print("Shipping provider not configured - skipping courier.")
    return False


def prize_return_delivered(prize_delivery: PrizeDelivery) -> bool:
    if current_app.config["SIMULATE_SHIPPING"]:
        print("[Simulated] Prize delivered back to raffle creator")
        if not transition(
            prize_delivery=prize_delivery,
            new_status=PrizeDeliveryStatus.PRIZE_RETURNED,
            note="Courier returned the prize to the raffle creator (simulated)",
        ):
            return False
        print(f"Delivery {prize_delivery.id}: return marked RETURNED (simulated).")
        return True
    print("Shipping provider not configured - skipping courier.")
    return False


def return_prize(prize_delivery: PrizeDelivery) -> bool:
    if not current_app.config["SIMULATE_SHIPPING"]:
        print("Shipping provider not configured - skipping courier.")
        return False

    try:
        if not (
            call_courier(prize_delivery)
            and courier_collected_return(prize_delivery)
            and prize_return_delivered(prize_delivery)
        ):
            db.session.rollback()
            return False
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Prize return failed for delivery {prize_delivery.id}: {e}")
        return False
