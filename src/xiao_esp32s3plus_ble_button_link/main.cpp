/*
 * 创建时间：2026-06-17
 * 文件职责：XIAO ESP32S3 Plus 按钮 BLE 最小链路验证固件。
 * 核心输入输出：输入为板载 Boot 按钮按下事件；输出为 BLE 按钮事件通知与串口状态日志。
 * 最后更改时间：2026-06-17
 * 更改日志：
 * - 2026-06-17：新增按钮事件 BLE 链路最小骨架，用于小程序、云函数、云存储、LLM 全链路打通。
 * 注意事项：
 * - 当前默认把板载 Boot 键(GPIO0)作为临时测试按钮，只用于本轮链路验证。
 * - 若 Boot 键影响下载或启动稳定性，应切换为外接普通 GPIO 按键。
 */

#include <Arduino.h>
#include <BLEDevice.h>
#include <BLE2902.h>
#include <BLEServer.h>
#include <BLEUtils.h>

namespace {
constexpr char kDeviceName[] = "HOLD-LINK-TEST";
constexpr uint8_t kButtonPin = 0;
constexpr uint8_t kUserLedPin = 21;
constexpr uint32_t kDebounceMs = 180;

BLECharacteristic *eventCharacteristic = nullptr;
BLECharacteristic *infoCharacteristic = nullptr;
bool isClientConnected = false;
uint32_t pressCount = 0;
bool lastStableButtonState = HIGH;
bool lastRawButtonState = HIGH;
uint32_t lastDebounceAtMs = 0;
uint32_t lastAdvertiseLogAtMs = 0;

class LinkServerCallbacks final : public BLEServerCallbacks {
public:
  void onConnect(BLEServer *server) override {
    isClientConnected = true;
    Serial.println("[BLE] client connected");
    digitalWrite(kUserLedPin, LOW);
  }

  void onDisconnect(BLEServer *server) override {
    isClientConnected = false;
    Serial.println("[BLE] client disconnected, restart advertising");
    digitalWrite(kUserLedPin, HIGH);
    BLEDevice::startAdvertising();
  }
};

String buildDeviceInfoJson() {
  String payload = "{";
  payload += "\"device_id\":\"" + String(kDeviceName) + "\",";
  payload += "\"firmware\":\"xiao_esp32s3plus_ble_button_link\",";
  payload += "\"button_pin\":" + String(kButtonPin);
  payload += "}";
  return payload;
}

String buildButtonEventJson() {
  String payload = "{";
  payload += "\"event_type\":\"button_press\",";
  payload += "\"device_id\":\"" + String(kDeviceName) + "\",";
  payload += "\"press_count\":" + String(pressCount) + ",";
  payload += "\"device_timestamp\":" + String(millis());
  payload += "}";
  return payload;
}

void setupBle() {
  BLEDevice::init(kDeviceName);
  BLEServer *server = BLEDevice::createServer();
  server->setCallbacks(new LinkServerCallbacks());

  BLEService *service = server->createService("19B10010-E8F2-537E-4F6C-D104768A1214");

  eventCharacteristic = service->createCharacteristic(
      "19B10011-E8F2-537E-4F6C-D104768A1214",
      BLECharacteristic::PROPERTY_NOTIFY);
    eventCharacteristic->addDescriptor(new BLE2902());

  infoCharacteristic = service->createCharacteristic(
      "19B10012-E8F2-537E-4F6C-D104768A1214",
      BLECharacteristic::PROPERTY_READ);

  infoCharacteristic->setValue(buildDeviceInfoJson().c_str());
  service->start();

  BLEAdvertising *advertising = BLEDevice::getAdvertising();
  advertising->addServiceUUID(service->getUUID());
  advertising->setScanResponse(true);
  advertising->setMinPreferred(0x06);
  advertising->setMinPreferred(0x12);
  BLEDevice::startAdvertising();
  Serial.println("[BLE] advertising started");
}

void emitButtonEvent() {
  ++pressCount;
  String payload = buildButtonEventJson();
  Serial.println("[BUTTON] " + payload);

  if (eventCharacteristic != nullptr && isClientConnected) {
    eventCharacteristic->setValue(payload.c_str());
    eventCharacteristic->notify();
    Serial.println("[BLE] notify sent");
  } else {
    Serial.println("[BLE] notify skipped, no connected client");
  }
}
} // namespace

void setup() {
  Serial.begin(115200);
  delay(1200);

  pinMode(kButtonPin, INPUT_PULLUP);
  pinMode(kUserLedPin, OUTPUT);
  digitalWrite(kUserLedPin, HIGH);

  Serial.println("[BOOT] xiao_esp32s3plus_ble_button_link starting");
  Serial.println("[BOOT] GPIO0 boot button is used as temporary test input");
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

  if (!isClientConnected && now - lastAdvertiseLogAtMs > 5000) {
    lastAdvertiseLogAtMs = now;
    Serial.println("[BLE] waiting for mini program connection...");
  }

  delay(10);
}