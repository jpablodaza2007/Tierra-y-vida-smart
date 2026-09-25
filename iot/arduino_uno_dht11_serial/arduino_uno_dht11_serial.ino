#include <DHT.h>

// Cableado: DHT11 en D9 y sensor de humedad de suelo en A0.
const byte PIN_DHT = 9;
const byte PIN_HUMEDAD_SUELO = A0;
const byte TIPO_DHT = DHT11;
const unsigned long INTERVALO_MS = 20000;

DHT dht(PIN_DHT, TIPO_DHT);
unsigned long ultimaLectura = 0;

void setup() {
  Serial.begin(9600);
  dht.begin();
}

void loop() {
  if (millis() - ultimaLectura < INTERVALO_MS) return;
  ultimaLectura = millis();

  float temperatura = dht.readTemperature();
  float humedad = dht.readHumidity();
  int lecturaSuelo = analogRead(PIN_HUMEDAD_SUELO);
  int humedadSuelo = constrain(map(lecturaSuelo, 0, 1023, 100, 0), 0, 100);
  if (isnan(temperatura) || isnan(humedad)) {
    Serial.println("{\"error\":\"No se pudo leer el DHT11\"}");
    return;
  }

  Serial.print("{\"temperatura\":");
  Serial.print(temperatura, 1);
  Serial.print(",\"humedad_ambiente\":");
  Serial.print(humedad, 1);
  Serial.print(",\"humedad_suelo\":");
  Serial.print(humedadSuelo, 1);
  Serial.println("}");
}
