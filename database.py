import psycopg2


# 🔌 CONEXIÓN POSTGRES (RAILWAY)
def conectar():
    DATABASE_URL = "postgresql://postgres:pPdLgVSnWTFoJXIPcZqxxxQDngDlZBfj@shinkansen.proxy.rlwy.net:12209/railway"
    return psycopg2.connect(DATABASE_URL)


# 🔹 LIMPIAR TEXTO
def limpiar(texto):
    if not texto:
        return ""
    return texto.strip().lower()


# 🔥 NORMALIZAR NÚMERO (CLAVE)
def normalizar_numero(numero):
    if not numero:
        return ""
    return numero.replace("whatsapp:", "").replace("+", "").replace(" ", "").strip()


# 🔹 INIT DB
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

    # 🔥 TABLA CUENTAS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cuentas (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT,
        tipo TEXT
    )
    """)

    # 🔥 NUEVA COLUMNA (NO ROMPE)
    try:
        cursor.execute("ALTER TABLE cuentas ADD COLUMN numero_cliente TEXT")
    except Exception:
        pass

    # 🔥 NUEVA TABLA: POOL DE NÚMEROS TWILIO
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS numeros_twilio (
        id SERIAL PRIMARY KEY,
        numero TEXT UNIQUE,
        en_uso BOOLEAN DEFAULT FALSE
    )
    """)

    conn.commit()
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
    palabra = limpiar(palabra)

    conn = conectar()
    cursor = conn.cursor()

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
    conn.close()


# 🤖 OBTENER RESPUESTA
def obtener_respuesta(tipo, mensaje):
    tipo = normalizar_numero(tipo)
    mensaje = limpiar(mensaje)

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT respuesta 
        FROM respuestas 
        WHERE tipo = %s AND palabra = %s
        LIMIT 1
    """, (tipo, mensaje))

    resultado = cursor.fetchone()

    if not resultado:
        cursor.execute("""
            SELECT respuesta 
            FROM respuestas 
            WHERE tipo = %s AND %s ILIKE '%%' || palabra || '%%'
            LIMIT 1
        """, (tipo, mensaje))

        resultado = cursor.fetchone()

    conn.close()

    return resultado[0] if resultado else None


# 🔹 OBTENER TODAS LAS RESPUESTAS
def obtener_respuestas(tipo):
    tipo = normalizar_numero(tipo)

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT palabra, respuesta FROM respuestas WHERE tipo = %s",
        (tipo,)
    )

    datos = cursor.fetchall()
    conn.close()

    return datos


# 🔹 ELIMINAR RESPUESTA
def eliminar_respuesta(tipo, palabra):
    tipo = normalizar_numero(tipo)
    palabra = limpiar(palabra)

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM respuestas WHERE tipo = %s AND palabra = %s",
        (tipo, palabra)
    )

    conn.commit()
    conn.close()


# 🔥 DEMO
def cargar_respuestas_demo():
    print("⚠️ cargar_respuestas_demo ejecutado")


# =========================
# 🔥 OBTENER NÚMERO DISPONIBLE (POOL TWILIO)
# =========================
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

    numero = resultado[0]

    cursor.execute("""
        UPDATE numeros_twilio
        SET en_uso = TRUE
        WHERE numero = %s
    """, (numero,))

    conn.commit()
    conn.close()

    return numero


# 🔐 CREAR CUENTA
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


# 🔐 LOGIN
def validar_usuario(username, password):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT tipo FROM cuentas
        WHERE username = %s AND password = %s
        LIMIT 1
    """, (username, password))

    resultado = cursor.fetchone()
    conn.close()

    return resultado[0] if resultado else None


# =========================
# 🔥 POOL DE NÚMEROS TWILIO
# =========================

def obtener_numero_disponible():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, numero FROM numeros_twilio
        WHERE en_uso = FALSE
        LIMIT 1
    """)

    resultado = cursor.fetchone()

    if not resultado:
        conn.close()
        raise Exception("❌ No hay números disponibles")

    id_numero, numero = resultado

    cursor.execute("""
        UPDATE numeros_twilio
        SET en_uso = TRUE
        WHERE id = %s
    """, (id_numero,))

    conn.commit()
    conn.close()

    return numero


def liberar_numero(numero):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE numeros_twilio
        SET en_uso = FALSE
        WHERE numero = %s
    """, (numero,))

    conn.commit()
    conn.close()