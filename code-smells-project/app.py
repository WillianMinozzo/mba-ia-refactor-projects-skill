import logging

from flask import Flask
from flask_cors import CORS

from config.settings import load_settings
from database.connection import close_db, get_db
from database.schema import init_schema
from database.seed import seed_if_empty
from middlewares.error_handler import register_error_handlers
from routes import register_routes

logger = logging.getLogger(__name__)


def create_app(settings=None):
    app = Flask(__name__)
    app.config.from_mapping(settings or load_settings())
    CORS(app, origins=app.config["CORS_ORIGINS"])
    app.teardown_appcontext(close_db)

    with app.app_context():
        db = get_db()
        init_schema(db)
        seed_if_empty(db)

    register_routes(app)
    register_error_handlers(app)
    return app


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    app = create_app()
    logger.info("Servidor iniciado em http://%s:%s", app.config["HOST"], app.config["PORT"])
    app.run(host=app.config["HOST"], port=app.config["PORT"], debug=app.config["DEBUG"])
