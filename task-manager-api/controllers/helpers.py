from flask import request

from models.errors import ValidationError


def json_body(allow_empty=False):
    """Corpo JSON como dict; 'Dados inválidos' (400) se ausente, não-objeto ou vazio (quando não permitido)."""
    data = request.get_json()
    if not isinstance(data, dict) or (not data and not allow_empty):
        raise ValidationError('Dados inválidos')
    return data


def int_query_arg(name, message):
    value = request.args.get(name, '')
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        raise ValidationError(message)
