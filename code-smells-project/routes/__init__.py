from routes.pedido_routes import pedido_bp
from routes.produto_routes import produto_bp
from routes.relatorio_routes import relatorio_bp
from routes.sistema_routes import sistema_bp
from routes.usuario_routes import usuario_bp

BLUEPRINTS = (produto_bp, usuario_bp, pedido_bp, relatorio_bp, sistema_bp)


def register_routes(app):
    for blueprint in BLUEPRINTS:
        app.register_blueprint(blueprint)
