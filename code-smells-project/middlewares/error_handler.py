import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from models.errors import AppError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        corpo = {"erro": err.mensagem}
        if err.com_sucesso:
            corpo["sucesso"] = False
        return jsonify(corpo), err.status

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        if isinstance(err, HTTPException):
            return err
        logger.exception("Erro não tratado")
        return jsonify({"erro": "Erro interno do servidor"}), 500
