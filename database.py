import psycopg2

def conectar():
    import os
    try:
        DATABASE_URL = os.getenv("DATABASE_URL")

        if not DATABASE_URL:
            raise Exception("❌ DATABASE_URL no existe")

        conn = psycopg2.connect(DATABASE_URL)
        print("✅ Conectado a PostgreSQL")
        return conn

    except Exception as e:
        print("❌ ERROR CONEXIÓN DB:", e)
        raise e


# 🔹 LIMPIAR TEXTO
def limpiar(texto):
    if not texto:
        return ""
    return texto.strip().lower()


# 🔥 NORMALIZAR NÚMERO
def normalizar_numero(numero):
    if not numero:
        return ""
    return numero.replace("whatsapp:", "").replace("+", "").replace(" ", "").strip()


# 🔹 INIT DB
def init_db():
    conn = conectar()
    cursor = conn.cursor()

    try:
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

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS cuentas (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            tipo TEXT
        )
        """)

        try:
            cursor.execute("ALTER TABLE cuentas ADD COLUMN numero_cliente TEXT")
        except Exception:
            conn.rollback()
            cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS numeros_twilio (
            id SERIAL PRIMARY KEY,
            numero TEXT UNIQUE,
            en_uso BOOLEAN DEFAULT FALSE
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS citas (
            id SERIAL PRIMARY KEY,
            cliente TEXT,
            negocio TEXT,
            fecha TEXT,
            estado TEXT DEFAULT 'pendiente',
            creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS estados (
            numero TEXT PRIMARY KEY,
            estado TEXT
        )
        """)

        conn.commit()

    except Exception as e:
        conn.rollback()
        print("❌ ERROR init_db:", e)

    finally:
        conn.close()


# 🔹 GUARDAR MENSAJE
def guardar_usuario(numero, mensaje, tipo):
    numero = normalizar_numero(numero)
    tipo = normalizar_numero(tipo)

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO usuarios (numero, mensaje, tipo) VALUES (%s, %s, %s)",
        (numero, mensaje, tipo)
    )

    conn.commit()
    conn.close()


# 🔹 REGISTRAR CLIENTE
def registrar_cliente(numero, tipo):
    numero = normalizar_numero(numero)
    tipo = normalizar_numero(tipo)

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO clientes (numero, tipo)
        VALUES (%s, %s)
        ON CONFLICT (numero)
        DO UPDATE SET tipo = EXCLUDED.tipo
    """, (numero, tipo))

    conn.commit()
    conn.close()


# 🤖 GUARDAR RESPUESTA
def guardar_respuesta(tipo, palabra, respuesta):
    tipo = normalizar_numero(tipo)
    palabra = limpiar(palabra).strip()  # 🔥 FIX

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM respuestas WHERE TRIM(tipo) = TRIM(%s) AND TRIM(palabra) = TRIM(%s)",
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
    conn.close()


# 🤖 RESPUESTA INTELIGENTE (FIX REAL)
def obtener_respuesta(tipo, mensaje):
    tipo = normalizar_numero(tipo)
    mensaje = limpiar(mensaje)

    conn = conectar()
    cursor = conn.cursor()

    # 🔥 FIX CLAVE (evita errores por espacios o formato)
    cursor.execute("""
        SELECT respuesta 
        FROM respuestas 
        WHERE TRIM(tipo) = TRIM(%s) 
        AND LOWER(TRIM(palabra)) = LOWER(TRIM(%s))
        LIMIT 1
    """, (tipo, mensaje))

    resultado = cursor.fetchone()

    if not resultado:
        cursor.execute("""
            SELECT respuesta 
            FROM respuestas 
            WHERE TRIM(tipo) = TRIM(%s) 
            AND %s ILIKE '%%' || palabra || '%%'
            ORDER BY LENGTH(palabra) DESC
            LIMIT 1
        """, (tipo, mensaje))

        resultado = cursor.fetchone()

    conn.close()
    return resultado[0] if resultado else None


# 🔥 CITAS
def guardar_cita(cliente, negocio, fecha):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO citas (cliente, negocio, fecha)
        VALUES (%s, %s, %s)
    """, (cliente, negocio, fecha))

    conn.commit()
    conn.close()


# 🔥 ESTADO
def guardar_estado(numero, estado):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO estados (numero, estado)
        VALUES (%s, %s)
        ON CONFLICT (numero)
        DO UPDATE SET estado = EXCLUDED.estado
    """, (numero, estado))

    conn.commit()
    conn.close()


def obtener_estado(numero):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT estado FROM estados
        WHERE numero = %s
        LIMIT 1
    """, (numero,))

    r = cursor.fetchone()
    conn.close()

    return r[0] if r else None


# 🔹 RESTO
def obtener_respuestas(tipo):
    tipo = normalizar_numero(tipo)
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT palabra, respuesta FROM respuestas WHERE TRIM(tipo) = TRIM(%s)",
        (tipo,)
    )

    datos = cursor.fetchall()
    conn.close()
    return datos


def eliminar_respuesta(tipo, palabra):
    tipo = normalizar_numero(tipo)
    palabra = limpiar(palabra)

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM respuestas WHERE TRIM(tipo) = TRIM(%s) AND TRIM(palabra) = TRIM(%s)",
        (tipo, palabra)
    )

    conn.commit()
    conn.close()


def obtener_numero_disponible():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT numero FROM numeros_twilio
        WHERE en_uso = FALSE
        LIMIT 1
    """)

    resultado = cursor.fetchone()

    if not resultado:
        conn.close()
        return None

    numero = normalizar_numero(resultado[0])

    cursor.execute("""
        UPDATE numeros_twilio
        SET en_uso = TRUE
        WHERE numero = %s
    """, (numero,))

    conn.commit()
    conn.close()

    return numero


def validar_usuario(username, password):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT tipo FROM cuentas
        WHERE username = %s AND password = %s
        LIMIT 1
    """, (username, password))

    r = cursor.fetchone()
    conn.close()

    return r[0] if r else None


def crear_cuenta(username, password, numero_twilio, numero_cliente=None):
    numero_twilio = normalizar_numero(numero_twilio)
    numero_cliente = normalizar_numero(numero_cliente)

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO cuentas (username, password, tipo, numero_cliente)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (username)
        DO UPDATE SET 
            password = EXCLUDED.password,
            tipo = EXCLUDED.tipo,
            numero_cliente = EXCLUDED.numero_cliente
    """, (username, password, numero_twilio, numero_cliente))

    conn.commit()
    conn.close()


def eliminar_cliente(username):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT tipo FROM cuentas
        WHERE username = %s
        LIMIT 1
    """, (username,))

    resultado = cursor.fetchone()

    if not resultado:
        conn.close()
        return False

    numero = normalizar_numero(resultado[0])

    cursor.execute("""
        UPDATE numeros_twilio
        SET en_uso = FALSE
        WHERE numero = %s
    """, (numero,))

    cursor.execute("""
        DELETE FROM cuentas
        WHERE username = %s
    """, (username,))

    conn.commit()
    conn.close()

    return True


def obtener_negocio_por_cliente(numero_cliente):
    numero_cliente = normalizar_numero(numero_cliente)

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT tipo
        FROM cuentas
        WHERE numero_cliente = %s
        LIMIT 1
    """, (numero_cliente,))

    r = cursor.fetchone()
    conn.close()

    return r[0] if r else None



    