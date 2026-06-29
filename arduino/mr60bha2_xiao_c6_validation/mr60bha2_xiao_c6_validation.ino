#include <Arduino.h>
#include "Seeed_Arduino_mmWave.h"

#ifdef ESP32
#include <HardwareSerial.h>
HardwareSerial mmWaveSerial(0);
#else
#define mmWaveSerial Serial1
#endif

namespace {

constexpr uint32_t kDebugBaudRate = 115200;
constexpr uint32_t kUpdateTimeoutMs = 100;
constexpr uint32_t kLogIntervalMs = 1000;

SEEED_MR60BHA2 mmWave;
unsigned long lastLogAtMs = 0;
uint32_t sampleIndex = 0;

void printFloatField(const char* label, bool valid, float value, uint8_t decimals = 2) {
  Serial.print(label);
  Serial.print(": ");
  if (valid) {
    Serial.print(value, decimals);
  } else {
    Serial.print("n/a");
  }
  Serial.println();
}

bool tryComputeIntervalSeconds(bool hasRate, float ratePerMinute, float& intervalSeconds) {
  if (!hasRate || ratePerMinute <= 0.0f) {
    intervalSeconds = 0.0f;
    return false;
  }

  intervalSeconds = 60.0f / ratePerMinute;
  return true;
}

void printStatus(unsigned long nowMs) {
  const bool humanDetected = mmWave.isHumanDetected();

  float totalPhase = 0.0f;
  float breathPhase = 0.0f;
  float heartPhase = 0.0f;
  const bool hasPhase =
      mmWave.getHeartBreathPhases(totalPhase, breathPhase, heartPhase);

  float breathRate = 0.0f;
  const bool hasBreathRate = mmWave.getBreathRate(breathRate);

  float heartRate = 0.0f;
  const bool hasHeartRate = mmWave.getHeartRate(heartRate);

  float distance = 0.0f;
  const bool hasDistance = mmWave.getDistance(distance);

  float breathIntervalSeconds = 0.0f;
  const bool hasBreathInterval =
      tryComputeIntervalSeconds(hasBreathRate, breathRate, breathIntervalSeconds);

  float heartIntervalSeconds = 0.0f;
  const bool hasHeartInterval =
      tryComputeIntervalSeconds(hasHeartRate, heartRate, heartIntervalSeconds);

  ++sampleIndex;

  Serial.println();
  Serial.println("================ MR60BHA2 =================");
  Serial.print("sample: ");
  Serial.println(sampleIndex);
  Serial.print("uptime_ms: ");
  Serial.print(nowMs);
  Serial.println();
  Serial.print("human_detected: ");
  Serial.println(humanDetected ? "YES" : "NO");

  printFloatField("distance_m", hasDistance, distance);

  Serial.println("-- breathing --");
  printFloatField("breath_rate_bpm", hasBreathRate, breathRate);
  printFloatField("breath_interval_s", hasBreathInterval, breathIntervalSeconds);

  Serial.println("-- heartbeat --");
  printFloatField("heart_rate_bpm", hasHeartRate, heartRate);
  printFloatField("heart_interval_s", hasHeartInterval, heartIntervalSeconds);

  Serial.println("-- phases --");

  if (hasPhase) {
    printFloatField("total_phase", true, totalPhase, 3);
    printFloatField("breath_phase", true, breathPhase, 3);
    printFloatField("heart_phase", true, heartPhase, 3);
  } else {
    printFloatField("total_phase", false, 0.0f);
    printFloatField("breath_phase", false, 0.0f);
    printFloatField("heart_phase", false, 0.0f);
  }

  Serial.println("===========================================");
}

}  // namespace

void setup() {
  Serial.begin(kDebugBaudRate);
  delay(1000);

  Serial.println();
  Serial.println("[system] MR60BHA2 Arduino IDE validation starting");
  Serial.println("[system] Target scene: single person, within 1.5m, mostly still");

  mmWave.begin(&mmWaveSerial);

  Serial.println("[system] mmWave library initialized");
}

void loop() {
  const unsigned long nowMs = millis();
  const bool updated = mmWave.update(kUpdateTimeoutMs);

  if (!updated) {
    return;
  }

  if (nowMs - lastLogAtMs < kLogIntervalMs) {
    return;
  }

  lastLogAtMs = nowMs;
  printStatus(nowMs);
}