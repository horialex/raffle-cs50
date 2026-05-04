from flask import current_app

from utils.file_helpers import allowed_file, get_file_size, get_valid_images
from forms.product_form import ProductForm


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
