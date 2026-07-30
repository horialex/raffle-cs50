from flask import Blueprint, abort, render_template, request, session

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
    # TODO: implement this
    user: User = User.query.get_or_404(get_current_user_id())
    if not user.is_admin:
        abort(403)

    contestation: PrizeContestation = PrizeContestation.query.get_or_404(id)

    return render_template(
        "admin/admin_contestation_details.html",
        contestation=contestation,
    )


# ----------------------------
# Accept contestation
# ----------------------------
@prize_contestation_bp.route("/<int:id>/accept", methods=["POST"])
@login_required
def accept_contestation(id):
    # TODO: implement this
    user: User = User.query.get_or_404(get_current_user_id())
    if not user.is_admin:
        abort(403)

    contestation: PrizeContestation = PrizeContestation.query.get_or_404(id)

    return render_template(
        "admin/admin_contestation_details.html",
        contestation=contestation,
    )


def get_current_user_id() -> int:
    return session.get("user_id")
