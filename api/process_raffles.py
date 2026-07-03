from datetime import date

from sqlalchemy import func

from db import db
from constants.raffle_status import RaffleStatus
from models.raffle_model import Raffle


def get_raffles_due_for_settlement() -> list[Raffle]:
    return (
        db.session.query(Raffle)
        .filter(
            Raffle.status == RaffleStatus.ACTIVE,
            func.date(Raffle.due_date) < date.today(),
        )
        .all()
    )


def has_reached_minimum(raffle: Raffle) -> bool:

    return


def process_raffles():
    raffles = get_raffles_due_for_settlement()
    for raffle in raffles:
        print(raffle.id, raffle.due_date)


if __name__ == "__main__":
    from app import app

    with app.app_context():
        process_raffles()
