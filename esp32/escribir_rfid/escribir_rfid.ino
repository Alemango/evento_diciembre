//Declaración de Librerías
#include <UNIT_PN532.h> 

//Conexiones SPI del ESP32
#define PN532_SCK  (18)
#define PN532_MOSI (23)
#define PN532_SS   (5)
#define PN532_MISO (19)

UNIT_PN532 nfc(PN532_SS);

void setup() {
  Serial.begin(115200);
  nfc.begin();

  nfc.setPassiveActivationRetries(0xFF);

  nfc.SAMConfig();
}

void loop() {
  for (uint16_t i = 1; i <= 10; i++) {
    delay(10000);
    Serial.println("=======================================================");
    Serial.print("Escribiremos la tarjeta:");
    Serial.print(i);
    Serial.println("=======================================================");
    EscribirEstructura(i, 10, 1);
  }

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