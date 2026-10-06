"""Emissão de token de login assinado (substitui o token previsível 'fake-jwt-token-<id>')."""
from itsdangerous import URLSafeTimedSerializer

TOKEN_SALT = 'auth-token'


def issue_token(user, secret_key):
    return URLSafeTimedSerializer(secret_key, salt=TOKEN_SALT).dumps({'user_id': user.id})
