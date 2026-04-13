import sqlite3

conn = sqlite3.connect("usuarios.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM usuarios")
rows = cursor.fetchall()

for row in rows:
    print(row)

conn.close()