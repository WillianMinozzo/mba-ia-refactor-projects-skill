from flask import jsonify, request

from models import pedido_model
from services import pedido_service
from validators.pedido_validator import validar_pedido, validar_status


def criar_pedido():
    pedido = validar_pedido(request.get_json(silent=True))
    resultado = pedido_service.criar_pedido(pedido["usuario_id"], pedido["itens"])
    return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201


def listar_todos_pedidos():
    return jsonify({"dados": pedido_model.listar(), "sucesso": True}), 200


def listar_pedidos_usuario(usuario_id):
    return jsonify({"dados": pedido_model.listar(usuario_id), "sucesso": True}), 200


def atualizar_status_pedido(pedido_id):
    novo_status = validar_status(request.get_json(silent=True))
    pedido_service.atualizar_status(pedido_id, novo_status)
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
