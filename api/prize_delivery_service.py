from constants.delivery_status import PrizeDeliveryStatus
from models.prize_delivery_log_model import PrizeDeliveryLog
from models.prize_delivery_model import PrizeDelivery
import secrets
import string


# Builds the prize delivery for a won raffle. Pickup details are prefilled from
# the raffle creator; the winner only provides name/email now and fills in the
# shipping address later via the address form. Returns the object - the caller
# adds it to the session and owns the transaction.
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
        status=PrizeDeliveryStatus.PENDING_ADDRESS,
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


# Builds a single audit row for a prize delivery. Linked through the `delivery`
# relationship so it works before the delivery has been flushed (no id yet).
# actor is None for system-driven transitions (e.g. the timeout job). Returns the
# object - the caller adds it to the session.
def create_prize_delivery_log(
    prize_delivery: PrizeDelivery,
    from_status,
    to_status,
    actor=None,
    note=None,
) -> PrizeDeliveryLog:
    return PrizeDeliveryLog(
        delivery=prize_delivery,
        from_status=from_status,
        to_status=to_status,
        actor_user_id=actor.id if actor else None,
        note=note,
    )
