from datetime import date
from flask import current_app
from sqlalchemy import func
from db import db
from models.user_model import User
from constants.ticket_status import TicketStatus
from constants.raffle_status import RaffleStatus
from models.raffle_model import Raffle
from models.ticket_model import Ticket
from models.message_model import Message

RAFFLE_NOT_TRIGGERED_MESSAGE = "The raffle {title} did not take place because the minimum required tickets were not sold!"


# Grabs all the active raffles that have the due date in the past
def get_raffles_due_for_settlement() -> list[Raffle]:
    raffles = Raffle.query.filter(
        Raffle.status == RaffleStatus.ACTIVE, func.date(Raffle.due_date) < date.today()
    ).all()

    return raffles


# Splits raffles in 2 lists, succesfull ones - those that have reached the minimum number of tickets sold and those that didn't
def split_raffles_by_minimum_tickets(
    raffles: list[Raffle],
) -> tuple[list[Raffle], list[Raffle]]:
    successful_raffles: list[Raffle] = []
    failed_raffles: list[Raffle] = []

    for raffle in raffles:
        if has_raffle_reached_minimum_tickets_sold(raffle):
            successful_raffles.append(raffle)
        else:
            failed_raffles.append(raffle)

    return successful_raffles, failed_raffles


# Check's if the raffle has reached the required number of tickets to be sold
def has_raffle_reached_minimum_tickets_sold(raffle: Raffle) -> bool:
    if len(raffle.tickets) >= raffle.minimum_required_tickets:
        return True
    return False


def process_raffles():
    raffles = get_raffles_due_for_settlement()
    succesfull_raffles, failed_raffles = split_raffles_by_minimum_tickets(raffles)

    print("\n\nsuccesfull raffles: ", len(succesfull_raffles))
    print("failed raffles: ", len(failed_raffles))


def process_failed_raffles(raffles: list[Raffle]):
    # 1. Set the status in the db to CANCELLED
    # 2. Grab all the tickets for each raffle and set the status to CANCELLED
    # 3. Send back the money to the ticket buyers
    # 4. Notify the raffle creator that the raffle X did not took place
    # 5. Notify the ticket buyer that the raffle X did not took place (refund confirmed)

    return


def process_failed_raffle(raffle: Raffle) -> bool:
    raffle_not_triggered_message = RAFFLE_NOT_TRIGGERED_MESSAGE.format(title=raffle.title)
    raffle_creator: User = raffle.creator

    # 1. Set the status in the db to CANCELLED
    if not set_raffle_status(raffle, RaffleStatus.CANCELLED):
        return False

    # 2. Grab all the tickets for each raffle and set the status to CANCELLED
    if not set_tickets_status(raffle.tickets, TicketStatus.CANCELLED):
        return False

    # 3. Send back the money to the ticket buyers
    if not refund_tickets(raffle.tickets):
        return False

    # 4. Notify the raffle creator that the raffle X did not took place
    return notify_user(raffle_creator, raffle_not_triggered_message)


def process_succesfull_raffles(raffles: list[Raffle]):
    # 1. Set the status in the db to WON
    # 2. Extract a ticket from the raffle tickets - and set that ticket to status = WINNER
    # 3. Set all the other Raffle's tickets to status = LOST
    # 4. Notify the winner ticket user that he won the raffle and he must insert his Shipping details
    # 5. Notify the Raffle creator that the raffle was won
    return


def set_raffle_status(raffle: Raffle, status: RaffleStatus) -> bool:
    raffle.status = status
    try:
        db.session.commit()
        print(f"Raffle status = {status.name}")
        return True
    except Exception as e:
        db.session.rollback()
        print("Unable to change Raffle status:", e)
        return False


def set_tickets_status(tickets: list[Ticket], status: TicketStatus) -> bool:
    for ticket in tickets:
        ticket.status = status

    try:
        db.session.commit()
        print(f"{len(tickets)} ticket(s) status = {status.name}")
        return True
    except Exception as e:
        db.session.rollback()
        print("Unable to change ticket statuses:", e)
        return False


def refund_tickets(tickets: list[Ticket]) -> bool:
    if current_app.config["SIMULATE_PAYMENT"]:
        return True

    for ticket in tickets:
        print(f"Refund ticket {ticket.id} for price {ticket.price}.")
    # TODO: Implement this when the payment mechanism will be implemented
    raise NotImplementedError


def notify_by_email(user: User, message: str) -> bool:
    # TODO: Implement this when an email provider is integrated
    print(f"Sending email to {user.email}: {message}")
    return True


def notify_by_sms(user: User, message: str) -> bool:
    # TODO: Implement this when an SMS provider is integrated
    print(f"Sending SMS to {user.phone}: {message}")
    return True


def notify_by_message(user: User, message: str) -> bool:
    db.session.add(Message(user_id=user.id, body=message))
    try:
        db.session.commit()
        print(f"Message sent to user {user.id}: {message}")
        return True
    except Exception as e:
        db.session.rollback()
        print("Unable to save message:", e)
        return False


def notify_user(user: User, message: str) -> bool:
    email_sent = notify_by_email(user, message)
    sms_sent = notify_by_sms(user, message)
    message_sent = notify_by_message(user, message)
    return email_sent and sms_sent and message_sent


if __name__ == "__main__":
    from app import app

    with app.app_context():
        process_raffles()
