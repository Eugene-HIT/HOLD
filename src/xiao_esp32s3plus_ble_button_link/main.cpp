#include <Arduino.h>
#include <BLE2902.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <Wire.h>

#include <Adafruit_DRV2605.h>

namespace {
constexpr char kDeviceName[] = "HOLD-LINK-TEST";
constexpr char kServiceUuid[] = "19B10010-E8F2-537E-4F6C-D104768A1214";
constexpr char kEventUuid[] = "19B10011-E8F2-537E-4F6C-D104768A1214";
constexpr char kInfoUuid[] = "19B10012-E8F2-537E-4F6C-D104768A1214";
constexpr char kCommandUuid[] = "19B10013-E8F2-537E-4F6C-D104768A1214";

constexpr uint8_t kButtonPin = 0;
constexpr uint8_t kUserLedPin = 21;
constexpr uint32_t kDebounceMs = 180;
constexpr uint32_t kTelemetryMs = 1000;
constexpr uint32_t kBreathStepMs = 120;
constexpr uint32_t kCalibrationMs = 12000;

BLECharacteristic* eventCharacteristic = nullptr;
BLECharacteristic* commandCharacteristic = nullptr;
Adafruit_DRV2605 haptic;

bool isClientConnected = false;
bool hapticReady = false;
bool breathEnabled = false;
bool calibrationRunning = false;
bool lastStableButtonState = HIGH;
bool lastRawButtonState = HIGH;
uint32_t pressCount = 0;
uint32_t breathStep = 0;
uint32_t calibrationStartedAtMs = 0;
uint32_t lastDebounceAtMs = 0;
uint32_t lastAdvertiseLogAtMs = 0;
uint32_t lastTelemetryAtMs = 0;
uint32_t lastBreathStepAtMs = 0;

String jsonPair(const char* key, const String& value) {
  return "\"" + String(key) + "\":\"" + value + "\"";
}

void notifyJson(const String& payload) {
  Serial.println("[BLE] " + payload);
  if (eventCharacteristic != nullptr && isClientConnected) {
    eventCharacteristic->setValue(payload.c_str());
    eventCharacteristic->notify();
  }
}

void setMotor(uint8_t rtp) {
  if (hapticReady) {
    haptic.setRealtimeValue(rtp);
  }
  digitalWrite(kUserLedPin, rtp > 0 ? LOW : HIGH);
}

void stopFeedback() {
  breathEnabled = false;
  calibrationRunning = false;
  setMotor(0);
}

String buildStatusJson(const char* eventType) {
  String payload = "{";
  payload += jsonPair("event_type", eventType) + ",";
  payload += jsonPair("device_id", kDeviceName) + ",";
  payload += "\"press_count\":";
  payload += String(pressCount);
  payload += ",\"breath_enabled\":";
  payload += breathEnabled ? "true" : "false";
  payload += ",\"calibration_running\":";
  payload += calibrationRunning ? "true" : "false";
  payload += ",\"haptic_ready\":";
  payload += hapticReady ? "true" : "false";
  payload += ",\"device_timestamp\":";
  payload += String(millis());
  payload += "}";
  return payload;
}

void emitStatus(const char* eventType) {
  notifyJson(buildStatusJson(eventType));
}

void handleCommand(const String& command) {
  if (command.indexOf("breath_start") >= 0) {
    calibrationRunning = false;
    breathEnabled = true;
    breathStep = 0;
    lastBreathStepAtMs = 0;
    emitStatus("breath_started");
    return;
  }

  if (command.indexOf("breath_stop") >= 0) {
    stopFeedback();
    emitStatus("breath_stopped");
    return;
  }

  if (command.indexOf("calibrate_start") >= 0) {
    breathEnabled = false;
    calibrationRunning = true;
    calibrationStartedAtMs = millis();
    emitStatus("calibration_started");
    return;
  }

  emitStatus("unknown_command");
}

class CommandCallbacks final : public BLECharacteristicCallbacks {
 public:
  void onWrite(BLECharacteristic* characteristic) override {
    String command = characteristic->getValue().c_str();
    command.trim();
    Serial.println("[CMD] " + command);
    handleCommand(command);
  }
};

class LinkServerCallbacks final : public BLEServerCallbacks {
 public:
  void onConnect(BLEServer*) override {
    isClientConnected = true;
    Serial.println("[BLE] client connected");
    digitalWrite(kUserLedPin, LOW);
  }

  void onDisconnect(BLEServer*) override {
    isClientConnected = false;
    stopFeedback();
    Serial.println("[BLE] client disconnected, restart advertising");
    BLEDevice::startAdvertising();
  }
};

void setupHaptic() {
  Wire.begin();
  hapticReady = haptic.begin(&Wire);
  if (!hapticReady) {
    Serial.println("[HAPTIC] DRV2605L not found, using LED fallback");
    return;
  }

  haptic.useLRA();
  haptic.selectLibrary(6);
  haptic.setMode(DRV2605_MODE_REALTIME);
  haptic.setRealtimeValue(0);
  Serial.println("[HAPTIC] ready");
}

void setupBle() {
  BLEDevice::init(kDeviceName);
  BLEServer* server = BLEDevice::createServer();
  server->setCallbacks(new LinkServerCallbacks());

  BLEService* service = server->createService(kServiceUuid);
  eventCharacteristic = service->createCharacteristic(kEventUuid, BLECharacteristic::PROPERTY_NOTIFY);
  eventCharacteristic->addDescriptor(new BLE2902());

  service->createCharacteristic(kInfoUuid, BLECharacteristic::PROPERTY_READ)
      ->setValue(buildStatusJson("device_info").c_str());

  commandCharacteristic = service->createCharacteristic(kCommandUuid, BLECharacteristic::PROPERTY_WRITE);
  commandCharacteristic->setCallbacks(new CommandCallbacks());

  service->start();
  BLEAdvertising* advertising = BLEDevice::getAdvertising();
  advertising->addServiceUUID(service->getUUID());
  advertising->setScanResponse(true);
  BLEDevice::startAdvertising();
  Serial.println("[BLE] advertising started");
}

void updateBreathFeedback(uint32_t now) {
  if (!breathEnabled || now - lastBreathStepAtMs < kBreathStepMs) {
    return;
  }

  lastBreathStepAtMs = now;
  const uint8_t phase = breathStep++ % 40;
  const uint8_t rtp = phase < 20 ? phase * 4 : (39 - phase) * 4;
  setMotor(rtp);
}

void updateCalibration(uint32_t now) {
  if (!calibrationRunning) {
    return;
  }

  setMotor((now / 250) % 2 == 0 ? 0x35 : 0x00);
  if (now - calibrationStartedAtMs >= kCalibrationMs) {
    stopFeedback();
    emitStatus("calibration_done");
  }
}

void emitButtonEvent() {
  ++pressCount;
  emitStatus("button_press");
}
}  // namespace

void setup() {
  Serial.begin(115200);
  delay(800);
  pinMode(kButtonPin, INPUT_PULLUP);
  pinMode(kUserLedPin, OUTPUT);
  digitalWrite(kUserLedPin, HIGH);

  Serial.println("[BOOT] HOLD BLE link starting");
  setupHaptic();
  setupBle();
}

void loop() {
  const uint32_t now = millis();
  const bool rawState = digitalRead(kButtonPin);

  if (rawState != lastRawButtonState) {
    lastDebounceAtMs = now;
    lastRawButtonState = rawState;
  }

  if ((now - lastDebounceAtMs) > kDebounceMs && rawState != lastStableButtonState) {
    lastStableButtonState = rawState;
    if (lastStableButtonState == LOW) {
      emitButtonEvent();
    }
  }

  updateBreathFeedback(now);
  updateCalibration(now);

  if (isClientConnected && now - lastTelemetryAtMs > kTelemetryMs) {
    lastTelemetryAtMs = now;
    emitStatus("telemetry");
  }

  if (!isClientConnected && now - lastAdvertiseLogAtMs > 5000) {
    lastAdvertiseLogAtMs = now;
    Serial.println("[BLE] waiting for mini program connection...");
  }

  delay(10);
}
