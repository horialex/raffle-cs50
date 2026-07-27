from enum import Enum


class ContestationStatus(Enum):
    # Winner has raised the contestation, awaiting admin review
    PENDING = "pending"
    # Admin confirmed the contestation is valid -> delivery becomes PRIZE_REJECTED
    ACCEPTED = "accepted"
    # Admin found the contestation invalid -> delivery becomes PRIZE_ACCEPTED
    DISMISSED = "dismissed"
