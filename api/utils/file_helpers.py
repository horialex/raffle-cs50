import os
import uuid
from flask import current_app
from werkzeug.utils import secure_filename
from wtforms import ValidationError


def delete_profile_picture(filename):
    if not filename:
        return

    folder = current_app.config["PROFILE_PICS_FOLDER"]
    file_path = os.path.abspath(os.path.join(folder, filename))

    # ensure file is inside the intended folder
    if not file_path.startswith(os.path.abspath(folder)):
        return

    if os.path.exists(file_path):
        os.remove(file_path)


def delete_product_image(filename):
    if not filename:
        return

    print("filename: ", filename)
    folder = current_app.config["PRODUCT_IMAGES_FOLDER"]
    file_path = os.path.abspath(os.path.join(folder, filename))

    # ensure file is inside the intended folder
    if not file_path.startswith(os.path.abspath(folder)):
        return

    if os.path.exists(file_path):
        os.remove(file_path)


def save_product_image(product_image_form_data) -> str:
    product_images_folder = current_app.config["PRODUCT_IMAGES_FOLDER"]

    filename = secure_filename(product_image_form_data.filename)
    pic_name = f"product_image_{uuid.uuid1()}_{filename}"
    product_image_form_data.save(os.path.join(product_images_folder, pic_name))

    return pic_name


def get_valid_images(images):
    valid_images = []
    for img in images:
        if img and img.filename:
            valid_images.append(img)

    return valid_images


def get_file_size(file):
    file.stream.seek(0, 2)
    size = file.stream.tell()
    file.stream.seek(0)
    return size


def validate_file_size(file, max_bytes):
    size = get_file_size(file)
    if size > max_bytes:
        size_mb = size / (1024 * 1024)
        max_mb = max_bytes / (1024 * 1024)

        raise ValidationError(
            f"File too large ({size_mb:.2f} MB). Max allowed is {max_mb:.2f} MB."
        )


def allowed_file(filename: str) -> bool:
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]
    )
