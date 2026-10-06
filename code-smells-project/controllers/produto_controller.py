import logging

from flask import jsonify, request

from models import produto_model
from validators.produto_validator import validar_filtros_busca, validar_produto

logger = logging.getLogger(__name__)


def listar_produtos():
    produtos = produto_model.listar()
    logger.info("Listando %d produtos", len(produtos))
    return jsonify({"dados": produtos, "sucesso": True}), 200


def buscar_produto(produto_id):
    produto = produto_model.buscar_por_id(produto_id)
    if not produto:
        return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404
    return jsonify({"dados": produto, "sucesso": True}), 200


def buscar_produtos():
    filtros = validar_filtros_busca(request.args)
    resultados = produto_model.buscar(**filtros)
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200


def criar_produto():
    produto = validar_produto(request.get_json(silent=True))
    produto_id = produto_model.criar(**produto)
    logger.info("Produto criado: id=%s", produto_id)
    return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201


def atualizar_produto(produto_id):
    if not produto_model.buscar_por_id(produto_id):
        return jsonify({"erro": "Produto não encontrado"}), 404
    produto = validar_produto(request.get_json(silent=True), regras_de_criacao=False)
    produto_model.atualizar(produto_id, **produto)
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


def deletar_produto(produto_id):
    if not produto_model.buscar_por_id(produto_id):
        return jsonify({"erro": "Produto não encontrado"}), 404
    produto_model.deletar(produto_id)
    logger.info("Produto deletado: id=%s", produto_id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
