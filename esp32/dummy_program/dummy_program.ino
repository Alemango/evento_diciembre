#include <WiFi.h>
#include <HTTPClient.h>

const char* ssid = "Totalplay-A9CD";           // Nombre de tu red WiFi
const char* password = "A9CD5590s3Dq7DHH"; // Contraseña de tu red WiFi
const char* serverURL = "http://192.168.1.18:5001/data";

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Conectando a WiFi...");
  }

  Serial.print("Conectado a WiFi con IP: ");
  Serial.println(WiFi.localIP());

  // Inicializa el generador de números aleatorios
  randomSeed(analogRead(0));
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverURL);
    http.addHeader("Content-Type", "application/json");

    // Generar valores aleatorios para ID, Game y Score
    int ID = random(1, 201);       // ID entre 1 y 200
    int Game = random(1, 11);      // Game entre 1 y 10
    int Score = random(100, 1000); // Score de 3 dígitos (100 a 999)

    // Crear el payload JSON
    String jsonPayload = "{\"ID\": " + String(ID) + 
                         ", \"Game\": " + String(Game) + 
                         ", \"Score\": " + String(Score) + "}";

    Serial.println("Enviando datos: " + jsonPayload);

    // Intentos para tolerancia a errores
    int attempts = 0;
    const int maxAttempts = 5;
    int httpResponseCode = -1;

    while (attempts < maxAttempts) {
      Serial.print("Intento ");
      Serial.print(attempts + 1);
      Serial.println(" de enviar datos...");

      httpResponseCode = http.POST(jsonPayload);

      if (httpResponseCode > 0) {
        Serial.print("Datos enviados exitosamente. Código de respuesta HTTP: ");
        Serial.println(httpResponseCode);
        break; // Salir del bucle si el envío fue exitoso
      } else {
        Serial.print("Error al enviar datos. Código de error: ");
        Serial.println(httpResponseCode);

        // Diagnóstico adicional
        Serial.print("Estado WiFi: ");
        Serial.println(WiFi.status());

        Serial.print("Memoria libre: ");
        Serial.println(ESP.getFreeHeap());

        attempts++;
        delay(1000); // Esperar antes de reintentar
      }
    }

    if (httpResponseCode <= 0) {
      Serial.println("No se pudo enviar datos tras múltiples intentos.");
    }

    http.end(); // Liberar memoria usada por HTTP
  } else {
    Serial.println("WiFi no está conectado.");
  }

  delay(5000); // Esperar antes del próximo envío
}
