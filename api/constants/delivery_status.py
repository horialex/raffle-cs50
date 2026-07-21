from enum import Enum


class PrizeDeliveryStatus(Enum):
    # Awaiting input
    PENDING_DELIVERY_ADDRESS = "pending_delivery_address"
    PENDING_SENDER_ADDRESS = "pending_sender_address"

    # In transit
    WAITING_FOR_SHIPMENT = "waiting_for_shipment"
    PRIZE_SENT = "prize_sent"
    PRIZE_DELIVERED = "prize_delivered"

    # Finalized
    PRIZE_ACCEPTED = "prize_accepted"
    CONTESTED = "contested"
    DELIVERY_FAILED = "delivery_failed"
    DELIVERY_TIMEOUT = "delivery_timeout"
    PRIZE_REJECTED = "prize_rejected"
