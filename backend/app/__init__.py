import redis
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_session import Session

db = SQLAlchemy()
migrate = Migrate()


def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")
    app.config["SESSION_REDIS"] = redis.from_url(app.config["SESSION_REDIS_URL"])

    db.init_app(app)
    migrate.init_app(app, db)
    Session(app)

    from . import models
    from .routes import bp
    app.register_blueprint(bp)

    return app
