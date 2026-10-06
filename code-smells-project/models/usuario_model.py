import hmac

from werkzeug.security import check_password_hash, generate_password_hash

from database.connection import get_db

TIPO_PADRAO = "cliente"
PREFIXOS_HASH = ("scrypt:", "pbkdf2:")

CAMPOS_PUBLICOS = ("id", "nome", "email", "tipo", "criado_em")
CAMPOS_LOGIN = ("id", "nome", "email", "tipo")


def _to_dict(row, campos=CAMPOS_PUBLICOS):
    return {campo: row[campo] for campo in campos}


def listar():
    rows = get_db().execute("SELECT * FROM usuarios").fetchall()
    return [_to_dict(row) for row in rows]


def buscar_por_id(usuario_id):
    row = get_db().execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    return _to_dict(row) if row else None


def criar(nome, email, senha, tipo=TIPO_PADRAO):
    db = get_db()
    with db:
        cursor = db.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            (nome, email, generate_password_hash(senha), tipo),
        )
    return cursor.lastrowid


def autenticar(email, senha):
    rows = get_db().execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchall()
    for row in rows:
        if _senha_confere(row, senha):
            return _to_dict(row, CAMPOS_LOGIN)
    return None


def _senha_confere(row, senha):
    armazenada = row["senha"] or ""
    if armazenada.startswith(PREFIXOS_HASH):
        return check_password_hash(armazenada, senha)
    # senha legada em texto puro (bancos criados antes do hash): confere e regrava com hash
    if not hmac.compare_digest(armazenada.encode(), senha.encode()):
        return False
    db = get_db()
    with db:
        db.execute("UPDATE usuarios SET senha = ? WHERE id = ?", (generate_password_hash(senha), row["id"]))
    return True
