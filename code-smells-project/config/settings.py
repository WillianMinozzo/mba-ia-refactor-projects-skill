import logging
import os
import secrets

logger = logging.getLogger(__name__)

API_VERSION = "1.0.0"


def _bool(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes")


def _secret(name, app_env):
    value = os.getenv(name)
    if value:
        return value
    if app_env == "production":
        raise RuntimeError(f"{name} must be set in production")
    logger.warning("%s não definida; usando valor efêmero", name)
    return secrets.token_hex(32)


def _origins(value):
    origens = [origem.strip() for origem in value.split(",") if origem.strip()]
    return "*" if not origens or "*" in origens else origens


def load_settings():
    app_env = os.getenv("APP_ENV", "development")
    return {
        "APP_ENV": app_env,
        "SECRET_KEY": _secret("SECRET_KEY", app_env),
        "DEBUG": _bool("DEBUG", False),
        "HOST": os.getenv("HOST", "0.0.0.0"),
        "PORT": int(os.getenv("PORT", "5000")),
        "DATABASE_PATH": os.getenv("DATABASE_PATH", "loja.db"),
        "CORS_ORIGINS": _origins(os.getenv("CORS_ORIGINS", "*")),
        "ADMIN_TOKEN": os.getenv("ADMIN_TOKEN", ""),
    }
