from flask import Flask
from database import init_db  # 🔥 IMPORTANTE

def create_app():
    app = Flask(__name__)

    # 🔐 CLAVE PARA LOGIN (SESIONES)
    app.secret_key = "superclave123"

    # 🔥 INICIALIZAR BASE DE DATOS
    init_db()

    from database import crear_tabla_respuestas
crear_tabla_respuestas()

    from .routes import main
    app.register_blueprint(main)

    return app