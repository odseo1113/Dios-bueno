from flask import Flask

def create_app():
    app = Flask(__name__)

    # 🔐 CLAVE PARA LOGIN (SESIONES)
    app.secret_key = "superclave123"

    from .routes import main
    app.register_blueprint(main)

    return app