from flask import Flask
from database import init_db

def create_app():
    app = Flask(__name__)

    app.secret_key = "superclave123"

    # 🔥 SOLO intenta iniciar DB si conexión funciona
    try:
        init_db()
        print("✅ Base de datos inicializada correctamente")
    except Exception as e:
        print("❌ ERROR init_db:", e)

    from .routes import main
    app.register_blueprint(main)

    return app