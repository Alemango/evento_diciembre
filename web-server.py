from flask import Flask, render_template, jsonify, request
import sqlite3
import os

# Configuración
DB_NAME = "diciembre.db"

app = Flask(__name__)

# ========================
# Base de Datos
# ========================

# Inicializar la base de datos si no existe
def init_db():
    if not os.path.exists(DB_NAME):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE users (
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

        cursor.execute("""
        CREATE TABLE foods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            food_mark_type INTEGER,
            other_mark_type INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE TABLE game_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            game_id INTEGER,
            score_number INTEGER,
            ticket_amount INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
        CREATE INDEX idx_game_scores_user_id ON game_scores (user_id)
        """)

        cursor.execute("""
        CREATE INDEX idx_game_scores_game_id ON game_scores (game_id)
        """)

        cursor.execute("""
        CREATE TABLE games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id INTEGER,
            game_name TEXT,
            game_description TEXT,
            game_type TEXT,
            ticket_per_score_amount INTEGER,
            max_ticket_amount INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE TABLE exchange (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            ticket_exchange_mark_type INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.commit()
        conn.close()
        print("Base de datos inicializada.")

# ========================
# APIs
# ========================

# Obtener la lista de jugadores
@app.route('/api/player/<int:player_id>')
def api_player_details(player_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Consulta para obtener el detalle del jugador
    query_player = """
        SELECT 
            MAX(user_name) AS name, 
            MAX(avatar_id) AS avatar
        FROM users
        WHERE user_id = ?
    """
    query_scores = """
        SELECT 
            game_id, 
            SUM(score_number) as total_score
        FROM game_scores
        WHERE user_id = ?
        GROUP BY game_id
    """

    query_food = """
        SELECT
            MAX(food_mark_type) AS food_mark_type,
            MAX(other_mark_type) AS other_mark_type
        FROM foods
        WHERE user_id = ?
    """

    cursor.execute(query_player, (player_id,))
    player = cursor.fetchone()
    cursor.execute(query_scores, (player_id,))
    scores = cursor.fetchall()
    cursor.execute(query_food, (player_id,))
    food = cursor.fetchone()
    conn.close()

    if not player[0]:
        return jsonify({"error": "Player not found"}), 404

    return jsonify({
        "name": player[0],
        "avatar": player[1],
        "scores": [{"game_id": row[0], "total_score": row[1]} for row in scores],
        "food": {"food_mark_type": food[0], "other_mark_type": food[1]}
    })

# ========================
# Métodos Generales
# ========================

# Obtener la página para actualizar el nombre y avatar del usuario
@app.route('/update_player', methods=['GET', 'POST'])
def update_player():
    if request.method == 'POST':
        player_id = request.form.get('user_id')
        name = request.form.get('user_name')
        avatar = request.form.get('avatar_id')

        if not player_id or not name or not avatar:
            return jsonify(message="Missing data. Please provide all fields."), 400

        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            # Validar si el player_id existe en la tabla 'users' y obtener el valor de 'associated_type'
            cursor.execute("SELECT associated_type FROM users WHERE user_id = ?", (player_id,))
            result = cursor.fetchone()
            if not result:
                return jsonify(message="Player ID not found in table 'users'."), 404

            associated_type = result[0]
            if associated_type == 1:
                return jsonify(message="Update rejected. Player has associated_type 1."), 403

            # Actualizar la tabla 'users'
            cursor.execute("""
                UPDATE users
                SET user_name = ?, avatar_id = ?, associated_type = 1
                WHERE user_id = ?;
            """, (name, avatar, player_id))

            # Confirmar los cambios
            conn.commit()
            conn.close()

            return jsonify(message="Player info and stats updated successfully!"), 200
        except Exception as e:
            return jsonify(message=f"An error occurred: {str(e)}"), 500
    else:
        return render_template('update_player.html')

# Obtener la página para agregar un nuevo registro de comida
@app.route('/add_food', methods=['GET', 'POST'])
def add_food():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        food_mark_type = request.form.get('food_mark_type')
        other_mark_type = request.form.get('other_mark_type')

        if not user_id or not food_mark_type or not other_mark_type:
            return jsonify(message="Missing data. Please provide all fields."), 400

        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            # Verificar los valores actuales en la base de datos
            cursor.execute("""
                SELECT food_mark_type, other_mark_type
                FROM foods
                WHERE user_id = ?
            """, (user_id,))
            current_values = cursor.fetchone()

            if current_values:
                current_food_mark_type, current_other_mark_type = current_values
                if current_food_mark_type == 1 or current_other_mark_type == 1:
                    return jsonify(message="Invalid data. Current food_mark_type or other_mark_type is 1."), 400

            # Insertar un nuevo registro en la tabla 'foods'
            cursor.execute("""
                UPDATE foods
                SET food_mark_type = ?, other_mark_type = ?
                WHERE user_id = ?;
            """, (food_mark_type, other_mark_type, user_id))

            # Confirmar los cambios
            conn.commit()
            conn.close()

            return jsonify(message="Food added successfully!"), 200
        except Exception as e:
            return jsonify(message=f"An error occurred: {str(e)}"), 500
    else:
        conn = sqlite3.connect('diciembre.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, food_mark_type, other_mark_type
            FROM foods
            WHERE (user_id, timestamp) IN (
                SELECT user_id, MAX(timestamp)
                FROM foods
                GROUP BY user_id
            )""")
        foods = cursor.fetchall()
        conn.close()
        return render_template('add_food.html', foods=foods)

# Ruta para mostrar detalles de un jugador
@app.route('/player/<int:player_id>')
def player_details(player_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Consulta para obtener el detalle del jugador
    query_player = """
        SELECT 
            MAX(user_name) AS name, 
            MAX(avatar_id) AS avatar
        FROM users
        WHERE user_id = ?
    """
    query_scores = """
        SELECT 
            game_id, 
            SUM(score_number) as total_score
        FROM game_scores
        WHERE user_id = ?
        GROUP BY game_id
    """

    query_food = """
        SELECT
            MAX(food_mark_type) AS food_mark_type,
            MAX(other_mark_type) AS other_mark_type
        FROM foods
        WHERE user_id = ?
    """

    cursor.execute(query_player, (player_id,))
    player = cursor.fetchone()
    cursor.execute(query_scores, (player_id,))
    scores = cursor.fetchall()
    cursor.execute(query_food, (player_id,))
    food = cursor.fetchone()
    conn.close()

    # Verifica si el jugador existe
    if not player[0]:
        return "Player not found", 404

    return render_template('player_details.html', player=(player_id, player[0], player[1]), scores=scores, food=food)

# ========================
# Inicialización
# ========================
    
if __name__ == '__main__':
    init_db()  # Llama a la función para inicializar la base de datos si es necesario
    app.run(host='0.0.0.0', port=5001)