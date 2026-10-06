from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    """Liga a sessão do ORM à app (sessão por requisição) e garante o schema."""
    from database.schema import create_schema

    db.init_app(app)
    with app.app_context():
        create_schema()


def commit():
    """Confirma a unidade de trabalho da requisição; desfaz tudo se falhar."""
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
