import sqlite3

from database.connection import get_db
from models.errors import BancoIndisponivelError

TABELAS_RESET = ("itens_pedido", "pedidos", "produtos", "usuarios")


def contar_registros():
    try:
        row = get_db().execute(
            """
            SELECT (SELECT COUNT(*) FROM produtos) AS produtos,
                   (SELECT COUNT(*) FROM usuarios) AS usuarios,
                   (SELECT COUNT(*) FROM pedidos) AS pedidos
            """
        ).fetchone()
    except sqlite3.Error as err:
        raise BancoIndisponivelError("Banco de dados indisponível") from err
    return {"produtos": row["produtos"], "usuarios": row["usuarios"], "pedidos": row["pedidos"]}


def resetar_banco():
    db = get_db()
    with db:
        for tabela in TABELAS_RESET:
            db.execute(f"DELETE FROM {tabela}")


def executar_sql(sql):
    """Executa SQL administrativo. Devolve as linhas para SELECT e None para os demais comandos."""
    db = get_db()
    with db:
        cursor = db.execute(sql)
        if sql.strip().upper().startswith("SELECT"):
            return [dict(row) for row in cursor.fetchall()]
    return None
