from db import db
from models.user_model import User
from models.raffle_model import Raffle
from models.ticket_model import Ticket
from models.message_model import Message


def notify_by_email(user: User, message: str, raffle_id: int, ticket_id: int) -> bool:
    # TODO: Implement this when an email provider is integrated
    print(f"Sending email to {user.email}: {message}")
    return True


def notify_by_sms(user: User, message: str, raffle_id: int, ticket_id: int) -> bool:
    # TODO: Implement this when an SMS provider is integrated
    print(f"Sending SMS to {user.phone}: {message}")
    return True


def notify_by_message(user: User, message: str, raffle_id: int, ticket_id: int) -> bool:
    db.session.add(
        Message(user_id=user.id, body=message, raffle_id=raffle_id, ticket_id=ticket_id)
    )
    print(f"Message queued for user {user.id}: {message}")
    return True


def notify_user(user: User, message: str) -> bool:
    return _notify(user, message, None, None)


def notify_user_for_raffle(user: User, message: str, raffle: Raffle) -> bool:
    return _notify(user, message, raffle.id, None)


def notify_user_for_ticket(ticket: Ticket, message: str) -> bool:
    return _notify(ticket.user, message, ticket.raffle_id, ticket.id)


def _notify(user: User, message: str, raffle_id: int, ticket_id: int) -> bool:
    email_sent = notify_by_email(user, message, raffle_id, ticket_id)
    sms_sent = notify_by_sms(user, message, raffle_id, ticket_id)
    message_sent = notify_by_message(user, message, raffle_id, ticket_id)
    return email_sent and sms_sent and message_sent
