from flask import Flask
from database import init_db

print("🔥🔥🔥 INIT REAL EJECUTADO 🔥🔥🔥")

def create_app():
    app = Flask(__name__)

    app.secret_key = "superclave123"

    # 🔥 Inicializar DB UNA SOLA VEZ
    with app.app_context():
        try:
            init_db()
            print("✅ Base de datos inicializada correctamente")
        except Exception as e:
            print("❌ ERROR init_db:", e)

    from .routes import main
    app.register_blueprint(main)

    # 🔥 DEBUG CLAVE
    print("🔥 RUTAS REGISTRADAS:")
    print(app.url_map)

    return app