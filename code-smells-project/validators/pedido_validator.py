from models.errors import ValidationError
from models.pedido_model import STATUS_VALIDOS


def _inteiro_positivo(valor):
    return isinstance(valor, int) and not isinstance(valor, bool) and valor > 0


def validar_pedido(dados):
    if not dados or not isinstance(dados, dict):
        raise ValidationError("Dados inválidos")

    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])

    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    if not _inteiro_positivo(usuario_id):
        raise ValidationError("Usuario ID inválido")
    if not itens:
        raise ValidationError("Pedido deve ter pelo menos 1 item")
    if not isinstance(itens, list):
        raise ValidationError("Itens inválidos")
    for item in itens:
        if not (isinstance(item, dict)
                and _inteiro_positivo(item.get("produto_id"))
                and _inteiro_positivo(item.get("quantidade"))):
            raise ValidationError("Item inválido: produto_id e quantidade (inteiro maior que zero) são obrigatórios")

    return {"usuario_id": usuario_id, "itens": itens}


def validar_status(dados):
    dados = dados if isinstance(dados, dict) else {}
    novo_status = dados.get("status", "")
    if not isinstance(novo_status, str) or novo_status not in STATUS_VALIDOS:
        raise ValidationError("Status inválido")
    return novo_status
