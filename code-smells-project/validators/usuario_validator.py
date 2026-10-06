from models.errors import ValidationError


def _textos(*valores):
    return all(isinstance(valor, str) and valor for valor in valores)


def validar_cadastro(dados):
    if not dados or not isinstance(dados, dict):
        raise ValidationError("Dados inválidos")
    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not _textos(nome, email, senha):
        raise ValidationError("Nome, email e senha são obrigatórios")
    return {"nome": nome, "email": email, "senha": senha}


def validar_login(dados):
    dados = dados if isinstance(dados, dict) else {}
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not _textos(email, senha):
        raise ValidationError("Email e senha são obrigatórios")
    return {"email": email, "senha": senha}
