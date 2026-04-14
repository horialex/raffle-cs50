from datetime import datetime, timezone

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
)

from forms.raffle_form import CreateRaffleForm
from models.raffle_model import Raffle
from db import db


USER_ROLE = "user"
ADMIN_ROLE = "admin"

raffle_bp = Blueprint("raffle_bp", __name__, url_prefix="/raffles")


# -----------------------------------
# Count raffles route - test endpoint
# -----------------------------------
@raffle_bp.route("/count_raffles")
def test():
    raffles = Raffle.query.all()
    return {"count": len(raffles)}


# ----------------------------
# List raffles
# GET /raffles
# ----------------------------
@raffle_bp.route("/", methods=["GET"])
def list_raffles():
    # TODO: Finish this
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 100)

    paginated_raffles = Raffle.query.order_by(Raffle.id).paginate(
        page=page, per_page=per_page, error_out=False
    )

    raffles: Raffle = [
        {
            "id": r.id,
            "creator_id": r.creator_id,
            "title": r.title,
            "description": r.last_name,
            "status": r.status,
            "ticket_price": r.ticket_price,
            "created_date": r.created_at,
            "due_date": r.due_date,
        }
        for r in paginated_raffles.items
    ]

    return render_template(
        "raffles.html",
        raffles=raffles,
        total=paginated_raffles.total,
        page=page,
        per_page=per_page,
    )


# ----------------------------
# Create Raffle
# ----------------------------
@raffle_bp.route("/create", methods=["GET", "POST"])
def create_raffle():
    form = CreateRaffleForm()
    # min_due_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:00")
    # min_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if form.validate_on_submit():
        # hashed_password = generate_password_hash(form.password.data)

        # # Handle form data
        # pic_name = None
        # if form.profile_picture.data:
        #     pic_file = form.profile_picture.data
        #     filename = secure_filename(pic_file.filename)
        #     pic_name = f"{uuid.uuid1()}_{filename}"
        #     pic_file.save(os.path.join(upload_folder, pic_name))

        # user = User(
        #     first_name=form.first_name.data,
        #     last_name=form.last_name.data,
        #     username=form.username.data,
        #     email=form.email.data,
        #     password=hashed_password,
        #     phone=form.phone.data,
        #     country=form.country.data,
        #     address=form.address.data,
        #     profile_picture=pic_name,
        #     last_login_at=datetime.now(timezone.utc),
        # )

        # # ----------------------------
        # # Commit changes
        # # ----------------------------
        # try:
        #     db.session.add(user)
        #     db.session.commit()
        # except Exception as e:
        #     db.session.rollback()
        #     if "Duplicate entry" in str(e):
        #         flash("Username or email already exists", "error")
        #         return render_template("register_user.html", form=form)
        #     else:
        #         flash(f"Error creating user: {str(e)}", "error")
        #         return render_template("register_user.html", form=form)

        # # ----------------------------
        # # Log user in
        # # ----------------------------
        # session["user_id"] = user.id
        # session["username"] = user.username
        # session["first_name"] = user.first_name

        flash("Raffle created.", "success")
        return redirect("/")

    return render_template("create_raffle.html", form=form)
