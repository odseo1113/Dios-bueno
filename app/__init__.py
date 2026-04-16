from flask import Flask
from database import init_db  # ✅ SIN punto

def create_app():
    app = Flask(__name__)

    # 🔐 CLAVE PARA LOGIN
    app.secret_key = "superclave123"

    # 🔥 INICIALIZAR DB
    init_db()

    from .routes import main
    app.register_blueprint(main)

    return app