"""Composition root: monta config, dados, rotas e middlewares e sobe o servidor."""
import logging

from flask import Flask
from flask_cors import CORS

from config import Settings
from database import init_db
from middlewares.auth import warn_if_admin_routes_open
from middlewares.error_handler import register_error_handlers
from routes import register_routes


def create_app(settings=None):
    settings = settings or Settings()
    app = Flask(__name__)
    app.config.from_object(settings)
    CORS(app, origins=settings.CORS_ORIGINS)
    init_db(app)
    register_routes(app)
    register_error_handlers(app)
    warn_if_admin_routes_open(app)
    return app


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
    app = create_app()
    app.run(debug=app.config['DEBUG'], host=app.config['HOST'], port=app.config['PORT'])
