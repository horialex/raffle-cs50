from enum import Enum


class PrizeDeliveryStatus(Enum):
    PENDING_ADDRESS = "pending_address"
    WAITING_FOR_SHIPMENT = "waiting_for_shipment"
    PRIZE_SENT = "prize_sent"
    PRIZE_DELIVERED = "prize_delivered"
    PRIZE_ACCEPTED = "prize_accepted"
    CONTESTED = "contested"
    DELIVERY_FAILED = "delivery_failed"
