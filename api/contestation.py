from datetime import datetime, timezone
from typing import List, Set

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from constants.ticket_status import TicketStatus
from models.ticket_model import Ticket
from models.raffle_model import Raffle
from models.prize_delivery_model import PrizeDelivery
from db import db
from jobs.raffles_processor import (
    refund_tickets,
    set_raffle_status,
    set_tickets_status,
    transfer_money,
)
from constants.raffle_status import RaffleStatus
from constants.delivery_status import PrizeDeliveryStatus
from services.prize_delivery_service import transition
from services.courier_service import return_prize
from constants.message_category import MessageCategory
from services.notifications_service import (
    queue_message_for_raffle,
    send_external_notifications,
)
from constants.contestation_status import ContestationStatus
from models.prize_contestation_model import PrizeContestation
from models.user_model import User
from utils.helpers import login_required

prize_contestation_bp = Blueprint(
    "prize_contestation_bp", __name__, url_prefix="/prize-contestations"
)


# ----------------------------
# All prize contestations (admin) - tracking view
# ----------------------------
@prize_contestation_bp.route("/all", methods=["GET"])
@login_required
def all_contestations_admin():
    user: User = User.query.get_or_404(get_current_user_id())
    if not user.is_admin:
        abort(403)

    page = request.args.get("page", 1, type=int)
    page = max(page, 1)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(max(per_page, 1), 20)

    # Sorting
    sort_columns = {
        "status": PrizeContestation.status,
        "reason": PrizeContestation.reason,
        "created": PrizeContestation.created_at,
        "updated": PrizeContestation.updated_at,
    }
    sort = request.args.get("sort", "created")
    if sort not in sort_columns:
        sort = "created"
    direction = request.args.get("dir", "desc")
    if direction not in ("asc", "desc"):
        direction = "desc"

    sort_column = sort_columns[sort]
    order_by = sort_column.asc() if direction == "asc" else sort_column.desc()

    pagination = PrizeContestation.query.order_by(order_by).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template(
        "admin/all_contestations_admin.html",
        contestations=pagination.items,
        pagination=pagination,
        per_page=per_page,
        sort=sort,
        direction=direction,
    )


# ----------------------------
# Contestation details (admin) - TODO: implement full review page
# ----------------------------
@prize_contestation_bp.route("/<int:id>", methods=["GET"])
@login_required
def contestation_details(id):
    user: User = User.query.get_or_404(get_current_user_id())
    if not user.is_admin:
        abort(403)

    contestation: PrizeContestation = PrizeContestation.query.get_or_404(id)

    return render_template(
        "admin/admin_contestation_details.html",
        contestation=contestation,
    )


# ----------------------------
# Reject contestation
# ----------------------------
@prize_contestation_bp.route("/<int:id>/reject", methods=["POST"])
@login_required
def reject_contestation(id):
    admin_user: User = User.query.get_or_404(get_current_user_id())
    if not admin_user.is_admin:
        abort(403)

    contestation: PrizeContestation = PrizeContestation.query.get_or_404(id)
    details_url = url_for(
        "prize_contestation_bp.contestation_details", id=contestation.id
    )

    if contestation.status != ContestationStatus.PENDING:
        flash("This contestation is not PENDING anymore.", "error")
        return redirect(details_url)

    # 1. Change the PrizeDelivery status - the winner keeps the prize
    if not transition(
        prize_delivery=contestation.prize_delivery,
        new_status=PrizeDeliveryStatus.PRIZE_ACCEPTED,
        actor_id=admin_user.id,
        note="The admin rejected the contestation.",
    ):
        db.session.rollback()
        flash("You can't change the status of the prize delivery.", "error")
        return redirect(details_url)

    # 2. Message the ticket winner and the raffle creator
    winner_message = (
        f"The contestation you created for the prize for: "
        f"'{contestation.prize_delivery.raffle.title}' was not accepted. "
        f"We consider the prize is the correct one therefore you have to keep it"
    )
    creator_message = (
        f"The contestation filed by the user who won the prize for: "
        f"'{contestation.prize_delivery.raffle.title}' was not accepted. "
        f"We consider the prize is the correct one therefore they have to keep it. "
        f"You will get the money soon."
    )

    queue_message_for_raffle(
        contestation.prize_delivery.winner,
        winner_message,
        contestation.prize_delivery.raffle,
        contestation.prize_delivery,
        category=MessageCategory.INFO,
    )
    queue_message_for_raffle(
        contestation.prize_delivery.creator,
        creator_message,
        contestation.prize_delivery.raffle,
        contestation.prize_delivery,
        category=MessageCategory.INFO,
    )

    # 3. Resolve the contestation
    contestation.status = ContestationStatus.DISMISSED
    contestation.resolved_by_user_id = admin_user.id
    contestation.resolved_at = datetime.now(timezone.utc)
    contestation.resolution_note = "Contestation dismissed by admin."

    # 4. Change the Raffle status
    contestation.prize_delivery.raffle.status = RaffleStatus.COMPLETED

    # 5. Save the data
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print("Error: ", e)
        flash("Unable to reject the contestation.", "error")
        return redirect(details_url)

    # 6. External side effects: only after the state is durably committed
    if not transfer_money(contestation.prize_delivery.creator):
        flash(
            "Contestation rejected, but the payout could not be arranged yet.",
            "warning",
        )

    send_external_notifications(contestation.prize_delivery.creator, creator_message)
    send_external_notifications(contestation.prize_delivery.winner, winner_message)

    # 7. Flash message and redirect
    flash("Contestation rejected successfully", "success")

    return redirect(details_url)


# ----------------------------
# Accept contestation
# ----------------------------
@prize_contestation_bp.route("/<int:id>/accept", methods=["POST"])
@login_required
def accept_contestation(id):
    admin_user: User = User.query.get_or_404(get_current_user_id())
    if not admin_user.is_admin:
        abort(403)

    contestation: PrizeContestation = PrizeContestation.query.get_or_404(id)
    details_url = url_for(
        "prize_contestation_bp.contestation_details", id=contestation.id
    )

    if contestation.status != ContestationStatus.PENDING:
        flash("This contestation is not PENDING anymore.", "error")
        return redirect(details_url)

    prize_delivery: PrizeDelivery = contestation.prize_delivery
    raffle: Raffle = prize_delivery.raffle
    tickets: List[Ticket] = raffle.tickets
    ticket_owners: Set[User] = set()

    # Status change:
    # 1. Contestation
    contestation.status = ContestationStatus.ACCEPTED
    contestation.resolved_by_user_id = admin_user.id
    contestation.resolved_at = datetime.now(timezone.utc)
    contestation.resolution_note = "Contestation accepted by admin."

    # 2. Prize Delivery
    if not transition(
        prize_delivery=contestation.prize_delivery,
        new_status=PrizeDeliveryStatus.PRIZE_REJECTED,
        actor_id=admin_user.id,
        note="The admin accepted the contestation.",
    ):
        db.session.rollback()
        flash("You can't change the status of the prize delivery.", "error")
        return redirect(details_url)

    # 3. Tickets
    for ticket in tickets:
        ticket_user: User = User.query.get_or_404(ticket.user_id)
        ticket_owners.add(ticket_user)

    if not set_tickets_status(raffle.tickets, TicketStatus.CANCELLED):
        db.session.rollback()
        flash("Unable to cancel the tickets for this raffle.", "error")
        return redirect(details_url)

    # 4. Raffle
    if not set_raffle_status(raffle, RaffleStatus.REJECTED_PRIZE):
        db.session.rollback()
        flash("Unable to change the raffle status.", "error")
        return redirect(details_url)

    # 3. Send back the money to the ticket buyers
    if not refund_tickets(raffle.tickets):
        db.session.rollback()
        flash("Unable to refund the ticket buyers.", "error")
        return redirect(details_url)

    raffle_winner_message = (
        f"The contestation you created for the prize for: "
        f"'{contestation.prize_delivery.raffle.title}' was accepted. "
        f"A courier will arrive at your address to fetch the prize and deliver it back to the raffle creator. "
        f"If you changed your address please contact us at PHONE_NUMBER_PLACEHOLDER"
    )

    raffle_creator_message = (
        f"The contestation filed by the user who won the prize for: "
        f"'{contestation.prize_delivery.raffle.title}' was accepted. "
        f"We consider the prize is NOT the correct one therefore they have to keep it. "
        f"A courier will bring back the prize soon to your address. "
        f"If you changed your address please contact us at PHONE_NUMBER_PLACEHOLDER"
    )

    ticket_refound_notification_message = (
        f"The ticket you bought for Raffle: "
        f"'{contestation.prize_delivery.raffle.title}' was refunded. "
        f"The raffle did not complete successfully, "
        f"therefore a refund was performed. In the next few days the money will be "
        f"back in your bank account."
    )

    queue_message_for_raffle(
        contestation.prize_delivery.winner,
        raffle_winner_message,
        contestation.prize_delivery.raffle,
        contestation.prize_delivery,
        category=MessageCategory.INFO,
    )

    queue_message_for_raffle(
        contestation.prize_delivery.creator,
        raffle_creator_message,
        contestation.prize_delivery.raffle,
        contestation.prize_delivery,
        category=MessageCategory.INFO,
    )

    for ticket_owner in ticket_owners:
        queue_message_for_raffle(
            ticket_owner,
            ticket_refound_notification_message,
            contestation.prize_delivery.raffle,
            contestation.prize_delivery,
            category=MessageCategory.LOSS,
        )

    # 5. Save the data
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print("Error: ", e)
        flash("Unable to accept the contestation.", "error")
        return redirect(details_url)

    # 6. External side effects: only after the state is durably committed
    if not return_prize(prize_delivery):
        flash(
            "Contestation accepted, but the return courier could not be arranged yet.",
            "warning",
        )

    send_external_notifications(
        contestation.prize_delivery.creator, raffle_creator_message
    )

    send_external_notifications(
        contestation.prize_delivery.winner, raffle_winner_message
    )

    for ticket_owner in ticket_owners:
        send_external_notifications(ticket_owner, ticket_refound_notification_message)

    # 7. Flash message and redirect
    flash("Contestation accepted successfully", "success")
    return redirect(details_url)
    # return render_template(
    #     "admin/admin_contestation_details.html",
    #     contestation=contestation,
    # )


def get_current_user_id() -> int:
    return session.get("user_id")
