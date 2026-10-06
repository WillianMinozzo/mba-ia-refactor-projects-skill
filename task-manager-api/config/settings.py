"""Configuração da aplicação, lida do ambiente (e de um .env opcional)."""
import logging
import os
import secrets

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def _bool(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in ('1', 'true', 'yes', 'on')


def _list(name, default):
    raw = os.getenv(name)
    if not raw:
        return default
    return [item.strip() for item in raw.split(',') if item.strip()]


def _secret(name, app_env):
    value = os.getenv(name)
    if value:
        return value
    if app_env == 'production':
        raise RuntimeError(f'{name} must be set in production')
    logger.warning('%s not set; using an ephemeral value (issued tokens expire on restart)', name)
    return secrets.token_hex(32)


class Settings:
    """Valores não sensíveis têm o mesmo padrão do comportamento original."""

    def __init__(self):
        self.APP_ENV = os.getenv('APP_ENV', 'development')
        self.SECRET_KEY = _secret('SECRET_KEY', self.APP_ENV)
        self.SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///tasks.db')
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
        self.DEBUG = _bool('DEBUG', False)
        self.HOST = os.getenv('HOST', '0.0.0.0')
        self.PORT = int(os.getenv('PORT', '5000'))
        self.CORS_ORIGINS = _list('CORS_ORIGINS', '*')
        self.ADMIN_TOKEN = os.getenv('ADMIN_TOKEN') or None
