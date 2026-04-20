import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    # Core Flask
    SECRET_KEY = os.getenv("APP_SECRET", "dev-secret-key")

    # SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Uploads
    MAX_FILE_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_MB", 3)) * 1024 * 1024
    MAX_CONTENT_LENGTH = MAX_FILE_UPLOAD_SIZE
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
    MAX_PRODUCTS_PER_RAFFLE = 5
