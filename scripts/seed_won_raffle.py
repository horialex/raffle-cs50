"""Seed a clean "won raffle" starting point for manually testing the prize-delivery flow.

Wipes test_winner's and test_creator's inboxes and prior "TEST -%" raffles, then settles
one single-ticket raffle so it is WON with the delivery at PENDING_DELIVERY_ADDRESS.

Result: exactly 2 messages -> 1 to the winner (with a "Provide delivery address" CTA),
1 to the creator. Log in as test_winner / test_creator (password below).

Run from the repo root:
    python scripts/seed_won_raffle.py
"""

import os
import sys

# Make the app importable regardless of where the script is run from:
# the app is rooted at api/, and app.py also imports the `api` package (repo root).
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [ROOT, os.path.join(ROOT, "api")]

from datetime import datetime, timezone, timedelta
from werkzeug.security import generate_password_hash

from app import app, db
from models.user_model import User
from models.raffle_model import Raffle
from models.product_model import Product
from models.ticket_model import Ticket
from models.message_model import Message
from constants.raffle_status import RaffleStatus
from constants.product_condition import ProductCondition
from jobs.raffles_processor import process_raffles

PASSWORD = "password123"
MARKER_TITLE = "TEST - Won raffle"


def get_or_create(username, email, first, last):
    user = User.query.filter_by(username=username).first()
    if user:
        return user
    user = User(
        first_name=first,
        last_name=last,
        username=username,
        email=email,
        password=generate_password_hash(PASSWORD),
        phone="40712345678",
        country="ro",
        address="Str. Exemplu 1, Cluj",
    )
    db.session.add(user)
    db.session.flush()
    return user


def seed():
    creator = get_or_create(
        "test_creator", "test_creator@example.com", "Test", "Creator"
    )
    winner = get_or_create("test_winner", "test_winner@example.com", "Test", "Winner")

    # clean slate: wipe both test users' inboxes and prior TEST raffles
    Message.query.filter(Message.user_id.in_([creator.id, winner.id])).delete(
        synchronize_session=False
    )
    for old in Raffle.query.filter(
        Raffle.creator_id == creator.id, Raffle.title.like("TEST -%")
    ).all():
        Message.query.filter_by(raffle_id=old.id).delete(synchronize_session=False)
        db.session.delete(old)
    db.session.commit()

    # one ACTIVE raffle due yesterday, single ticket for the winner
    raffle = Raffle(
        creator_id=creator.id,
        title=MARKER_TITLE,
        description="Seeded to test the prize-delivery flow from the start.",
        status=RaffleStatus.ACTIVE,
        ticket_price=10,
        minimum_required_tickets=1,
        maximum_tickets_per_user=5,
        due_date=datetime.now(timezone.utc) - timedelta(days=1),
    )
    db.session.add(raffle)
    db.session.flush()
    db.session.add(
        Product(
            raffle_id=raffle.id,
            name="Test Prize",
            description="A shiny test prize.",
            condition=ProductCondition.NEW,
            estimated_value=100,
            quantity=1,
        )
    )
    db.session.add(Ticket(raffle_id=raffle.id, user_id=winner.id, price=10))
    db.session.commit()
    rid = raffle.id

    # settle -> WON + prize_delivery @ PENDING_DELIVERY_ADDRESS + 2 messages
    process_raffles()

    pd = db.session.get(Raffle, rid).prize_delivery
    win_msgs = Message.query.filter_by(user_id=winner.id).all()
    cre_msgs = Message.query.filter_by(user_id=creator.id).all()

    print("\n================ STATE ================")
    print(f"Raffle {rid} status: {db.session.get(Raffle, rid).status.value}")
    print(f"PrizeDelivery id={pd.id} status={pd.status.value}")
    print(f"test_winner inbox : {len(win_msgs)} message(s)")
    print(f"test_creator inbox: {len(cre_msgs)} message(s)")
    print(f"TOTAL messages: {len(win_msgs) + len(cre_msgs)} (expected 2)")
    print("======================================")
    print(f"Log in as test_winner / test_creator (password: {PASSWORD}).")


if __name__ == "__main__":
    with app.app_context():
        seed()
