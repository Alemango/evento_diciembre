//Declaración de Librerías
#include <UNIT_PN532.h> 
#include <WiFi.h>
#include <HTTPClient.h>

//Conexiones SPI del ESP32
#define PN532_SCK  (18)
#define PN532_MOSI (23)
#define PN532_SS   (5)
#define PN532_MISO (19)

const int pulsadorGPIO = 15;
bool estadoBoton = false;

const char* ssid = "Totalplay-41AF";
const char* password = "41AF7950YZcw2G7X";
const char* serverURL = "http://192.168.100.150:5001/submit-score";

UNIT_PN532 nfc(PN532_SS);

void setup() {
  Serial.begin(115200);
  nfc.begin();

  pinMode(pulsadorGPIO, INPUT);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }

  Serial.print("Conectado a WiFi con IP: ");
  Serial.println(WiFi.localIP());

  //Establezca el número máximo de reintentos para leer de una tarjeta.
  //Esto evita que tengamos que esperar eternamente por una tarjeta,
  //que es el comportamiento predeterminado del PN532.
  nfc.setPassiveActivationRetries(0xFF);

  nfc.SAMConfig();
}

void loop() {
  static uint8_t uidActual[7] = {0};         // UID de la tarjeta actual
  static uint8_t longitudUIDActual = 0;      // Longitud del UID actual
  static boolean tarjetaPresente = false;    // Estado de la tarjeta
  static boolean habilitarEscritura = false; // Indica si se debe realizar escritura
  static uint8_t uidEscritura[7] = {0};      // UID al que se debe escribir
  static uint8_t longitudUIDEscritura = 0;   // Longitud del UID a escribir

  uint8_t uid[7] = {0};                 // UID temporal
  uint8_t longitudUID = 0;              // Longitud temporal del UID

  static int idParticipante = 0;
  static int tickets = 0;
  static int comida = 0;

  // Detección de tarjeta
  if (DetectarTarjeta(uid, &longitudUID)) {
    if (!tarjetaPresente || memcmp(uidActual, uid, longitudUID) != 0 || longitudUIDActual != longitudUID) {
      // Nueva tarjeta detectada
      memcpy(uidActual, uid, longitudUID);
      longitudUIDActual = longitudUID;
      tarjetaPresente = true;

      Serial.println("Nueva tarjeta detectada!");
      Serial.print("UID: ");
      for (uint8_t i = 0; i < longitudUIDActual; i++) {
        Serial.print(" 0x");
        Serial.print(uidActual[i], HEX);
      }
      Serial.println();

      // Leer los datos actuales de la tarjeta
      LeerEstructura(&idParticipante, &tickets, &comida);

      // Si cambia la tarjeta, deshabilitamos cualquier intento de escritura
      habilitarEscritura = false;
    }
  } else {
    if (tarjetaPresente) {
      // La tarjeta fue retirada
      Serial.println("Tarjeta retirada.");
      tarjetaPresente = false;
      habilitarEscritura = false; // Deshabilitar escritura si no hay tarjeta presente
    }
  }

  String UIDStr = ConvertirUIDaString(uid, longitudUID);

  // AQUÍ VA EL JUEGO

  estadoBoton = digitalRead(pulsadorGPIO);

  // Si la tarjeta está presente, procesa comandos desde la consola
  if (estadoBoton == HIGH) {
    // Habilitar escritura en la tarjeta actual
    memcpy(uidEscritura, uidActual, longitudUIDActual);
    longitudUIDEscritura = longitudUIDActual;
    habilitarEscritura = true;
    Serial.println("Escritura habilitada. Acerca la tarjeta para escribir.");
  }

  // Si está habilitada la escritura y el UID coincide, realiza la escritura
  if (habilitarEscritura && 
      memcmp(uidEscritura, uidActual, longitudUIDActual) == 0 &&
      longitudUIDEscritura == longitudUIDActual) {
    EscribirEstructura(idParticipante, 10, comida); // Ejemplo: ID=123, Tickets=10, Comida=1
    Serial.println("Escritura completada.");

    Serial.println("=============================");
    Serial.println(idParticipante);
    Serial.println(tickets);
    Serial.println(comida);
    Serial.println("=============================");

    sendData(UIDStr, idParticipante, tickets, comida);

    habilitarEscritura = false; // Deshabilitar escritura después de completarla
  }

  delay(5000); // Espera antes de intentar detectar nuevamente
}

void EscribirEstructura(uint16_t idParticipante, uint16_t tickets, uint8_t comida) {
  uint8_t uid[7] = {0};        // Búfer para almacenar el UID
  uint8_t longitudUID = 0;     // Longitud del UID
  uint8_t datos[16] = {0};     // Estructura completa a escribir
  uint8_t bloque = 4;          // Bloque donde se almacenarán los datos

  // Intentar leer el UID de la tarjeta
  boolean tarjetaDetectada = nfc.readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, &longitudUID);

  if (tarjetaDetectada) {
    Serial.println("Tarjeta detectada para escritura!");
    Serial.print("UID: ");
    for (uint8_t i = 0; i < longitudUID; i++) {
      Serial.print(" 0x");
      Serial.print(uid[i], HEX);
      if (i < 4) datos[i] = uid[i]; // Copiar los primeros 4 bytes del UID a la estructura
    }
    Serial.println();

    // Agregar el ID del participante
    datos[4] = (idParticipante >> 8) & 0xFF; // Byte alto
    datos[5] = idParticipante & 0xFF;        // Byte bajo

    // Agregar los tickets
    datos[6] = (tickets >> 8) & 0xFF; // Byte alto
    datos[7] = tickets & 0xFF;        // Byte bajo

    // Agregar el valor de la comida
    datos[8] = comida;

    // Autenticar y escribir en el bloque
    uint8_t clave[] = { 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF }; // Clave predeterminada
    if (nfc.mifareclassic_AuthenticateBlock(uid, longitudUID, bloque, 0, clave)) {
      Serial.println("Autenticación exitosa! Escribiendo datos...");
      if (nfc.mifareclassic_WriteDataBlock(bloque, datos)) {
        Serial.println("Datos escritos correctamente!");
      } else {
        Serial.println("Error al escribir en el bloque.");
      }
    } else {
      Serial.println("Error en la autenticación del bloque.");
    }
  } else {
    Serial.println("No se detectó ninguna tarjeta.");
  }
}

void LeerEstructura(int* idParticipante, int* tickets, int* comida) {
  uint8_t uid[7] = {0};        // Búfer para almacenar el UID
  uint8_t longitudUID = 0;     // Longitud del UID
  uint8_t datos[16] = {0};     // Búfer para almacenar datos del bloque
  uint8_t bloque = 4;          // Bloque donde se encuentran los datos

  // Intentar leer el UID de la tarjeta
  boolean tarjetaDetectada = nfc.readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, &longitudUID);

  if (tarjetaDetectada) {
    Serial.println("Tarjeta detectada para lectura!");
    Serial.print("UID: ");
    for (uint8_t i = 0; i < longitudUID; i++) {
      Serial.print(" 0x");
      Serial.print(uid[i], HEX);
    }
    Serial.println();

    // Autenticar y leer el bloque
    uint8_t clave[] = { 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF }; // Clave predeterminada
    if (nfc.mifareclassic_AuthenticateBlock(uid, longitudUID, bloque, 0, clave)) {
      Serial.println("Autenticación exitosa! Leyendo datos...");
      if (nfc.mifareclassic_ReadDataBlock(bloque, datos)) {
        Serial.println("Datos leídos:");
        
        // Mostrar UID
        Serial.print("UID: ");
        for (int i = 0; i < 4; i++) {
          Serial.print(" 0x");
          Serial.print(datos[i], HEX);
        }
        Serial.println();

        // Extraer ID, tickets y comida
        *idParticipante = (datos[4] << 8) | datos[5];
        *tickets = (datos[6] << 8) | datos[7];
        *comida = datos[8];

      } else {
        Serial.println("Error al leer datos del bloque.");
      }
    } else {
      Serial.println("Error en la autenticación del bloque.");
    }
  } else {
    Serial.println("No se detectó ninguna tarjeta.");
  }
}

boolean DetectarTarjeta(uint8_t* uid, uint8_t* longitudUID) {
  return nfc.readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, longitudUID);
}

void sendData(String UID, int ID, int Game, int Score) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverURL);
    http.addHeader("Content-Type", "application/json");

    // Crear el payload JSON
    String jsonPayload = "{\"UID\": \"" + UID + 
                         "\", \"ID\": " + String(ID) + 
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
}

String ConvertirUIDaString(uint8_t* uid, uint8_t longitudUID) {
  String uidString = ""; // Inicializar un String vacío

  for (uint8_t i = 0; i < longitudUID; i++) {
    if (uid[i] < 0x10) {
      uidString += "0"; // Agregar un cero inicial si el byte es menor a 0x10
    }
    uidString += String(uid[i], HEX); // Convertir el byte a hexadecimal y concatenarlo
  }

  return uidString;
}
