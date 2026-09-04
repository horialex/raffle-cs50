"""Seed a PENDING prize contestation so the admin review page can be tested by hand.

Settles a single-ticket raffle (so it is WON with a real PrizeDelivery + audit log),
walks the delivery through the happy path to PRIZE_DELIVERED, then contests it exactly
like `contest_prize` does: delivery -> CONTESTED, raffle -> CONTESTED, and a PENDING
PrizeContestation with two evidence images.

Result: one contestation ready to Accept/Reject at /prize-contestations/<id>.
Log in as test_admin to review it (password below).

Run from the repo root:
    python scripts/seed_contested_raffle.py
"""

import os
import shutil
import sys
import uuid

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
from models.prize_contestation_model import PrizeContestation
from models.prize_contestation_image_model import PrizeContestationImage
from constants.raffle_status import RaffleStatus
from constants.product_condition import ProductCondition
from constants.delivery_status import PrizeDeliveryStatus
from constants.contestation_status import ContestationStatus
from constants.contestation_reason import ContestationReason
from services.prize_delivery_service import transition
from jobs.raffles_processor import process_raffles

PASSWORD = "password123"
MARKER_TITLE = "TEST - Contested raffle"

# Walked in order, straight down the happy path of ALLOWED_TRANSITIONS.
PATH_TO_DELIVERED = [
    PrizeDeliveryStatus.PENDING_PICKUP_ADDRESS,
    PrizeDeliveryStatus.WAITING_FOR_SHIPMENT,
    PrizeDeliveryStatus.PRIZE_SENT,
    PrizeDeliveryStatus.PRIZE_DELIVERED,
]


def get_or_create(username, email, first, last, role="user"):
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
        role=role,
    )
    db.session.add(user)
    db.session.flush()
    return user


def seed_evidence_images(contestation_id):
    """Copy whatever images already sit in the upload folder under fresh names.

    Keeps the seeded rows self-contained: deleting them later removes only the copies.
    """
    folder = app.config["PRIZE_CONTESTATION_IMAGES_FOLDER"]
    os.makedirs(folder, exist_ok=True)

    sources = [
        name
        for name in sorted(os.listdir(folder))
        if not name.startswith("seed_")
        and name.lower().endswith((".png", ".jpg", ".jpeg"))
    ][:2]

    for source in sources:
        name = f"seed_{uuid.uuid4().hex}_{source}"
        shutil.copyfile(os.path.join(folder, source), os.path.join(folder, name))
        db.session.add(
            PrizeContestationImage(
                prize_contestation_id=contestation_id, image_url=name
            )
        )
    return len(sources)


def wipe_previous(creator):
    """Drop earlier runs of this seed: the raffle cascade takes the delivery,
    contestation and its image rows with it; message FKs are ON DELETE SET NULL."""
    for old in Raffle.query.filter(
        Raffle.creator_id == creator.id, Raffle.title == MARKER_TITLE
    ).all():
        Message.query.filter_by(raffle_id=old.id).delete(synchronize_session=False)
        for image in (
            old.prize_delivery.contestation.images
            if old.prize_delivery and old.prize_delivery.contestation
            else []
        ):
            path = os.path.join(
                app.config["PRIZE_CONTESTATION_IMAGES_FOLDER"], image.image_url
            )
            if image.image_url.startswith("seed_") and os.path.exists(path):
                os.remove(path)
        db.session.delete(old)
    db.session.commit()


def seed():
    creator = get_or_create(
        "test_creator", "test_creator@example.com", "Test", "Creator"
    )
    winner = get_or_create("test_winner", "test_winner@example.com", "Test", "Winner")
    admin = get_or_create(
        "test_admin", "test_admin@example.com", "Test", "Admin", role="admin"
    )
    db.session.commit()

    wipe_previous(creator)

    # one ACTIVE raffle due yesterday, single ticket for the winner
    raffle = Raffle(
        creator_id=creator.id,
        title=MARKER_TITLE,
        description="Seeded to test the admin contestation review flow.",
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
            name="Vintage Watch",
            description="Seeded prize - a vintage watch, described as mint condition.",
            condition=ProductCondition.NEW,
            estimated_value=450,
            quantity=1,
        )
    )
    db.session.add(Ticket(raffle_id=raffle.id, user_id=winner.id, price=10))
    db.session.commit()
    rid = raffle.id

    # settle -> WON + prize_delivery @ PENDING_DELIVERY_ADDRESS
    process_raffles()

    prize_delivery = db.session.get(Raffle, rid).prize_delivery

    # walk the happy path so the audit log looks like a real delivery
    for status in PATH_TO_DELIVERED:
        if not transition(
            prize_delivery=prize_delivery,
            new_status=status,
            actor_id=None,
            note="Seeded transition.",
        ):
            raise SystemExit(
                f"Could not transition to {status.value} "
                f"from {prize_delivery.status.value} - check ALLOWED_TRANSITIONS."
            )
    db.session.commit()

    # contest it, the way contest_prize does
    if not transition(
        prize_delivery=prize_delivery,
        new_status=PrizeDeliveryStatus.CONTESTED,
        actor_id=winner.id,
        note="The winner user has contested the prize",
    ):
        raise SystemExit("Could not move the delivery to CONTESTED.")

    prize_delivery.raffle.status = RaffleStatus.CONTESTED

    contestation = PrizeContestation(
        prize_delivery_id=prize_delivery.id,
        reason=ContestationReason.WRONG_ITEM,
        description=(
            "The raffle advertised a vintage watch in mint condition, but the box "
            "contained a different model with a scratched glass and no papers. "
            "Photos of what actually arrived are attached."
        ),
        status=ContestationStatus.PENDING,
    )
    db.session.add(contestation)
    db.session.flush()

    image_count = seed_evidence_images(contestation.id)
    db.session.commit()

    print("\n================ STATE ================")
    print(f"Raffle        id={rid} status={db.session.get(Raffle, rid).status.value}")
    print(f"PrizeDelivery id={prize_delivery.id} status={prize_delivery.status.value}")
    print(f"              audit log rows: {len(prize_delivery.logs)}")
    print(f"Contestation  id={contestation.id} status={contestation.status.value}")
    print(f"              reason={contestation.reason.value} images={image_count}")
    print(f"              resolved_by={contestation.resolved_by_user_id} ")
    print(f"              resolved_at={contestation.resolved_at} ")
    print(f"              resolution_note={contestation.resolution_note}")
    print("======================================")
    print(f"Review it at: /prize-contestations/{contestation.id}")
    print(f"          or: /prize-contestations/all")
    print(f"Log in as test_admin (password: {PASSWORD}) - user id {admin.id}.")
    print(f"Winner: test_winner (id {winner.id}) | Creator: test_creator (id {creator.id})")
    print("\nAfter rejecting, expect: contestation=dismissed, delivery=prize_accepted,")
    print("raffle=completed, resolved_by/resolved_at/resolution_note populated,")
    print("plus one new message in each of test_winner's and test_creator's inbox.")


if __name__ == "__main__":
    with app.app_context():
        seed()
