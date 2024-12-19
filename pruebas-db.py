import requests

# URL del servidor y el endpoint
url = "http://localhost:5001/api/player/2767"  # Cambia el ID del jugador según sea necesario

# Enviar la solicitud GET
response = requests.get(url)

# Verificar el estado de la respuesta
if response.status_code == 200:
    # Imprimir la respuesta en formato JSON
    print(response.json())
else:
    print(f"Error: {response.status_code}")