from enum import Enum


class ContestationReason(Enum):
    DAMAGED = "damaged"
    NOT_AS_DESCRIBED = "not_as_described"
    WRONG_ITEM = "wrong_item"
    NOT_RECEIVED = "not_received"
