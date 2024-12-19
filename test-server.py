import sqlite3
import random
from datetime import datetime

# Conexión a la base de datos
conn = sqlite3.connect('diciembre.db')
cursor = conn.cursor()

# Crear la tabla si no existe (puedes omitir esto si ya existe)
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    uid_card_number INTEGER,
    role_id TEXT,
    associated_type INTEGER,
    avatar_id TEXT,
    user_name TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

# Lista de nombres propios para user_name
names = [
    "Alice", "Bob", "Charlie", "Diana", "Edward", "Fiona", "George", "Hannah", 
    "Isabel", "Jack", "Karen", "Liam", "Mia", "Nathan", "Olivia", "Paul", 
    "Quincy", "Rachel", "Samuel", "Tina", "Ursula", "Victor", "Wendy", 
    "Xander", "Yara", "Zane"
]

# Lista de paths de avatar_id
avatars = [f"/static/img/avatar{i}.png" for i in range(1, 10)]

# Insertar 100 registros aleatorios
for i in range(100):
    user_id = random.randint(1000, 9999)  # ID de usuario
    uid_card_number = random.randint(100000, 999999)  # Número de tarjeta UID
    role_id = random.choice(['admin', 'user', 'guest'])  # Rol
    associated_type = random.randint(0, 1)  # Tipo asociado
    avatar_id = random.choice(avatars)  # ID del avatar (path)
    user_name = random.choice(names)  # Nombre de usuario
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Timestamp actual
    
    cursor.execute("""
    INSERT INTO users (user_id, uid_card_number, role_id, associated_type, avatar_id, user_name, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, uid_card_number, role_id, associated_type, avatar_id, user_name, timestamp))

# Confirmar cambios y cerrar conexión
conn.commit()
conn.close()

print("Tabla 'users' llenada con 100 registros aleatorios.")
