from flask import Flask, render_template, jsonify, request
import sqlite3
import os

# Configuración
DB_NAME = "leaderboard.db"

app = Flask(__name__)

# Inicializar la base de datos si no existe
def init_db():
    if not os.path.exists(DB_NAME):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE test (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            avatar TEXT,
            name TEXT,
            uid TEXT,
            player_id INTEGER,
            game_id INTEGER,
            score INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE TABLE scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uid TEXT NOT NULL,
            player_id INTEGER NOT NULL,
            game_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.commit()
        conn.close()
        print("Base de datos inicializada.")

# Ruta para recibir datos
@app.route('/data', methods=['POST'])
def receive_data():
    # Obtener datos del cuerpo de la solicitud
    data = request.get_json()
    required_keys = {'avatar', 'name', 'UID', 'player_id', 'game_id', 'score'}
    if not data or not required_keys.issubset(data):
        return jsonify({"error": "Datos inválidos. Se requieren avatar, name, UID, player_id, game_id y score."}), 400

    avatar = data['avatar']
    name = data['name']
    uid = data['UID']
    player_id = data['player_id']
    game_id = data['game_id']
    score = data['score']

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO test (avatar, name, uid, player_id, game_id, score)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (avatar, name, uid, player_id, game_id, score))
        conn.commit()
        conn.close()
        return jsonify({"message": "Datos almacenados correctamente"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/submit-score', methods=['POST'])
def submit_score():
    try:
        # Obtener el payload JSON del cuerpo de la solicitud
        data = request.get_json()

        # Extraer datos específicos del payload
        uid = data.get("UID")
        player_id = data.get("ID")
        game_id = data.get("Game")
        score = data.get("Score")

        # Validar los datos
        if not all([uid, player_id, game_id, score]):
            return jsonify({"error": "Payload incompleto"}), 400

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Insertar en la tabla 'scores'
        cursor.execute("""
        INSERT INTO scores (uid, player_id, game_id, score)
        VALUES (?, ?, ?, ?)
        """, (uid, player_id, game_id, score))

        # Obtener el ID del registro recién creado en 'scores'
        score_id = cursor.lastrowid

        # Insertar una nueva fila en 'test' usando datos del payload y score_id
        cursor.execute("""
        INSERT INTO test (avatar, name, uid, player_id, game_id, score)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            f"avatar{score_id}",  # Avatar predeterminado o basado en score_id
            f"Player_{player_id}",  # Nombre predeterminado o basado en player_id
            uid,
            player_id,
            game_id,
            score
        ))

        conn.commit()
        conn.close()

        return jsonify({"message": "Puntaje guardado y registro añadido a test"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Ruta inicial para renderizar el leaderboard
@app.route('/')
def leaderboard_page():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    query = """
        SELECT 
            player_id, 
            MAX(name) AS name, 
            MAX(avatar) AS avatar, 
            SUM(score) as total_score
        FROM test
        GROUP BY player_id
        ORDER BY total_score DESC
        LIMIT 10;
    """
    cursor.execute(query)
    players = cursor.fetchall()
    conn.close()
    return render_template('index.html', players=players)

# Ruta para mostrar detalles de un jugador
@app.route('/player/<int:player_id>')
def player_details(player_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Consulta para obtener el detalle del jugador
    query_player = """
        SELECT 
            MAX(name) AS name, 
            MAX(avatar) AS avatar
        FROM test
        WHERE player_id = ?
    """
    query_scores = """
        SELECT 
            game_id, 
            SUM(score) as total_score
        FROM test
        WHERE player_id = ?
        GROUP BY game_id
    """
    cursor.execute(query_player, (player_id,))
    player = cursor.fetchone()
    cursor.execute(query_scores, (player_id,))
    scores = cursor.fetchall()
    conn.close()

    # Verifica si el jugador existe
    if not player[0]:
        return "Player not found", 404

    return render_template('player_details.html', player=(player_id, player[0], player[1]), scores=scores)

# Ruta para la API del leaderboard
@app.route('/api/leaderboard')
def leaderboard_api():
    # Conexión a la base de datos
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Consulta para calcular el leaderboard
    query = """
        SELECT 
            player_id, 
            MAX(name) AS name, 
            MAX(avatar) AS avatar, 
            SUM(score) as total_score
        FROM test
        GROUP BY player_id
        ORDER BY total_score DESC
        LIMIT 10;
    """
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()

    # Procesar los resultados en un formato JSON
    players = [
        {
            "player_id": row[0],
            "rank": idx + 1,
            "name": row[1] or f"Player {row[0]}",  # Si no hay nombre, usar un identificador genérico
            "avatar": row[2],  # Avatar asociado
            "score": row[3]
        }
        for idx, row in enumerate(results)
    ]

    return jsonify(players)

@app.route('/api/player/<int:player_id>')
def api_player_details(player_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Consulta para obtener el detalle del jugador
    query_player = """
        SELECT 
            MAX(name) AS name, 
            MAX(avatar) AS avatar
        FROM test
        WHERE player_id = ?
    """
    query_scores = """
        SELECT 
            game_id, 
            SUM(score) as total_score
        FROM test
        WHERE player_id = ?
        GROUP BY game_id
    """
    cursor.execute(query_player, (player_id,))
    player = cursor.fetchone()
    cursor.execute(query_scores, (player_id,))
    scores = cursor.fetchall()
    conn.close()

    if not player[0]:
        return jsonify({"error": "Player not found"}), 404

    return jsonify({
        "name": player[0],
        "avatar": player[1],
        "scores": [{"game_id": row[0], "total_score": row[1]} for row in scores]
    })

@app.route('/update_player', methods=['GET', 'POST'])
def update_player():
    if request.method == 'POST':
        player_id = request.form.get('player_id')
        name = request.form.get('name')
        avatar = request.form.get('avatar')

        if not player_id or not name or not avatar:
            return "Missing data. Please provide all fields.", 400

        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            # Validar si el player_id existe en la primera tabla
            cursor.execute("SELECT 1 FROM test WHERE player_id = ?", (player_id,))
            if not cursor.fetchone():
                return "Player ID not found in table 'test'.", 404

            # Validar si el player_id existe en la segunda tabla
            cursor.execute("SELECT 1 FROM users WHERE player_id = ?", (player_id,))
            if not cursor.fetchone():
                return "Player ID not found in table 'player_stats'.", 404

            # Actualizar la primera tabla (test)
            cursor.execute("""
                UPDATE test
                SET name = ?, avatar = ?
                WHERE player_id = ?;
            """, (name, avatar, player_id))

            # Actualizar la segunda tabla (player_stats)
            cursor.execute("""
                UPDATE users
                SET name = ?, avatar = ?
                WHERE player_id = ?;
            """, (name, avatar, player_id))

            # Confirmar los cambios
            conn.commit()
            conn.close()

            return "Player info and stats updated successfully!", 200
        except Exception as e:
            return f"An error occurred: {str(e)}", 500
    else:
        return render_template('update_player.html')

@app.route('/api/latest_user')
def latest_user_api():
    # Conexión a la base de datos
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Consulta para obtener el último usuario basado en timestamp
    query = """
        SELECT 
            id AS player_id, 
            name, 
            avatar, 
            timestamp
        FROM users
        ORDER BY timestamp DESC
        LIMIT 1;
    """
    cursor.execute(query)
    result = cursor.fetchone()
    conn.close()

    # Procesar el resultado en formato JSON
    if result:
        user = {
            "player_id": result[0],
            "name": result[1] or f"Player {result[0]}",  # Si no hay nombre, usar un identificador genérico
            "avatar": result[2],  # Avatar asociado
            "timestamp": result[3]
        }
    else:
        # Si no hay usuarios en la tabla, devolver un valor por defecto
        user = {
            "player_id": None,
            "name": "Anónimo",
            "avatar": None,
            "timestamp": None
        }

    return jsonify(user)

# Ruta para la página que muestra el último usuario
@app.route("/latest_user")
def latest_user_page():
    return render_template("color_game.html")  # Nueva página para mostrar el último usuario

# Inicializar la base de datos al inicio del servidor
if __name__ == '__main__':
    init_db()  # Llama a la función para inicializar la base de datos si es necesario
    app.run(host='0.0.0.0', port=5001)
