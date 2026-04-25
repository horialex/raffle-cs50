from datetime import datetime, timezone
import os
import uuid

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
)

from utils.file_helpers import allowed_file, get_file_size, save_product_image
from forms.product_form import ProductForm
from constants.product_condition import ProductCondition
from constants.raffle_status import RaffleStatus
from utils.helpers import login_required
from forms.raffle_form import CreateRaffleForm
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
# List raffles
# GET /raffles
# ----------------------------
@raffle_bp.route("/", methods=["GET"])
@login_required
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
            "description": r.description,
            "status": r.status.value,
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
@login_required
def create_raffle():
    current_user_id = session.get("user_id")
    form = CreateRaffleForm()

    if form.validate_on_submit():
        due_date = datetime.combine(
            form.due_date_date.data, datetime.min.time()
        ).replace(
            hour=int(form.due_date_hour.data),
            tzinfo=timezone.utc,  # adjust if you use another timezone
        )

        if due_date <= datetime.now(timezone.utc):
            flash("Due date must be in the future.", "error")
            return render_template("create_raffle.html", form=form)

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

        # Prize part TODO:
        products_to_save = []
        for index, product_entry in enumerate(form.products.entries, start=1):
            product_data = product_entry.form

            # Skip empty products
            if product_data.active.data != "1":
                continue

            # Product form validation
            error = validate_product_form(product_data, index)
            if error:
                flash(error, "error")
                return render_template("create_raffle.html", form=form)

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
            return render_template("create_raffle.html", form=form)

        # Save raffle in the db
        try:
            db.session.add(raffle)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating raffle: {str(e)}", "error")
            return render_template("create_raffle.html", form=form)

        flash("Raffle created.", "success")
        return redirect("/")

    # if form.is_submitted():
    #     for field, errors in form.errors.items():
    #         for error in errors:
    #             flash(f"{field}: {error}", "error")

    return render_template("create_raffle.html", form=form)


# ----------------------------
# Helpers
# ----------------------------
def validate_product_form(product_form: ProductForm, index) -> str | None:
    max_image_size = current_app.config["MAX_IMAGE_SIZE"]  # bytes

    max_allowed_images = current_app.config["MAX_IMAGES_PER_PRODUCT"]
    name = (product_form.name.data or "").strip()
    description = (product_form.description.data or "").strip()
    estimated_value = product_form.estimated_value.data
    quantity = product_form.quantity.data
    condition = product_form.condition.data
    images = product_form.images.data

    # Validate name
    if not name:
        return f"Product {index}: Name is required."

    if len(name) < 3 or len(name) > 100:
        return f"Product {index}: Name must be between 3 and 100 characters"

    # Validate descr
    if not description:
        return f"Product {index}: Description is required."

    if len(description) < 8 or len(description) > 255:
        return f"Product {index}: Description must be between 8 and 255 characters"

    # Validate estimated_value
    if not estimated_value:
        return f"Product {index}: Estimated value is required."

    if estimated_value < 1 or estimated_value > 100_000:
        return f"Product {index}: Estimated value must be at least 1."

    # Validate quantity
    if not quantity:
        return f"Product {index}: Quantity is required."

    if quantity < 1 or quantity > 99:
        return f"Product {index}: Quantity must be between 1 and 99"

    # Validate condition
    if not condition:
        return f"Product {index}: Condition is required."

    # Validate images
    valid_images = get_valid_images(images)

    if not valid_images:
        return f"Product {index}: At least one image is required."

    if len(valid_images) > max_allowed_images:
        return (
            f"Product {index}: Maximum {max_allowed_images} images per product allowed"
        )

    # Validate image extensions
    for img in valid_images:
        if not allowed_file(img.filename):
            return f"Product {index}: Only JPG, JPEG and PNG images are allowed."

    # Validate image size
    for img in valid_images:
        size = get_file_size(img)

        if size > max_image_size:
            max_mb = max_image_size // (1024 * 1024)
            return f"Product {index}: Each image must be under {max_mb}MB"

    return None


def get_valid_images(images):
    valid_images = []
    for img in images:
        if img and img.filename:
            valid_images.append(img)

    return valid_images
