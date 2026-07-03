from datetime import date

from flask import session
from sqlalchemy import func

from constants.raffle_status import RaffleStatus
from models.raffle_model import Raffle


def get_raffles_due_for_settlement() -> list[Raffle]:
    results = (
        session.query(Raffle)
        .filter(
            Raffle.status == RaffleStatus.ACTIVE,
            func.date(Raffle.due_date) < date.today(),
        )
        .all()
    )

    return results


raffles = get_raffles_due_for_settlement()

for raffle in raffles:
    print(raffle.id, raffle.due_date)


def has_reached_minimum(raffle: Raffle) -> bool:

    return
