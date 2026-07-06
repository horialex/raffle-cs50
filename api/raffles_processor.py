from datetime import date
from flask import current_app
from sqlalchemy import func
from db import db
from models.user_model import User
from constants.ticket_status import TicketStatus
from constants.raffle_status import RaffleStatus
from models.raffle_model import Raffle
from models.ticket_model import Ticket
from notifications import notify_user_for_raffle, notify_user_for_ticket

RAFFLE_NOT_TRIGGERED_MESSAGE_CREATOR = "The raffle {title} did not take place because the minimum required number of tickets was not sold."
RAFFLE_NOT_TRIGGERED_MESSAGE_BUYER = "The raffle {title} did not take place because the minimum required number of tickets was not sold. Your tickets have been refunded."


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
    raffle_not_triggered_message_creator = RAFFLE_NOT_TRIGGERED_MESSAGE_CREATOR.format(
        title=raffle.title
    )
    raffle_not_triggered_message_buyer = RAFFLE_NOT_TRIGGERED_MESSAGE_BUYER.format(
        title=raffle.title
    )
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
    if not notify_user_for_raffle(
        raffle_creator, raffle_not_triggered_message_creator, raffle
    ):
        return False

    # 5. Notify the ticket buyer that the raffle X did not took place (refund confirmed)
    # Create a list of all the individual buyers for this raffle - a set or some sort
    # loop the tickets and add it in the list if it is not already there
    # than for each user - loop that list and notify the uesr for raffle but with the buyer message
    buyers = {}
    for ticket in raffle.tickets:
        buyers[ticket.user_id] = ticket.user

    for buyer in buyers.values():
        if not notify_user_for_raffle(
            buyer, raffle_not_triggered_message_buyer, raffle
        ):
            return False
    return True


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


if __name__ == "__main__":
    from app import app

    with app.app_context():
        process_raffles()
