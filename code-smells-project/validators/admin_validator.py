from models.errors import ValidationError


def validar_sql(dados):
    dados = dados if isinstance(dados, dict) else {}
    sql = dados.get("sql", "")
    if not isinstance(sql, str) or not sql:
        raise ValidationError("Query não informada")
    return sql
