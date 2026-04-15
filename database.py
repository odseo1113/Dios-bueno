import sqlite3

# 🔹 Crear base de datos
def init_db():
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()

    # 📩 Tabla de mensajes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero TEXT,
        mensaje TEXT,
        tipo TEXT,
        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 🔐 Tabla de cuentas (login)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cuentas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        tipo TEXT
    )
    """)

    # 📲 Tabla clientes (WHATSAPP → tipo cliente)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero TEXT UNIQUE,
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


# 🔹 Obtener tipo por número (CLAVE 🔥)
def obtener_tipo_por_numero(numero):
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT tipo FROM clientes WHERE numero = ?",
        (numero,)
    )

    resultado = cursor.fetchone()
    conn.close()

    return resultado[0] if resultado else None


# 🔹 Registrar cliente automáticamente
def registrar_cliente(numero, tipo="abogado"):
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO clientes (numero, tipo) VALUES (?, ?)",
            (numero, tipo)
        )
        conn.commit()
    except:
        pass  # ya existe

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


# 🔐 Crear cuenta (login)
def crear_cuenta(username, password, tipo):
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO cuentas (username, password, tipo) VALUES (?, ?, ?)",
        (username, password, tipo)
    )

    conn.commit()
    conn.close()


# 🔐 Validar usuario
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