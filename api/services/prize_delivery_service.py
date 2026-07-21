from db import db
from constants.delivery_status import PrizeDeliveryStatus
from models.prize_delivery_log_model import PrizeDeliveryLog
from models.prize_delivery_model import PrizeDelivery
import secrets
import string


def create_prize_delivery(raffle, winner_user) -> PrizeDelivery:
    creator = raffle.creator

    length = 24
    tracking_code = "".join(
        secrets.choice(string.ascii_letters + string.digits) for _ in range(length)
    )

    return PrizeDelivery(
        raffle_id=raffle.id,
        winner_user_id=winner_user.id,
        creator_user_id=creator.id,
        tracking_code=tracking_code,
        status=PrizeDeliveryStatus.PENDING_DELIVERY_ADDRESS,
        pickup_name=creator.first_name + " " + creator.last_name,
        pickup_address=creator.address,
        pickup_country=creator.country,
        pickup_phone=creator.phone,
        pickup_email=creator.email,
        delivery_name=winner_user.first_name + " " + winner_user.last_name,
        delivery_address=winner_user.address,
        delivery_country=winner_user.country,
        delivery_phone=winner_user.phone,
        delivery_email=winner_user.email,
    )


def create_prize_delivery_log(
    prize_delivery: PrizeDelivery,
    from_status,
    to_status,
    actor_id=None,
    note=None,
) -> PrizeDeliveryLog:
    return PrizeDeliveryLog(
        delivery=prize_delivery,
        from_status=from_status,
        to_status=to_status,
        actor_user_id=actor_id,
        note=note,
    )


ALLOWED_TRANSITIONS = {
    PrizeDeliveryStatus.PENDING_DELIVERY_ADDRESS: {
        PrizeDeliveryStatus.PENDING_SENDER_ADDRESS,
        PrizeDeliveryStatus.DELIVERY_TIMEOUT,
    },
    PrizeDeliveryStatus.PENDING_SENDER_ADDRESS: {
        PrizeDeliveryStatus.WAITING_FOR_SHIPMENT,
        PrizeDeliveryStatus.DELIVERY_TIMEOUT,
    },
    PrizeDeliveryStatus.WAITING_FOR_SHIPMENT: {
        PrizeDeliveryStatus.PRIZE_SENT,
        PrizeDeliveryStatus.DELIVERY_TIMEOUT,
    },
    PrizeDeliveryStatus.PRIZE_SENT: {
        PrizeDeliveryStatus.PRIZE_DELIVERED,
        PrizeDeliveryStatus.DELIVERY_FAILED,
    },
    PrizeDeliveryStatus.PRIZE_DELIVERED: {
        PrizeDeliveryStatus.PRIZE_ACCEPTED,
        PrizeDeliveryStatus.CONTESTED,
    },
    PrizeDeliveryStatus.CONTESTED: {
        PrizeDeliveryStatus.PRIZE_ACCEPTED,
        PrizeDeliveryStatus.PRIZE_REJECTED,
        PrizeDeliveryStatus.DELIVERY_TIMEOUT,
    },
}


def can_transition(
    prize_delivery: PrizeDelivery, new_status: PrizeDeliveryStatus
) -> bool:
    allowed = ALLOWED_TRANSITIONS.get(prize_delivery.status, set())
    if new_status in allowed:
        return True
    return False


def transition(
    prize_delivery: PrizeDelivery,
    new_status: PrizeDeliveryStatus,
    actor_id: int = None,
    note: str = None,
) -> bool:
    if not can_transition(prize_delivery, new_status):
        return False
    log = create_prize_delivery_log(
        prize_delivery, prize_delivery.status, new_status, actor_id, note
    )
    prize_delivery.status = new_status
    db.session.add(log)
    return True
