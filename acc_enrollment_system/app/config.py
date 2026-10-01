"""Application configuration."""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:
    """Default configuration shared by development and production."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///" + str(BASE_DIR / "instance" / "acc_enrollment.db"),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Safer session-cookie defaults.
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("COOKIE_SECURE", "0") == "1"

    # Keep forms reasonably small.
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024
