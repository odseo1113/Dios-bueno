import sqlite3

# 🔹 Crear base de datos
def init_db():
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()

    # Tabla mensajes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero TEXT,
        mensaje TEXT,
        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Agregar columna tipo si no existe
    try:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN tipo TEXT DEFAULT 'default'")
    except:
        pass

    # 🔐 Tabla cuentas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cuentas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        tipo TEXT
    )
    """)

    conn.commit()
    conn.close()


# 🔹 Guardar mensaje
def guardar_usuario(numero, mensaje, tipo):
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO usuarios (numero, mensaje, tipo) VALUES (?, ?, ?)",
        (numero, mensaje, tipo)
    )

    conn.commit()
    conn.close()


# 🔹 Obtener todos
def obtener_usuarios():
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM usuarios ORDER BY id DESC")
    rows = cursor.fetchall()

    conn.close()
    return rows


# 🔹 Filtrar por tipo
def obtener_por_tipo(tipo):
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM usuarios WHERE tipo = ? ORDER BY id DESC",
        (tipo,)
    )

    rows = cursor.fetchall()
    conn.close()
    return rows


# 🔹 Contar total
def contar_total():
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM usuarios")
    count = cursor.fetchone()[0]

    conn.close()
    return count


# 🔹 Contar por tipo
def contar_por_tipo(tipo):
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM usuarios WHERE tipo = ?",
        (tipo,)
    )

    count = cursor.fetchone()[0]
    conn.close()
    return count


# 🔹 Crear cuenta
def crear_cuenta(username, password, tipo):
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO cuentas (username, password, tipo) VALUES (?, ?, ?)",
        (username, password, tipo)
    )

    conn.commit()
    conn.close()


# 🔹 Validar usuario
def validar_usuario(username, password):
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM cuentas WHERE username = ? AND password = ?",
        (username, password)
    )

    user = cursor.fetchone()
    conn.close()

    return user