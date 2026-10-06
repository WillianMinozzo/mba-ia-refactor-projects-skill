from flask import jsonify

from models import relatorio_model


def relatorio_vendas():
    return jsonify({"dados": relatorio_model.vendas(), "sucesso": True}), 200
