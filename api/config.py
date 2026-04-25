import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    # Core Flask
    SECRET_KEY = os.getenv("APP_SECRET", "dev-secret-key")

    # SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Uploads
    MAX_IMAGE_SIZE = int(os.getenv("MAX_IMAGE_MB", 3)) * 1024 * 1024
    MAX_REQUEST_SIZE = int(os.getenv("MAX_REQUEST_MB", 15)) * 1024 * 1024
    MAX_CONTENT_LENGTH = MAX_REQUEST_SIZE

    # Allowed image types
    ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png"}

    UPLOAD_FOLDER = str(BASE_DIR / "static" / "uploads")
    PROFILE_PICS_FOLDER = str(
        BASE_DIR / "static" / "uploads" / "images" / "profile_pictures"
    )
    PRODUCT_IMAGES_FOLDER = str(BASE_DIR / "static" / "uploads" / "images" / "products")

    # Session
    SESSION_PERMANENT = False
    SESSION_TYPE = "filesystem"

    # Business rules
    MIN_PRODUCTS_PER_RAFFLE = 1
    MAX_PRODUCTS_PER_RAFFLE = 3
    MAX_IMAGES_PER_PRODUCT = 3
