from functools import wraps
from hmac import compare_digest

from flask import current_app, jsonify, request


def require_admin(view):
    """Exige o header X-Admin-Token igual a ADMIN_TOKEN; sem token configurado a rota fica desabilitada."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        esperado = current_app.config.get("ADMIN_TOKEN")
        informado = request.headers.get("X-Admin-Token", "")
        if not esperado:
            return jsonify({"erro": "Rota administrativa desabilitada"}), 403
        if not compare_digest(informado.encode(), esperado.encode()):
            return jsonify({"erro": "Não autorizado"}), 401
        return view(*args, **kwargs)

    return wrapper
