from enum import Enum


class TicketStatus(Enum):
    PENDING = "pending"
    WINNER = "winner"
    LOST = "lost"
    CANCELLED = "cancelled"
