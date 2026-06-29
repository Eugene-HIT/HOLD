#include <Arduino.h>

#ifdef ESP32
#include <HardwareSerial.h>
HardwareSerial mmWaveSerial(0);
#else
#define mmWaveSerial Serial1
#endif

constexpr uint32_t kDebugBaudRate = 115200;

void setup() {
  Serial.begin(kDebugBaudRate);
  while (!Serial) {
    delay(10);
  }

  mmWaveSerial.begin(kDebugBaudRate);

  Serial.println();
  Serial.println("[system] MR60BHA2 passthrough ready");
  Serial.println("[system] USB serial <-> radar UART bridge enabled");
}

void loop() {
  while (mmWaveSerial.available() > 0) {
    Serial.write(mmWaveSerial.read());
  }

  while (Serial.available() > 0) {
    mmWaveSerial.write(Serial.read());
  }
}