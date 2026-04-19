import os


BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Basic Flask config
    # SECRET_KEY = os.getenv("APP_SECRET", "dev-secret-key")
    # SQLALCHEMY_TRACK_MODIFICATIONS = False
    # MAX_CONTENT_LENGTH = int(os.getenv("MAX_UPLOAD_MB", 3)) * 1024 * 1024

    # Upload config
    # UPLOAD_FOLDER = os.path.join(BASE_DIR, "api", "static", "uploads")
    # IMAGES_FOLDER = os.path.join(UPLOAD_FOLDER, "images")

    # PROFILE_PICTURES_FOLDER = os.path.join(IMAGES_FOLDER, "profiles")
    # PRODUCT_IMAGES_FOLDER = os.path.join(IMAGES_FOLDER, "products")

    # Business rules
    MIN_PRODUCTS_PER_RAFFLE = 1
    MAX_PRODUCTS_PER_RAFFLE = 5
