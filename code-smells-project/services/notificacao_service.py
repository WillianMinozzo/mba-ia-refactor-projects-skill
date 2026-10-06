import logging

logger = logging.getLogger(__name__)


def pedido_criado(pedido_id, usuario_id):
    logger.info("Enviando e-mail: pedido %s criado para usuário %s", pedido_id, usuario_id)
    logger.info("Enviando SMS: pedido %s recebido", pedido_id)
    logger.info("Enviando push: novo pedido %s recebido pelo sistema", pedido_id)


def status_alterado(pedido_id, novo_status):
    if novo_status == "aprovado":
        logger.info("Notificação: pedido %s aprovado; preparar envio", pedido_id)
    elif novo_status == "cancelado":
        logger.info("Notificação: pedido %s cancelado; devolver estoque", pedido_id)
