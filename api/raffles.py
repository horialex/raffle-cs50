from datetime import date, datetime, time, timezone

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from models.user_model import User
from utils.file_helpers import (
    delete_product_image,
    get_valid_images,
    save_product_image,
)
from sqlalchemy import or_
from constants.product_condition import ProductCondition
from constants.raffle_status import RaffleStatus
from utils.helpers import is_safe_url, login_required
from forms.raffle_form import CreateRaffleForm, EditRaffleForm
from models.raffle_model import Raffle
from models.product_image_model import ProductImage
from db import db
from models.product_model import Product

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
# Create Raffle
# ----------------------------
@raffle_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_raffle():
    current_user_id = session.get("user_id")
    form = CreateRaffleForm()

    if form.validate_on_submit():
        due_date, error = build_due_date(form)
        if error:
            flash(error, "error")
            return render_template("/raffle/create_raffle.html", form=form)

        # Raffle part
        raffle = Raffle(
            creator_id=current_user_id,
            title=form.title.data,
            description=form.description.data,
            status=RaffleStatus.DRAFT,
            minimum_required_tickets=form.minimum_required_tickets.data,
            maximum_tickets_per_user=form.maximum_tickets_per_user.data,
            ticket_price=form.ticket_price.data,
            due_date=due_date,
        )

        products_to_save = []
        for product_entry in form.products.entries:
            product_data = product_entry.form

            # Create Product entity
            product: Product = Product(
                raffle=raffle,
                name=product_data.name.data,
                description=product_data.description.data,
                estimated_value=product_data.estimated_value.data,
                quantity=product_data.quantity.data,
                condition=ProductCondition[product_data.condition.data],
            )

            # Handle images
            valid_images = get_valid_images(product_data.images.data)

            for image_file in valid_images:
                image_url = save_product_image(image_file)
                product.images.append(ProductImage(image_url=image_url))

            # Append the products
            products_to_save.append(product)

        if not products_to_save:
            flash("Please add at least one product.", "error")
            return render_template("/raffle/create_raffle.html", form=form)

        # Save raffle in the db
        try:
            db.session.add(raffle)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating raffle: {str(e)}", "error")
            return render_template("/raffle/create_raffle.html", form=form)

        flash("Raffle created.", "success")
        return redirect(url_for("raffle_bp.get_raffle", id=raffle.id))

    if form.is_submitted():
        if form.errors:
            flash(
                f"Unable to create raffle - please check the error in the field",
                "error",
            )

    return render_template("/raffle/create_raffle.html", form=form)


# ----------------------------
# Edit Raffle
# ----------------------------
@raffle_bp.route("/update/<int:id>", methods=["GET", "POST"])
@login_required
def update_raffle(id):
    current_user_id = get_current_user_id()
    target_raffle: Raffle = Raffle.query.get_or_404(id)

    if not target_raffle.creator_id == current_user_id:
        abort(403)

    if not target_raffle.status == RaffleStatus.DRAFT:
        flash("The raffle has already started")
        abort(403)

    form = EditRaffleForm(obj=target_raffle)
    form.submit.label.text = "Update raffle"

    # Get next URL
    # Get next from GET or POST
    next_url = request.args.get("next") or request.form.get("next")

    # Fallback if missing or unsafe
    if not next_url or not is_safe_url(next_url):
        next_url = url_for("home")

    if form.validate_on_submit():
        due_date, error = build_due_date(form)
        if error:
            flash(error, "error")
            return render_template("/raffle/update_raffle.html", form=form)

        # ----------------------------
        # Update raffle
        # ----------------------------
        target_raffle.title = form.title.data
        target_raffle.description = form.description.data
        target_raffle.ticket_price = form.ticket_price.data
        target_raffle.minimum_required_tickets = form.minimum_required_tickets.data
        target_raffle.maximum_tickets_per_user = form.maximum_tickets_per_user.data
        target_raffle.due_date = due_date

        # ----------------------------
        # Update products
        # ----------------------------

        # --- DELETE PRODUCT ---
        submitted_ids = set()

        for product_form in form.products:
            product_id = product_form.form.id.data
            if product_id:
                submitted_ids.add(int(product_id))

        # work on a copy of target_raffle.products by using [:]
        for product in target_raffle.products[:]:
            if product.id not in submitted_ids:
                db.session.delete(product)

        # --- UPDATE AND CREATE PRODUCT ---
        for product_form in form.products:
            product_id = product_form.form.id.data

            # --- CREATE NEW PRODUCT ---
            if product_id:
                product = next(
                    (p for p in target_raffle.products if p.id == int(product_id)), None
                )
                if not product:
                    abort(404)
            else:
                product = Product(raffle=target_raffle)
                db.session.add(product)

            # --- UPDATE PRODUCT ---
            product.name = product_form.form.name.data
            product.description = product_form.form.description.data
            product.estimated_value = product_form.form.estimated_value.data
            product.quantity = product_form.form.quantity.data
            product.condition = ProductCondition[product_form.form.condition.data]

            new_valid_images = get_valid_images(product_form.form.images.data)

            # Remove old images
            if new_valid_images:
                for old_image in product.images:
                    db.session.delete(old_image)
                    delete_product_image(old_image.image_url)

                # Save new images
                for image_file in new_valid_images:
                    image_url = save_product_image(image_file)
                    product.images.append(ProductImage(image_url=image_url))

        # Save raffle in the db
        try:
            db.session.add(target_raffle)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating raffle: {str(e)}", "error")
            return render_template(
                "/raffle/update_raffle.html",
                form=form,
                raffle=target_raffle,
                next=next_url,
            )

        flash("Raffle updated.", "success")
        return redirect(url_for("raffle_bp.get_raffle", id=target_raffle.id))

    if form.is_submitted():
        if form.errors:
            flash(
                f"Unable to create raffle - please check the error in the field",
                "error",
            )

    return render_template(
        "/raffle/update_raffle.html", form=form, raffle=target_raffle, next=next_url
    )


# ----------------------------
# Get Raffle details page
# ----------------------------
@raffle_bp.route("/<int:id>", methods=["GET"])
@login_required
def get_raffle(id):
    current_user_id = get_current_user_id()

    user: User = User.query.get_or_404(current_user_id)
    raffle: Raffle = Raffle.query.get_or_404(id)

    is_admin = user.is_admin
    is_owner = raffle.creator_id == current_user_id

    if raffle.is_draft and not (is_admin or is_owner):
        abort(403)

    return render_template("/raffle/raffle_details.html", raffle=raffle)


# ---------------
# Delete Raffle
# ---------------
@raffle_bp.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete_raffle(id):
    current_user_id = get_current_user_id()
    user: User = User.query.get_or_404(current_user_id)
    is_admin = user.is_admin

    raffle: Raffle = Raffle.query.get_or_404(id)

    if raffle.creator_id != current_user_id and not is_admin:
        abort(403)

    if not raffle.is_draft:
        abort(403)

    image_urls = []
    for product in raffle.products:
        for image in product.images:
            image_urls.append(image.image_url)

    try:
        db.session.delete(raffle)
        db.session.commit()

        # Delete images from storage
        for image_url in image_urls:
            delete_product_image(image_url)

    except Exception as e:
        db.session.rollback()
        flash("Unable to delete the raffle", "error")
        return render_template("/raffle/raffle_details.html", raffle=raffle)

    flash("Raffle deleted.", "success")
    return redirect("/")


# ---------------
# Start Raffle
# ---------------
@raffle_bp.route("/start/<int:id>", methods=["POST"])
@login_required
def start_raffle(id):
    current_user_id = get_current_user_id()
    user: User = User.query.get_or_404(current_user_id)
    is_admin = user.is_admin
    raffle: Raffle = Raffle.query.get_or_404(id)
    is_raffle_creator = raffle.creator_id == current_user_id

    if not is_raffle_creator and not is_admin:
        abort(403)

    if not raffle.is_draft:
        abort(403)

    today = date.today()
    raffle_due_date = raffle.due_date.date()

    if raffle_due_date <= today:
        flash(
            "You cannot start a raffle with a due date of today or in the past. Please change your due-date",
            "error",
        )
        return redirect(url_for("raffle_bp.get_raffle", id=raffle.id))

    raffle.status = RaffleStatus.ACTIVE

    try:
        db.session.commit()
        flash("Raffle started", "success")
        return redirect(url_for("raffle_bp.get_raffle", id=raffle.id))
    except Exception as e:
        db.session.rollback()
        flash("Unable to start the raffle", "error")
        return redirect(url_for("raffle_bp.get_raffle", id=raffle.id))


# ---------------
# Get my raffles
# ---------------
@raffle_bp.route("/my-raffles", methods=["GET"])
@login_required
def my_raffles():
    user_id = get_current_user_id()

    # Grab request args
    page = request.args.get("page", 1, type=int)
    page = max(page, 1)
    per_page = request.args.get("per_page", 9, type=int)
    per_page = min(max(per_page, 1), 9)

    sort = request.args.get("sort", "newest")
    search = request.args.get("search", "").strip()

    selected_status = request.args.get("status_filter", "all")
    start_date_filter = request.args.get("start_date", "").strip()
    end_date_filter = request.args.get("end_date", "").strip()
    min_price = request.args.get("min_price", type=int)
    max_price = request.args.get("max_price", type=int)
    category_filter = request.args.get("category")

    # Only show current user's raffles
    query = Raffle.query.filter(Raffle.creator_id == user_id)

    # Filters
    ## Status filter
    allowed_statuses = ["all"] + [status.value for status in RaffleStatus]

    if selected_status not in allowed_statuses:
        selected_status = "all"

    status_filter_options = [
        {"value": status, "label": status.title()} for status in allowed_statuses
    ]

    if selected_status != "all":
        query = query.filter(Raffle.status == selected_status)

    ## Date filter
    start_date = None
    end_date = None

    if start_date_filter:
        try:
            start_date = datetime.strptime(start_date_filter, "%Y-%m-%d")
        except ValueError:
            start_date_filter = ""

    if end_date_filter:
        try:
            end_date = datetime.strptime(end_date_filter, "%Y-%m-%d")
            end_date = datetime.combine(end_date.date(), time.max)
        except ValueError:
            end_date_filter = ""

    if start_date and end_date and start_date > end_date:
        flash("Start date cannot be after end date.", "warning")
        start_date = None
        end_date = None
        start_date_filter = ""
        end_date_filter = ""

    if start_date:
        query = query.filter(Raffle.due_date >= start_date)

    if end_date:
        query = query.filter(Raffle.due_date <= end_date)

    ## Price filter
    if min_price is not None and min_price < 0:
        min_price = None

    if max_price is not None and max_price < 0:
        max_price = None

    if min_price is not None and max_price is not None and min_price > max_price:
        flash("Minimum price cannot be greater than maximum price.", "warning")
        min_price = None
        max_price = None

    if min_price is not None:
        query = query.filter(Raffle.ticket_price >= min_price)

    if max_price is not None:
        query = query.filter(Raffle.ticket_price <= max_price)

    ## Category filter
    # TODO: implement this once categories are added to the raffle products
    if category_filter:
        pass

    # Search
    if search:
        search_pattern = f"%{search}%"

        query = query.filter(
            or_(
                Raffle.title.ilike(search_pattern),
                Raffle.description.ilike(search_pattern),
                Raffle.products.any(
                    or_(
                        Product.name.ilike(search_pattern),
                        Product.description.ilike(search_pattern),
                    )
                ),
            )
        )

    # Sorting - add the sorting options
    # TODO: implement tickets_most, tickets_least, value_high, value_low
    allowed_sorts = [
        "newest",
        "oldest",
        "due_soon",
        "price_low",
        "price_high",
        "tickets_most",
        "tickets_least",
        "value_high",
        "value_low",
    ]

    if sort not in allowed_sorts:
        sort = "newest"

    if sort == "newest":
        query = query.order_by(Raffle.created_at.desc())
    elif sort == "oldest":
        query = query.order_by(Raffle.created_at.asc())
    elif sort == "due_soon":
        query = query.order_by(Raffle.due_date.asc())
    elif sort == "price_low":
        query = query.order_by(Raffle.ticket_price.asc())
    elif sort == "price_high":
        query = query.order_by(Raffle.ticket_price.desc())
    elif sort == "tickets_most":
        pass
    elif sort == "tickets_least":
        pass
    elif sort == "value_high":
        pass
    elif sort == "value_low":
        pass

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    raffles = pagination.items

    return render_template(
        "raffle/my_raffles.html",
        raffles=raffles,
        pagination=pagination,
        selected_status=selected_status,
        selected_sort=sort,
        search=search,
        per_page=per_page,
        start_date=start_date_filter,
        end_date=end_date_filter,
        min_price=min_price,
        max_price=max_price,
        status_filter_options=status_filter_options,
        allowed_sorts=allowed_sorts,
    )


# ----------------------------
# List raffles - Dashboard
# GET /raffles
# ----------------------------
@raffle_bp.route("/", methods=["GET"])
@login_required
def get_raffles():
    user_id = get_current_user_id()
    user: User = User.query.get_or_404(user_id)
    is_admin = user.is_admin

    # Grab request args
    page = request.args.get("page", 1, type=int)
    page = max(page, 1)
    per_page = request.args.get("per_page", 9, type=int)

    per_page = min(max(per_page, 1), 9)

    # Sort and search
    sort = request.args.get("sort", "due_soon")
    search = request.args.get("search", "").strip()

    start_date_filter = request.args.get("start_date", "").strip()
    end_date_filter = request.args.get("end_date", "").strip()
    min_price = request.args.get("min_price", type=int)
    max_price = request.args.get("max_price", type=int)
    category_filter = request.args.get("category")

    # Only show raffles in status: ACTIVE
    query = Raffle.query.filter(Raffle.status == RaffleStatus.ACTIVE)

    # Filters
    ## Date filter
    start_date = None
    end_date = None

    if start_date_filter:
        try:
            start_date = datetime.strptime(start_date_filter, "%Y-%m-%d")
        except ValueError:
            start_date_filter = ""

    if end_date_filter:
        try:
            end_date = datetime.strptime(end_date_filter, "%Y-%m-%d")
            end_date = datetime.combine(end_date.date(), time.max)
        except ValueError:
            end_date_filter = ""

    if start_date and end_date and start_date > end_date:
        flash("Start date cannot be after end date.", "warning")
        start_date = None
        end_date = None
        start_date_filter = ""
        end_date_filter = ""

    if start_date:
        query = query.filter(Raffle.due_date >= start_date)

    if end_date:
        query = query.filter(Raffle.due_date <= end_date)

    ## Price filter
    if min_price is not None and min_price < 0:
        min_price = None

    if max_price is not None and max_price < 0:
        max_price = None

    if min_price is not None and max_price is not None and min_price > max_price:
        flash("Minimum price cannot be greater than maximum price.", "warning")
        min_price = None
        max_price = None

    if min_price is not None:
        query = query.filter(Raffle.ticket_price >= min_price)

    if max_price is not None:
        query = query.filter(Raffle.ticket_price <= max_price)

    ## Category filter
    # TODO: implement this once categories are added to the raffle products
    if category_filter:
        pass

    # Search
    if search:
        search_pattern = f"%{search}%"

        query = query.filter(
            or_(
                Raffle.title.ilike(search_pattern),
                Raffle.description.ilike(search_pattern),
                Raffle.products.any(
                    or_(
                        Product.name.ilike(search_pattern),
                        Product.description.ilike(search_pattern),
                    )
                ),
            )
        )

    # Sorting - add the sorting options
    # TODO: implement tickets_most, tickets_least, value_high, value_low
    allowed_sorts = [
        "newest",
        "oldest",
        "due_soon",
        "price_low",
        "price_high",
        "tickets_most",
        "tickets_least",
        "value_high",
        "value_low",
    ]

    if sort not in allowed_sorts:
        sort = "newest"

    if sort == "newest":
        query = query.order_by(Raffle.created_at.desc())
    elif sort == "oldest":
        query = query.order_by(Raffle.created_at.asc())
    elif sort == "due_soon":
        query = query.order_by(Raffle.due_date.asc())
    elif sort == "price_low":
        query = query.order_by(Raffle.ticket_price.asc())
    elif sort == "price_high":
        query = query.order_by(Raffle.ticket_price.desc())
    elif sort == "tickets_most":
        pass
    elif sort == "tickets_least":
        pass
    elif sort == "value_high":
        pass
    elif sort == "value_low":
        pass

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    raffles = pagination.items

    return render_template(
        "index.html",
        raffles=raffles,
        pagination=pagination,
        selected_sort=sort,
        search=search,
        per_page=per_page,
        start_date=start_date_filter,
        end_date=end_date_filter,
        min_price=min_price,
        max_price=max_price,
        allowed_sorts=allowed_sorts,
    )


# ----------------------------
# Helpers
# ----------------------------
def build_due_date(form):
    due_date = datetime.combine(form.due_date_date.data, datetime.min.time()).replace(
        hour=int(form.due_date_hour.data),
        tzinfo=timezone.utc,  # adjust if needed
    )

    if due_date <= datetime.now(timezone.utc):
        return None, "Due date must be set in the future."

    return due_date, None


def get_current_user(id) -> User:
    return User.query.get_or_404(id)


def get_current_user_id() -> int:
    return session.get("user_id")
