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


# TODO: implement this - move this from here to a helper file
def save_product_image(product_image_form_data) -> str:
    product_images_folder = current_app.config["PRODUCT_IMAGES_FOLDER"]

    # pic_file = form.product_data.data
    filename = secure_filename(product_image_form_data.filename)
    pic_name = f"product_image_{uuid.uuid1()}_{filename}"
    product_image_form_data.save(os.path.join(product_images_folder, pic_name))

    return pic_name
