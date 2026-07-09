from datetime import date
import secrets
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

RAFFLE_WON_MESSAGE_WINNER = "Your ticket {ticket_id} has won the raffle {raffle_id} - {title} please provide the shipping details for the raffle creator so he can send you the prize."
RAFFLE_WON_MESSAGE_LOSER = (
    "The tickets you bought for raffle {raffle_id} - {title} are loser tickets"
)
RAFFLE_WON_MESSAGE_CREATOR = "Your raffle {raffle_id} - {title} was won by user {first_name} {last_name} with ticket {ticket_id} please wait for the user to provide the shipping details for the prize"


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
    complete_raffles, failed_raffles = split_raffles_by_minimum_tickets(raffles)

    print("\n\nsuccesfull raffles: ", len(complete_raffles))
    print("failed raffles: ", len(failed_raffles))

    print("\n\n --- Started Processing failed raffles ---")
    # Process the failed raffles
    if not process_failed_raffles(failed_raffles):
        print("Some failed raffles could not be settled - see errors above")

    print("\n\n --- Finished Processing failed raffles ---")

    print("\n\n --- Started Completed failed raffles ---")
    # Process the succesfull raffles
    if not process_complete_raffles(complete_raffles):
        print("Some succesfull raffles could not be settled - see errors above")

    print("\n\n --- Finished Processing Completed raffles ---")


def process_failed_raffles(raffles: list[Raffle]) -> bool:
    for raffle in raffles:
        if not process_failed_raffle(raffle):
            return False
    return True


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
        db.session.rollback()
        return False

    # 2. Grab all the tickets for each raffle and set the status to CANCELLED
    if not set_tickets_status(raffle.tickets, TicketStatus.CANCELLED):
        db.session.rollback()
        return False

    # 3. Send back the money to the ticket buyers
    if not refund_tickets(raffle.tickets):
        db.session.rollback()
        return False

    # 4. Notify the raffle creator that the raffle X did not took place
    if not notify_user_for_raffle(
        raffle_creator, raffle_not_triggered_message_creator, raffle
    ):
        db.session.rollback()
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
            db.session.rollback()
            return False

    # All steps succeeded - commit the raffle/ticket status changes and messages together.
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print("Unable to settle raffle:", e)
        return False

    return True


def process_complete_raffles(raffles: list[Raffle]) -> bool:
    for raffle in raffles:
        if not process_complete_raffle(raffle):
            return False
    return True


def process_complete_raffle(raffle: Raffle) -> bool:
    raffle_creator: User = raffle.creator

    # 1. Set the status in the db to WON
    if not set_raffle_status(raffle, RaffleStatus.WON):
        db.session.rollback()
        return False
    # 2. Extract a ticket from the raffle tickets
    winner_ticket: Ticket = extract_winner_ticket(raffle.tickets)
    winner_user: User = winner_ticket.user

    lost_tickets = [t for t in raffle.tickets if t.id != winner_ticket.id]
    # 3. Set all the other Raffle's tickets to status = LOST - and set that ticket to status = WINNER
    if not set_tickets_status(lost_tickets, TicketStatus.LOST):
        db.session.rollback()
        return False
    winner_ticket.status = TicketStatus.WINNER

    # 4. Notify the winner ticket user that he won the raffle and he must insert his Shipping details
    raffle_won_message_winner = RAFFLE_WON_MESSAGE_WINNER.format(
        ticket_id=winner_ticket.id, raffle_id=raffle.id, title=raffle.title
    )
    if not notify_user_for_ticket(winner_ticket, raffle_won_message_winner):
        db.session.rollback()
        return False

    # 5. Notify the loser tickets
    raffle_won_message_loser = RAFFLE_WON_MESSAGE_LOSER.format(
        raffle_id=raffle.id, title=raffle.title
    )
    loser_users = {}

    for ticket in lost_tickets:
        loser_users[ticket.user_id] = ticket.user

    loser_users = {
        uid: user for uid, user in loser_users.items() if uid != winner_user.id
    }

    for loser in loser_users.values():
        if not notify_user_for_raffle(loser, raffle_won_message_loser, raffle):
            db.session.rollback()
            return False

    # 6. Notify the Raffle creator that the raffle was won
    raffle_won_message_creator = RAFFLE_WON_MESSAGE_CREATOR.format(
        raffle_id=raffle.id,
        title=raffle.title.upper(),
        first_name=winner_user.first_name.upper(),
        last_name=winner_user.last_name.upper(),
        ticket_id=winner_ticket.id,
    )
    if not notify_user_for_raffle(raffle_creator, raffle_won_message_creator, raffle):
        db.session.rollback()
        return False

    # All steps succeeded - commit the raffle/ticket status changes and messages together.
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print("Unable to settle raffle:", e)
        return False

    return True


def set_raffle_status(raffle: Raffle, status: RaffleStatus) -> bool:
    raffle.status = status
    print(f"Raffle status = {status.name}")
    return True


def set_tickets_status(tickets: list[Ticket], status: TicketStatus) -> bool:
    for ticket in tickets:
        ticket.status = status

    print(f"{len(tickets)} ticket(s) status = {status.name}")
    return True


def refund_tickets(tickets: list[Ticket]) -> bool:
    if current_app.config["SIMULATE_PAYMENT"]:
        return True

    for ticket in tickets:
        print(f"Refund ticket {ticket.id} for price {ticket.price}.")
    # TODO: Implement this when the payment mechanism will be implemented
    print("Unable to refund tickets: payment mechanism not implemented")
    return False


def extract_winner_ticket(tickets: list[Ticket]) -> Ticket:
    winner_ticket = secrets.choice(tickets)
    return winner_ticket


if __name__ == "__main__":
    from app import app

    with app.app_context():
        process_raffles()
