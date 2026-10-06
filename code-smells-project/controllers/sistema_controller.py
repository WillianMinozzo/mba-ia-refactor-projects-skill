import logging

from flask import current_app, jsonify, request

from config.settings import API_VERSION
from models import sistema_model
from models.errors import BancoIndisponivelError
from validators.admin_validator import validar_sql

logger = logging.getLogger(__name__)


def index():
    return jsonify({
        "mensagem": "Bem-vindo à API da Loja",
        "versao": API_VERSION,
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        },
    })


def health_check():
    try:
        contagens = sistema_model.contar_registros()
    except BancoIndisponivelError as err:
        logger.exception("Health check falhou")
        return jsonify({"status": "erro", "detalhes": err.mensagem}), 500
    return jsonify({
        "status": "ok",
        "database": "connected",
        "counts": contagens,
        "versao": API_VERSION,
        "ambiente": current_app.config["APP_ENV"],
    }), 200


def reset_database():
    sistema_model.resetar_banco()
    logger.warning("Banco de dados resetado via /admin/reset-db")
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200


def executar_query():
    linhas = sistema_model.executar_sql(validar_sql(request.get_json(silent=True)))
    if linhas is None:
        return jsonify({"mensagem": "Query executada", "sucesso": True}), 200
    return jsonify({"dados": linhas, "sucesso": True}), 200
