import sqlite3
import pandas as pd

# Conectar a la base de datos SQLite
conn = sqlite3.connect("test-event.db")

# Función para consultar y mostrar los datos de una tabla
def view_table_data(table_name):
    query = f"SELECT * FROM {table_name}"
    try:
        # Leer los datos en un DataFrame
        df = pd.read_sql_query(query, conn)
        # Mostrar los datos
        print(f"Datos de la tabla {table_name}:")
        print(df)
        return df
    except Exception as e:
        print(f"Error al consultar la tabla {table_name}: {e}")

# Consultar las tablas
participants_df = view_table_data("Participants")
games_df = view_table_data("Games")
scores_df = view_table_data("Scores")
tickets_df = view_table_data("Tickets")

# Cerrar la conexión
conn.close()
