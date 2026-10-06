from database.connection import get_db
from models import produto_model
from models.errors import BusinessRuleError

STATUS_VALIDOS = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]
STATUS_INICIAL = "pendente"
PRODUTO_DESCONHECIDO = "Desconhecido"


def criar(usuario_id, itens):
    """Cria o pedido, seus itens e debita o estoque numa única transação."""
    db = get_db()
    with db:
        produtos = {}
        total = 0
        for item in itens:
            produto = produto_model.buscar_por_id(item["produto_id"])
            if produto is None:
                raise BusinessRuleError(f"Produto {item['produto_id']} não encontrado", com_sucesso=True)
            if produto["estoque"] < item["quantidade"]:
                raise BusinessRuleError("Estoque insuficiente para " + produto["nome"], com_sucesso=True)
            produtos[item["produto_id"]] = produto
            total = total + (produto["preco"] * item["quantidade"])

        pedido_id = db.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
            (usuario_id, STATUS_INICIAL, total),
        ).lastrowid

        for item in itens:
            produto = produtos[item["produto_id"]]
            db.execute(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                (pedido_id, item["produto_id"], item["quantidade"], produto["preco"]),
            )
            if not produto_model.baixar_estoque(item["produto_id"], item["quantidade"]):
                raise BusinessRuleError("Estoque insuficiente para " + produto["nome"], com_sucesso=True)

    return {"pedido_id": pedido_id, "total": total}


def listar(usuario_id=None):
    filtro, params = ("WHERE usuario_id = ?", (usuario_id,)) if usuario_id is not None else ("", ())
    db = get_db()
    pedidos = db.execute(f"SELECT * FROM pedidos {filtro} ORDER BY id", params).fetchall()
    itens = db.execute(
        f"""
        SELECT i.pedido_id, i.produto_id, i.quantidade, i.preco_unitario, p.nome AS produto_nome
        FROM itens_pedido i
        LEFT JOIN produtos p ON p.id = i.produto_id
        WHERE i.pedido_id IN (SELECT id FROM pedidos {filtro})
        ORDER BY i.id
        """,
        params,
    ).fetchall()

    itens_por_pedido = {}
    for item in itens:
        itens_por_pedido.setdefault(item["pedido_id"], []).append({
            "produto_id": item["produto_id"],
            "produto_nome": item["produto_nome"] if item["produto_nome"] is not None else PRODUTO_DESCONHECIDO,
            "quantidade": item["quantidade"],
            "preco_unitario": item["preco_unitario"],
        })

    return [
        {
            "id": pedido["id"],
            "usuario_id": pedido["usuario_id"],
            "status": pedido["status"],
            "total": pedido["total"],
            "criado_em": pedido["criado_em"],
            "itens": itens_por_pedido.get(pedido["id"], []),
        }
        for pedido in pedidos
    ]


def atualizar_status(pedido_id, novo_status):
    db = get_db()
    with db:
        db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
