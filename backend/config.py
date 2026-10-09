import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")


def _env(name, default=None):
    """환경변수 읽기. 값이 비어 있으면("KEY=") 기본값 사용
    (.env.example 을 그대로 복사해 빈 칸이 남아도 서버가 뜨도록, 그리고 docker compose 가
    backend/.env 의 빈 값으로 루트 .env 의 값을 덮어쓰지 않도록)"""
    value = os.environ.get(name)
    if value is None or value.strip() == "":
        return default
    return value


def _bool_env(name, default=False):
    value = _env(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def _build_database_uri():
    user = _env("DB_USER")
    password = quote_plus(_env("DB_PASSWORD", ""))
    host = _env("DB_HOST", "db")
    port = _env("DB_PORT", "3306")
    name = _env("DB_NAME")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}"


def _build_redis_url():
    host = _env("REDIS_HOST", "redis")
    port = _env("REDIS_PORT", "6379")
    password = _env("REDIS_PASSWORD")
    auth = f":{quote_plus(password)}@" if password else ""
    return f"redis://{auth}{host}:{port}/0"


class Config:
    SECRET_KEY = _env("SECRET_KEY", "dev")

    SQLALCHEMY_DATABASE_URI = _env("DATABASE_URL") or _build_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_TYPE = "redis"
    SESSION_REDIS_URL = _env("REDIS_URL") or _build_redis_url()
    SESSION_PERMANENT = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _env("FLASK_ENV") == "production"

    WTF_CSRF_TIME_LIMIT = None

    MAIL_SERVER = _env("MAIL_SERVER")
    MAIL_PORT = int(_env("MAIL_PORT", "587"))
    MAIL_USE_TLS = _bool_env("MAIL_USE_TLS", True)
    GMAIL_ADDRESS = _env("GMAIL_ADDRESS")
    GMAIL_APP_PASSWORD = _env("GMAIL_APP_PASSWORD")

    SOLAPI_API_KEY = _env("SOLAPI_API_KEY")
    SOLAPI_API_SECRET = _env("SOLAPI_API_SECRET")
    SOLAPI_SENDER = _env("SOLAPI_SENDER")
