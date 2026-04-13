from app import create_app
from database import init_db
import os

app = create_app()

# 🔥 Inicializar base de datos automáticamente
init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # 👈 clave para Render
    app.run(host="0.0.0.0", port=port)