from enum import Enum


class RaffleStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    WON = "won"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    CONTESTED = "contested"
