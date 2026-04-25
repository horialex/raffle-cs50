import os
import uuid
from flask import current_app
from werkzeug.utils import secure_filename


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


def save_product_image(product_image_form_data) -> str:
    product_images_folder = current_app.config["PRODUCT_IMAGES_FOLDER"]

    filename = secure_filename(product_image_form_data.filename)
    pic_name = f"product_image_{uuid.uuid1()}_{filename}"
    product_image_form_data.save(os.path.join(product_images_folder, pic_name))

    return pic_name


def get_file_size(file):
    file.stream.seek(0, 2)
    size = file.stream.tell()
    file.stream.seek(0)
    return size


def allowed_file(filename: str) -> bool:
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]
    )
