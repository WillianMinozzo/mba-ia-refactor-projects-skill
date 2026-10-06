from database.connection import db


def create_schema():
    import models  # noqa: F401  registra as tabelas no metadata

    db.create_all()
