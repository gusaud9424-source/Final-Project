import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_TYPE = "redis"
    SESSION_REDIS_URL = os.environ.get("REDIS_URL")
    SESSION_PERMANENT = False
