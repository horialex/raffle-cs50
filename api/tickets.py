from flask import Blueprint, render_template, request, session
from sqlalchemy import func, or_
from constants.raffle_status import RaffleStatus
from models.product_model import Product
from models.raffle_model import Raffle
from constants.ticket_status import TicketStatus
from models.ticket_model import Ticket
from utils.helpers import login_required

tickets_bp = Blueprint("tickets_bp", __name__, url_prefix="/tickets")


# ----------------------------
# My Tickets
# ----------------------------
@tickets_bp.route("/")
@login_required
def my_tickets():
    current_user_id = session.get("user_id")

    # Per page args
    # Grab request args
    page = request.args.get("page", 1, type=int)
    page = max(page, 1)
    per_page = request.args.get("per_page", 9, type=int)
    per_page = min(max(per_page, 1), 9)

    ## Search - Filters - Sort
    # Search for raffle
    # Filter by Ticket status
    # Sorting options ??
    search = request.args.get("search", "").strip()
    selected_status = request.args.get("status_filter", "all")
    category_filter = request.args.get("category")

    # Only show current user's tickets
    # query = Ticket.query.filter(Ticket.user_id == current_user_id)

    # Global metadata — computed before filters are applied
    user_tickets = Ticket.query.filter(Ticket.user_id == current_user_id)

    tickets_count = user_tickets.count()
    raffles_joined = user_tickets.with_entities(Ticket.raffle_id).distinct().count()
    total_spent = user_tickets.with_entities(func.sum(Ticket.price)).scalar() or 0
    won_tickets = user_tickets.filter(Ticket.status == TicketStatus.WINNER).count()

    metadata = {
        "tickets_count": tickets_count,
        "raffles_joined": raffles_joined,
        "total_spent": total_spent,
        "won_tickets": won_tickets,
    }

    query = Raffle.query.join(Ticket).filter(Ticket.user_id == current_user_id)

    # Filters
    ## Status filter
    allowed_statuses = ["all"] + [s.value for s in RaffleStatus]

    if selected_status not in allowed_statuses:
        selected_status = "all"

    # query = query.join(Ticket.raffle)

    if selected_status != "all":
        query = query.filter(Raffle.status == selected_status)

    ## Category filter
    # TODO: implement this once categories are added to the raffle products
    if category_filter:
        pass

    if search:
        search_escaped = (
            search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        )
        search_pattern = f"%{search_escaped}%"

        query = (
            query.join(Product, Product.raffle_id == Raffle.id)
            .filter(
                or_(
                    Raffle.title.ilike(search_pattern, escape="\\"),
                    Raffle.description.ilike(search_pattern, escape="\\"),
                    Product.name.ilike(search_pattern, escape="\\"),
                    Product.description.ilike(search_pattern, escape="\\"),
                )
            )
            .distinct()
        )

    query = query.order_by(Raffle.due_date.asc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    raffles: list[Raffle] = pagination.items
    # tickets: list[Ticket] = pagination.items

    ## Cards data
    # Total tickets
    # Raffles Joined
    # Total spent
    # Winnings

    ## Sections - by Ticket status
    ## Paginated tickets list

    ## Tickets data:
    # Image
    # Title
    # Tickets count for raffle
    # Prize value
    # Total spent
    # Raffle Status
    # Purchase date
    # Due Date
    # Actions

    print(raffles)

    return render_template(
        "/tickets/my_tickets.html",
        metadata=metadata,
        raffles=raffles,
        pagination=pagination,
        search=search,
        per_page=per_page,
        selected_status=selected_status,
    )
