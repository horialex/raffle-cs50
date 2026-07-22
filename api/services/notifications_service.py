from models.prize_delivery_model import PrizeDelivery
from db import db
from models.user_model import User
from models.raffle_model import Raffle
from models.ticket_model import Ticket
from models.message_model import Message


# ----------------------------
# External channels (call AFTER commit)
# ----------------------------
def notify_by_email(user: User, message: str) -> bool:
    # TODO: Implement this when an email provider is integrated
    print(f"Sending email to {user.email}: {message}")
    return True


def notify_by_sms(user: User, message: str) -> bool:
    # TODO: Implement this when an SMS provider is integrated
    print(f"Sending SMS to {user.phone}: {message}")
    return True


def send_external_notifications(user: User, message: str) -> bool:
    """Fire the external channels. Call only after the triggering transaction commits."""
    email_sent = notify_by_email(user, message)
    sms_sent = notify_by_sms(user, message)
    return email_sent and sms_sent


# ----------------------------
# In-app message (stage BEFORE commit)
# ----------------------------
def queue_message(
    user: User,
    message: str,
    raffle_id: int = None,
    ticket_id: int = None,
    prize_delivery=None,
    category: str = None,
) -> None:
    """Stage the in-app Message row in the current transaction (before commit).

    category ("win" | "loss" | "info") is the sender's declared sentiment; the UI
    uses it to tint the row. Leave None for a neutral message.
    """
    db.session.add(
        Message(
            user_id=user.id,
            body=message,
            raffle_id=raffle_id,
            ticket_id=ticket_id,
            prize_delivery=prize_delivery,
            category=category,
        )
    )
    print(f"Message queued for user {user.id}: {message}")


def queue_message_for_raffle(
    user: User,
    message: str,
    raffle: Raffle,
    prize_delivery: PrizeDelivery = None,
    category: str = None,
) -> None:
    queue_message(
        user,
        message,
        raffle_id=raffle.id,
        prize_delivery=prize_delivery,
        category=category,
    )


def queue_message_for_ticket(
    ticket: Ticket,
    message: str,
    prize_delivery: PrizeDelivery = None,
    category: str = None,
) -> None:
    queue_message(
        ticket.user,
        message,
        raffle_id=ticket.raffle_id,
        ticket_id=ticket.id,
        prize_delivery=prize_delivery,
        category=category,
    )
