import logging

from flask import jsonify, request

from models import usuario_model
from validators.usuario_validator import validar_cadastro, validar_login

logger = logging.getLogger(__name__)


def listar_usuarios():
    return jsonify({"dados": usuario_model.listar(), "sucesso": True}), 200


def buscar_usuario(usuario_id):
    usuario = usuario_model.buscar_por_id(usuario_id)
    if not usuario:
        return jsonify({"erro": "Usuário não encontrado"}), 404
    return jsonify({"dados": usuario, "sucesso": True}), 200


def criar_usuario():
    # o tipo nunca vem do cliente: todo cadastro público é "cliente"
    usuario_id = usuario_model.criar(**validar_cadastro(request.get_json(silent=True)))
    logger.info("Usuário criado: id=%s", usuario_id)
    return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201


def login():
    credenciais = validar_login(request.get_json(silent=True))
    usuario = usuario_model.autenticar(credenciais["email"], credenciais["senha"])
    if not usuario:
        logger.info("Login recusado")
        return jsonify({"erro": "Email ou senha inválidos", "sucesso": False}), 401
    logger.info("Login bem-sucedido: usuario_id=%s", usuario["id"])
    return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
