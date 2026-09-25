import redis
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_session import Session
from flask_wtf import CSRFProtect
from flask_wtf.csrf import CSRFError
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)


def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")
    app.config["SESSION_REDIS"] = redis.from_url(app.config["SESSION_REDIS_URL"])
    app.config["RATELIMIT_STORAGE_URI"] = app.config["SESSION_REDIS_URL"]

    db.init_app(app)
    migrate.init_app(app, db)
    Session(app)
    csrf.init_app(app)
    limiter.init_app(app)

    from . import models
    from .routes import bp as main_bp
    from .auth import bp as auth_bp
    from .dashboard import bp as dashboard_bp
    from .enrollments import bp as enrollments_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(enrollments_bp)

    @app.errorhandler(CSRFError)
    def handle_csrf_error(_error):
        return jsonify(error="csrf", message="보안 토큰이 만료되었습니다. 다시 시도하세요."), 400

    return app
