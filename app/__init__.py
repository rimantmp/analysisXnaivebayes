from flask import Flask
from werkzeug.security import generate_password_hash

from app.config import Config
from app.services.database import Database


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    if app.config.get("TESTING") and "MYSQL_ENABLED" not in (test_config or {}):
        app.config["MYSQL_ENABLED"] = False
    if app.config.get("TESTING") and "AUTH_DISABLED" not in (test_config or {}):
        app.config["AUTH_DISABLED"] = True

    database = Database(app.config)
    database.initialize()
    if database.available:
        database.ensure_admin(
            app.config["ADMIN_NAME"],
            app.config["ADMIN_USERNAME"],
            generate_password_hash(app.config["ADMIN_PASSWORD"]),
        )
    app.extensions["database"] = database

    from app.auth import auth
    from app.web import web

    app.register_blueprint(auth)
    app.register_blueprint(web)
    return app
