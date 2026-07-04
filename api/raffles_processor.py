from datetime import date

from sqlalchemy import func

from db import db
from constants.raffle_status import RaffleStatus
from models.raffle_model import Raffle


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


if __name__ == "__main__":
    from app import app

    with app.app_context():
        process_raffles()
