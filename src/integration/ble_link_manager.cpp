#include "ble_link_manager.h"

#include <BLE2902.h>
#include <BLEDevice.h>
#include <BLEServer.h>

#include "data_packager.h"

namespace hold_integration {
namespace {

constexpr char kIntegratedDeviceName[] = "HOLD-INTEGRATED";
constexpr char kServiceUuid[] = "19B10010-E8F2-537E-4F6C-D104768A1214";
constexpr char kNotifyCharacteristicUuid[] = "19B10011-E8F2-537E-4F6C-D104768A1214";
constexpr char kCommandCharacteristicUuid[] = "19B10012-E8F2-537E-4F6C-D104768A1214";

BleLinkState linkState = BleLinkState::kIdle;
bool clientConnected = false;
bool connectedEventPending = false;
bool disconnectedEventPending = false;
bool breathGuideRequestPending = false;
uint32_t breathGuideRequestDurationMs = 48000;
BLEServer *serverInstance = nullptr;
BLECharacteristic *notifyCharacteristic = nullptr;
BLECharacteristic *commandCharacteristic = nullptr;

uint32_t parseUnsignedField(const String &payload, const char *key, uint32_t fallbackValue) {
  const String pattern = String("\"") + String(key) + String("\":");
  const int start = payload.indexOf(pattern);
  if (start < 0) {
    return fallbackValue;
  }

  int index = start + pattern.length();
  String digits = "";
  while (index < payload.length()) {
    const char current = payload.charAt(index);
    if (current < '0' || current > '9') {
      break;
    }
    digits += current;
    index += 1;
  }

  return digits.length() > 0 ? static_cast<uint32_t>(digits.toInt()) : fallbackValue;
}

class IntegratedBleServerCallbacks final : public BLEServerCallbacks {
public:
  void onConnect(BLEServer *server) override {
    (void)server;
    clientConnected = true;
    linkState = BleLinkState::kConnected;
    connectedEventPending = true;
    disconnectedEventPending = false;
    Serial.println("[ble] real client connected");
  }

  void onDisconnect(BLEServer *server) override {
    (void)server;
    clientConnected = false;
    linkState = BleLinkState::kAdvertising;
    disconnectedEventPending = true;
    connectedEventPending = false;
    Serial.println("[ble] client disconnected, restart advertising");
    BLEDevice::startAdvertising();
  }
};

class CommandCharacteristicCallbacks final : public BLECharacteristicCallbacks {
public:
  void onWrite(BLECharacteristic *characteristic) override {
    if (characteristic == nullptr) {
      return;
    }

    const std::string value = characteristic->getValue();
    Serial.print("[ble-command] ");
    Serial.println(value.c_str());

    const String payload = String(value.c_str());
    if (payload.indexOf("start_breath_guide") >= 0) {
      breathGuideRequestPending = true;
      breathGuideRequestDurationMs = parseUnsignedField(payload, "duration_ms", 48000);
    }
  }
};

IntegratedBleServerCallbacks serverCallbacks;
CommandCharacteristicCallbacks commandCallbacks;

void notifyJsonPayload(const String &payload) {
  if (notifyCharacteristic != nullptr && clientConnected) {
    notifyCharacteristic->setValue(payload.c_str());
    notifyCharacteristic->notify();
  }
}

}  // namespace

void bleLinkManagerBegin(uint32_t nowMs) {
  (void)nowMs;
  linkState = BleLinkState::kAdvertising;
  clientConnected = false;
  connectedEventPending = false;
  disconnectedEventPending = false;

  BLEDevice::init(kIntegratedDeviceName);
  serverInstance = BLEDevice::createServer();
  serverInstance->setCallbacks(&serverCallbacks);

  BLEService *service = serverInstance->createService(kServiceUuid);
  notifyCharacteristic = service->createCharacteristic(
      kNotifyCharacteristicUuid, BLECharacteristic::PROPERTY_NOTIFY);
  notifyCharacteristic->addDescriptor(new BLE2902());

  commandCharacteristic = service->createCharacteristic(
      kCommandCharacteristicUuid,
      BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_WRITE |
          BLECharacteristic::PROPERTY_WRITE_NR);
  commandCharacteristic->setCallbacks(&commandCallbacks);
  commandCharacteristic->setValue("{}");

  service->start();

  BLEAdvertising *advertising = BLEDevice::getAdvertising();
  advertising->addServiceUUID(service->getUUID());
  advertising->setScanResponse(true);
  advertising->setMinPreferred(0x06);
  advertising->setMinPreferred(0x12);
  BLEDevice::startAdvertising();
  Serial.println("[ble] integrated advertising started");
}

void bleLinkManagerTick(uint32_t nowMs) {
  (void)nowMs;
}

bool bleLinkManagerConsumeConnectedEvent() {
  const bool hadEvent = connectedEventPending;
  connectedEventPending = false;
  return hadEvent;
}

bool bleLinkManagerConsumeDisconnectedEvent() {
  const bool hadEvent = disconnectedEventPending;
  disconnectedEventPending = false;
  return hadEvent;
}

bool bleLinkManagerConsumeBreathGuideRequest(uint32_t *durationMs) {
  const bool hadEvent = breathGuideRequestPending;
  if (durationMs != nullptr) {
    *durationMs = breathGuideRequestDurationMs;
  }
  breathGuideRequestPending = false;
  breathGuideRequestDurationMs = 48000;
  return hadEvent;
}

BleLinkState bleLinkManagerGetLinkState() { return linkState; }

bool bleLinkManagerIsClientConnected() { return clientConnected; }

void bleLinkManagerPublishDeviceState(const DeviceStateSnapshot &snapshot) {
  const String payload = packDeviceStateJson(snapshot);
  notifyJsonPayload(payload);
  Serial.print("[ble-device-state] ");
  Serial.println(payload);
}

void bleLinkManagerPublishCalibrationStatus(const CalibrationStatusSnapshot &snapshot) {
  const String payload = packCalibrationStatusJson(snapshot);
  notifyJsonPayload(payload);
  Serial.print("[ble-calibration] ");
  Serial.println(payload);
}

void bleLinkManagerPublishRespDebug(const CalibrationStatusSnapshot &snapshot) {
  const String payload = packRespDebugJson(snapshot);
  notifyJsonPayload(payload);
  Serial.print("[ble-resp-debug] ");
  Serial.println(payload);
}

void bleLinkManagerPublishActiveRealtime(const ActivePpgRealtimeSnapshot &snapshot) {
  const String payload = packActiveRealtimeJson(snapshot);
  notifyJsonPayload(payload);
  Serial.print("[ble-active-rt] ");
  Serial.println(payload);
}

void bleLinkManagerPublishActiveRealtimeBatch(const ActivePpgRealtimeBatch &batch) {
  const String payload = packActiveRealtimeBatchJson(batch);
  notifyJsonPayload(payload);
  Serial.printf("[ble-active-rt-batch] samples=%u bpm=%u qs=%u beat=%u\n",
                batch.sampleCount,
                batch.heartRateBpm,
                batch.qualityScore,
                batch.beatCount);
}

void bleLinkManagerPublishPassivePpgRealtimeBatch(const PassivePpgRealtimeBatch &batch) {
  const String payload = packPassivePpgRealtimeBatchJson(batch);
  notifyJsonPayload(payload);
  Serial.printf("[ble-passive-ppg-batch] samples=%u bpm=%u qs=%u\n",
                batch.sampleCount,
                batch.heartRateBpm,
                batch.qualityScore);
}

void bleLinkManagerPublishPassiveRespWindow(const PassiveRespWindow &window,
                                            uint16_t fragmentIndex,
                                            uint16_t fragmentTotal) {
  const String payload = packPassiveRespWindowJson(window, fragmentIndex, fragmentTotal);
  notifyJsonPayload(payload);
  Serial.print("[ble-passive] ");
  Serial.println(payload);
}

void bleLinkManagerPublishActiveWindow(const ActivePpgWindow &window,
                                       uint16_t fragmentIndex,
                                       uint16_t fragmentTotal,
                                       size_t processedPointOffset,
                                       size_t processedPointCount,
                                       size_t beatOffset,
                                       size_t beatCount) {
  const String payload = packActiveWindowJson(window,
                                              fragmentIndex,
                                              fragmentTotal,
                                              processedPointOffset,
                                              processedPointCount,
                                              beatOffset,
                                              beatCount);
  notifyJsonPayload(payload);
  Serial.print("[ble-active] ");
  Serial.println(payload);
}

void bleLinkManagerPublishDebugLog(const char *message) {
  if (message != nullptr && message[0] != '\0') {
    notifyJsonPayload(String("{\"msg_type\":\"debug_log\",\"message\":\"") +
                      String(message) + "\"}");
  }
  Serial.print("[ble-debug] ");
  Serial.println(message == nullptr ? "" : message);
}

}  // namespace hold_integration