#include <DHT.h>

const byte PIN_DHT = 2;
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
  if (isnan(temperatura) || isnan(humedad)) {
    Serial.println("{\"error\":\"No se pudo leer el DHT11\"}");
    return;
  }

  Serial.print("{\"temperatura\":");
  Serial.print(temperatura, 1);
  Serial.print(",\"humedad_ambiente\":");
  Serial.print(humedad, 1);
  Serial.println("}");
}
