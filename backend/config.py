import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")


def _bool_env(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def _build_database_uri():
    user = os.environ.get("DB_USER")
    password = quote_plus(os.environ.get("DB_PASSWORD", ""))
    host = os.environ.get("DB_HOST")
    port = os.environ.get("DB_PORT", "3306")
    name = os.environ.get("DB_NAME")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}"


def _build_redis_url():
    host = os.environ.get("REDIS_HOST")
    port = os.environ.get("REDIS_PORT", "6379")
    password = os.environ.get("REDIS_PASSWORD")
    auth = f":{quote_plus(password)}@" if password else ""
    return f"redis://{auth}{host}:{port}/0"


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev")

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or _build_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_TYPE = "redis"
    SESSION_REDIS_URL = os.environ.get("REDIS_URL") or _build_redis_url()
    SESSION_PERMANENT = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("FLASK_ENV") == "production"

    WTF_CSRF_TIME_LIMIT = None

    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
    MAIL_USE_TLS = _bool_env("MAIL_USE_TLS", True)
    GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS")
    GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")

    SOLAPI_API_KEY = os.environ.get("SOLAPI_API_KEY")
    SOLAPI_API_SECRET = os.environ.get("SOLAPI_API_SECRET")
    SOLAPI_SENDER = os.environ.get("SOLAPI_SENDER")
