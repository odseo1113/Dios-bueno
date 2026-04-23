import os
import psycopg2


# 🔌 CONEXIÓN POSTGRES (RAILWAY)
def conectar():
    import psycopg2

    print("🚨 ENTRE A CONECTAR")

    DATABASE_URL = "postgresql://postgres:pPdLgVSnWTFoJXIPcZqxxxQDngDlZBfj@shinkansen.proxy.rlwy.net:12209/railway"

    print("🚨 URL:", DATABASE_URL)

    return psycopg2.connect(DATABASE_URL)


# 🔹 LIMPIAR TEXTO
def limpiar(texto):
    if not texto:
        return ""
    return texto.strip().lower()


# 🔹 Crear base de datos (POSTGRES)
def init_db():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id SERIAL PRIMARY KEY,
        numero TEXT,
        mensaje TEXT,
        tipo TEXT,
        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cuentas (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT,
        tipo TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id SERIAL PRIMARY KEY,
        numero TEXT UNIQUE,
        tipo TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS respuestas (
        id SERIAL PRIMARY KEY,
        tipo TEXT,
        palabra TEXT,
        respuesta TEXT
    )
    """)

    conn.commit()
    conn.close()


# 🔹 Guardar mensaje
def guardar_usuario(numero, mensaje, tipo):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO usuarios (numero, mensaje, tipo) VALUES (%s, %s, %s)",
        (numero, mensaje, tipo)
    )

    conn.commit()
    conn.close()


# 🔹 Obtener tipo por número
def obtener_tipo_por_numero(numero):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT tipo FROM clientes WHERE numero = %s",
        (numero,)
    )

    resultado = cursor.fetchone()
    conn.close()

    return resultado[0] if resultado else None


# 🔹 Registrar cliente automáticamente
def registrar_cliente(numero, tipo="abogado"):
    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO clientes (numero, tipo) VALUES (%s, %s) ON CONFLICT (numero) DO NOTHING",
            (numero, tipo)
        )
        conn.commit()
    except:
        pass

    conn.close()


# 🔹 Filtrar por tipo
def obtener_por_tipo(tipo):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM usuarios WHERE tipo = %s ORDER BY id DESC",
        (tipo,)
    )

    rows = cursor.fetchall()
    conn.close()
    return rows


# 🔹 Contar por tipo
def contar_por_tipo(tipo):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM usuarios WHERE tipo = %s",
        (tipo,)
    )

    count = cursor.fetchone()[0]
    conn.close()
    return count


# 🔐 Crear cuenta
def crear_cuenta(username, password, tipo):
    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO cuentas (username, password, tipo) VALUES (%s, %s, %s) ON CONFLICT (username) DO NOTHING",
            (username, password, tipo)
        )
        conn.commit()
    except:
        pass

    conn.close()


# 🔐 Validar usuario
def validar_usuario(username, password):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM cuentas WHERE username = %s AND password = %s",
        (username, password)
    )

    user = cursor.fetchone()
    conn.close()

    return user


# 🤖 Guardar respuesta
def guardar_respuesta(tipo, palabra, respuesta):
    conn = conectar()
    cursor = conn.cursor()

    palabra = limpiar(palabra)
    tipo = limpiar(tipo)

    try:
        cursor.execute(
            "SELECT id FROM respuestas WHERE tipo = %s AND palabra = %s",
            (tipo, palabra)
        )

        existe = cursor.fetchone()

        if existe:
            cursor.execute(
                "UPDATE respuestas SET respuesta = %s WHERE id = %s",
                (respuesta, existe[0])
            )
        else:
            cursor.execute(
                "INSERT INTO respuestas (tipo, palabra, respuesta) VALUES (%s, %s, %s)",
                (tipo, palabra, respuesta)
            )

        conn.commit()

    except Exception as e:
        print("ERROR guardar_respuesta:", e)

    finally:
        conn.close()


# 🤖 Obtener respuesta
def obtener_respuesta(tipo, mensaje):
    conn = conectar()
    cursor = conn.cursor()

    mensaje = limpiar(mensaje)
    tipo = limpiar(tipo)

    cursor.execute(
        """
        SELECT respuesta 
        FROM respuestas 
        WHERE tipo = %s 
        AND palabra = %s
        ORDER BY id DESC
        LIMIT 1
        """,
        (tipo, mensaje)
    )

    resultado = cursor.fetchone()
    conn.close()

    return resultado[0] if resultado else None


# 🤖 Obtener todas
def obtener_respuestas(tipo):
    conn = conectar()
    cursor = conn.cursor()

    tipo = limpiar(tipo)

    cursor.execute(
        "SELECT id, palabra, respuesta FROM respuestas WHERE tipo = %s",
        (tipo,)
    )

    rows = cursor.fetchall()
    conn.close()
    return rows


# 🗑️ Eliminar respuesta
def eliminar_respuesta(id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM respuestas WHERE id = %s",
        (id,)
    )

    conn.commit()
    conn.close()


# 🔥 DEMO
def cargar_respuestas_demo():
    guardar_respuesta("abogado", "hola", "👋 Bienvenido al consultorio jurídico ⚖️\n1️⃣ Servicios\n2️⃣ Precios\n3️⃣ Cita")
    guardar_respuesta("abogado", "1", "⚖️ Derecho laboral, civil, familiar")
    guardar_respuesta("abogado", "2", "💰 Desde $50.000 COP")
    guardar_respuesta("abogado", "3", "📅 Envíanos tus datos para agendar")