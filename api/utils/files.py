import os
from flask import current_app


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
