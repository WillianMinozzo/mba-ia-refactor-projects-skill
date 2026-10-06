"""Guarda das rotas administrativas, ativada quando ADMIN_TOKEN está configurado."""
import logging
from functools import wraps
from hmac import compare_digest

from flask import current_app, jsonify, request

ADMIN_HEADER = 'X-Admin-Token'

logger = logging.getLogger(__name__)


def is_admin_request():
    expected = current_app.config.get('ADMIN_TOKEN')
    if not expected:
        return False
    provided = request.headers.get(ADMIN_HEADER, '')
    return compare_digest(provided.encode(), expected.encode())


def admin_when_configured(view):
    """Sem ADMIN_TOKEN: aberta fora de produção, 403 em produção. Com ADMIN_TOKEN: 401 sem o header."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        if not current_app.config.get('ADMIN_TOKEN'):
            if current_app.config.get('APP_ENV') == 'production':
                return jsonify({'error': 'Rota administrativa desabilitada'}), 403
            return view(*args, **kwargs)
        if not is_admin_request():
            return jsonify({'error': 'Não autorizado'}), 401
        return view(*args, **kwargs)

    return wrapper


def warn_if_admin_routes_open(app):
    if app.config.get('ADMIN_TOKEN'):
        return
    logger.warning(
        'ADMIN_TOKEN not set: /reports/* and DELETE /users/<id> are open (403 if APP_ENV=production); '
        'role assignment via POST/PUT /users is ignored'
    )
