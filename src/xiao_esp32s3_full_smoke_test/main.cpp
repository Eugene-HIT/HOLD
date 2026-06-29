/*
 * 创建时间: 2026-06-28
 * 文件主要职责: 提供 IMU + PPG + 压力 + DRV2605L + 热反馈控制脚 的整机冒烟测试入口。
 * 核心函数输入输出:
 * - setup(): 初始化主 I2C、MPU6050/MPU6500、MAX30102、压力传感器、DRV2605L 与加热控制 PWM，并打印统一接线提示。
 * - loop(): 周期读取 IMU、PPG、压力，驱动规律震动，并持续输出一行整机状态日志。
 * 最后更改时间: 2026-06-28
 * 累加式更改日志:
 * - 2026-06-28: 新建完整小 Demo 冒烟测试环境，优先验证多模块同时上电、读取、震动与 PWM 控制是否跑通。
 * - 2026-06-28: 兼容 MPU6500/MPU9250 系列 WHO_AM_I，避免新换 IMU 模块在整机版中被误判为失联。
 * 注意事项:
 * - D1(GPIO2) 在本工程中只输出 PWM 控制信号，必须接到逻辑级 N-MOSFET Gate，不能直接驱动加热片负载。
 * - 本入口目标是“整机是否同时跑通”，不是最终产品算法或安全闭环控制。
 */

#include <Arduino.h>
#include <Wire.h>

#include <Adafruit_DRV2605.h>

#include "heart_rate_estimator.h"
#include "max30102_raw_reader.h"
#include "pressure_film_raw_reader.h"
#include "project_config.h"

namespace {

constexpr uint32_t kSerialBaudRate = 115200;
constexpr unsigned long kStartupDelayMs = 300;
constexpr unsigned long kSerialAttachWaitMs = 1500;
constexpr unsigned long kStatusLogIntervalMs = 200;
constexpr unsigned long kMpuPollIntervalMs = 20;
constexpr unsigned long kPpgPollIntervalMs = project_config::kSensorPollIntervalMs;
constexpr unsigned long kPressurePollIntervalMs = project_config::kPressurePollIntervalMs;
constexpr unsigned long kReconnectIntervalMs = 1500;
constexpr uint32_t kI2cTimeoutMs = 20;

constexpr uint8_t kMpuAddressLow = 0x68;
constexpr uint8_t kMpuAddressHigh = 0x69;
constexpr uint8_t kDrv2605Address = 0x5A;
constexpr uint8_t kMpuRegisterWhoAmI = 0x75;
constexpr uint8_t kMpuRegisterPowerManagement1 = 0x6B;
constexpr uint8_t kMpuRegisterAccelXoutH = 0x3B;
constexpr float kAccelScaleLsbPerG = 16384.0f;
constexpr float kGyroScaleLsbPerDps = 131.0f;

constexpr unsigned long kHapticToggleIntervalMs = 700;
constexpr uint8_t kHapticActiveRtp = 0x48;

constexpr uint8_t kHeaterControlPin = 2;   // D1/A1
constexpr uint8_t kHeaterPwmChannel = 2;
constexpr uint32_t kHeaterPwmFrequencyHz = 5000;
constexpr uint8_t kHeaterPwmResolutionBits = 8;
constexpr uint32_t kHeaterPwmDuty80Percent = 204;
constexpr unsigned long kHeaterEnableDelayMs = 5000;

constexpr uint8_t kRgbRedPin = 7;    // D8
constexpr uint8_t kRgbGreenPin = 8;  // D9
constexpr uint8_t kRgbBluePin = 9;   // D10
constexpr unsigned long kLedRunnerIntervalMs = 280;
constexpr unsigned long kRgbSelfTestHoldMs = 700;
constexpr unsigned long kBoardHeartbeatIntervalMs = 500;
constexpr unsigned long kStagePulseOnMs = 80;
constexpr unsigned long kStagePulseOffMs = 120;
constexpr unsigned long kStagePulseGapMs = 260;

struct MpuSample {
  int16_t accelX = 0;
  int16_t accelY = 0;
  int16_t accelZ = 0;
  int16_t temperatureRaw = 0;
  int16_t gyroX = 0;
  int16_t gyroY = 0;
  int16_t gyroZ = 0;
  unsigned long capturedAtMs = 0;
};

struct MpuMetrics {
  float accelXg = 0.0f;
  float accelYg = 0.0f;
  float accelZg = 0.0f;
  float gyroXdps = 0.0f;
  float gyroYdps = 0.0f;
  float gyroZdps = 0.0f;
  float temperatureC = 0.0f;
};

struct ImuIdentity {
  uint8_t whoAmI;
  const char* modelName;
  float temperatureScale;
  float temperatureOffset;
};

Max30102RawReader ppgReader;
HeartRateEstimator heartRateEstimator;
PressureFilmRawReader pressureReader;
Adafruit_DRV2605 hapticDriver;

bool mpuReady = false;
bool ppgReady = false;
bool pressureReady = false;
bool hapticReady = false;
uint8_t activeMpuAddress = 0;
bool hapticOutputEnabled = false;
uint8_t currentHapticRtp = 0;
uint8_t activeLedIndex = 0;
bool heaterEnabled = false;
bool boardHeartbeatOn = false;
bool mpuAddressLowSeen = false;
bool mpuAddressHighSeen = false;
bool max30102Seen = false;
bool drv2605Seen = false;
uint8_t activeMpuWhoAmI = 0;
const char* activeMpuModelName = "MISS";

unsigned long lastMpuPollAtMs = 0;
unsigned long lastPpgPollAtMs = 0;
unsigned long lastPressurePollAtMs = 0;
unsigned long lastStatusLogAtMs = 0;
unsigned long lastReconnectAtMs = 0;
unsigned long lastHapticToggleAtMs = 0;
unsigned long lastLedRunnerAtMs = 0;
unsigned long lastBoardHeartbeatAtMs = 0;
uint32_t lastPpgSequence = 0;

MpuSample lastMpuSample{};
MpuMetrics lastMpuMetrics{};
Max30102RawReader::Sample lastPpgSample{};
PressureFilmRawReader::Sample lastPressureSample{};

constexpr ImuIdentity kSupportedImuIdentities[] = {
  {0x68, "MPU6050/MPU6000", 340.0f, 36.53f},
  {0x70, "MPU6500", 333.87f, 21.0f},
  {0x71, "MPU9250/MPU9255-family", 333.87f, 21.0f},
  {0x73, "MPU9255", 333.87f, 21.0f},
};

float convertAccelToG(int16_t rawAcceleration) {
  return static_cast<float>(rawAcceleration) / kAccelScaleLsbPerG;
}

float convertGyroToDegreesPerSecond(int16_t rawGyro) {
  return static_cast<float>(rawGyro) / kGyroScaleLsbPerDps;
}

const ImuIdentity* identifyImu(uint8_t whoAmI) {
  for (const ImuIdentity& identity : kSupportedImuIdentities) {
    if (identity.whoAmI == whoAmI) {
      return &identity;
    }
  }

  return nullptr;
}

float convertTemperatureCelsius(int16_t rawTemperature) {
  const ImuIdentity* identity = identifyImu(activeMpuWhoAmI);
  if (identity == nullptr) {
    return static_cast<float>(rawTemperature) / 340.0f + 36.53f;
  }

  return static_cast<float>(rawTemperature) / identity->temperatureScale + identity->temperatureOffset;
}

const char* currentLedLabel() {
  switch (activeLedIndex) {
    case 0:
      return "R";
    case 1:
      return "G";
    case 2:
      return "B";
    default:
      return "-";
  }
}

char visibleFlag(bool visible) {
  return visible ? 'Y' : 'N';
}

void logBootStage(const char* stage) {
  Serial.printf("[smoke][boot] %s\n", stage);
}

void writeBoardLed(bool turnOn) {
  digitalWrite(
      project_config::kUserLedPin,
      turnOn ? project_config::kLedOnLevel : project_config::kLedOffLevel);
  boardHeartbeatOn = turnOn;
}

void pulseBoardLed(uint8_t count) {
  for (uint8_t index = 0; index < count; ++index) {
    writeBoardLed(true);
    delay(kStagePulseOnMs);
    writeBoardLed(false);
    delay(kStagePulseOffMs);
  }

  delay(kStagePulseGapMs);
}

void logWiringGuide() {
  Serial.println("[smoke][wiring] 主 I2C: D4(GPIO5)=SDA, D5(GPIO6)=SCL -> MPU6050 + MAX30102 + DRV2605L");
  Serial.println("[smoke][wiring] 压力 AO: D0/A0(GPIO1)");
  Serial.println("[smoke][wiring] 热反馈控制: D1/A1(GPIO2) -> MOSFET Gate，仅 PWM 控制，禁止直驱加热片");
  Serial.println("[smoke][wiring] RGB 流水灯: D8(GPIO7)=R, D9(GPIO8)=G, D10(GPIO9)=B，共阴极接 GND");
  Serial.println("[smoke][wiring] 板载状态灯: GPIO21，低电平点亮，用于阶段报码与运行心跳");
}

bool probeI2cAddress(TwoWire& wireBus, uint8_t address) {
  wireBus.beginTransmission(address);
  return wireBus.endTransmission() == 0;
}

void refreshI2cVisibility() {
  mpuAddressLowSeen = probeI2cAddress(Wire, kMpuAddressLow);
  mpuAddressHighSeen = probeI2cAddress(Wire, kMpuAddressHigh);
  max30102Seen = probeI2cAddress(Wire, project_config::kMax30102Address);
  drv2605Seen = probeI2cAddress(Wire, kDrv2605Address);
}

bool readMpuRegister(uint8_t address, uint8_t reg, uint8_t& value) {
  Wire.beginTransmission(address);
  Wire.write(reg);
  if (Wire.endTransmission(false) != 0) {
    return false;
  }

  const uint8_t bytesRead = Wire.requestFrom(address, static_cast<uint8_t>(1), static_cast<uint8_t>(true));
  if (bytesRead != 1) {
    return false;
  }

  value = Wire.read();
  return true;
}

bool writeMpuRegister(uint8_t address, uint8_t reg, uint8_t value) {
  Wire.beginTransmission(address);
  Wire.write(reg);
  Wire.write(value);
  return Wire.endTransmission() == 0;
}

bool readMpuSample(uint8_t address, MpuSample& sample) {
  Wire.beginTransmission(address);
  Wire.write(kMpuRegisterAccelXoutH);
  if (Wire.endTransmission(false) != 0) {
    return false;
  }

  const uint8_t bytesRequested = 14;
  const uint8_t bytesRead = Wire.requestFrom(address, bytesRequested, static_cast<uint8_t>(true));
  if (bytesRead != bytesRequested) {
    return false;
  }

  sample.accelX = static_cast<int16_t>((Wire.read() << 8) | Wire.read());
  sample.accelY = static_cast<int16_t>((Wire.read() << 8) | Wire.read());
  sample.accelZ = static_cast<int16_t>((Wire.read() << 8) | Wire.read());
  sample.temperatureRaw = static_cast<int16_t>((Wire.read() << 8) | Wire.read());
  sample.gyroX = static_cast<int16_t>((Wire.read() << 8) | Wire.read());
  sample.gyroY = static_cast<int16_t>((Wire.read() << 8) | Wire.read());
  sample.gyroZ = static_cast<int16_t>((Wire.read() << 8) | Wire.read());
  sample.capturedAtMs = millis();
  return true;
}

bool initializeMpuAt(uint8_t address) {
  uint8_t whoAmI = 0;
  if (!readMpuRegister(address, kMpuRegisterWhoAmI, whoAmI)) {
    return false;
  }

  const ImuIdentity* identity = identifyImu(whoAmI);
  if (identity == nullptr) {
    return false;
  }

  if (!writeMpuRegister(address, kMpuRegisterPowerManagement1, 0x00)) {
    return false;
  }

  activeMpuAddress = address;
  activeMpuWhoAmI = whoAmI;
  activeMpuModelName = identity->modelName;
  return true;
}

bool initializeMpu() {
  refreshI2cVisibility();
  activeMpuWhoAmI = 0;
  activeMpuModelName = "MISS";

  if (probeI2cAddress(Wire, kMpuAddressLow) && initializeMpuAt(kMpuAddressLow)) {
    return true;
  }

  if (probeI2cAddress(Wire, kMpuAddressHigh) && initializeMpuAt(kMpuAddressHigh)) {
    return true;
  }

  activeMpuAddress = 0;
  return false;
}

bool initializePpg() {
  heartRateEstimator.reset();
  refreshI2cVisibility();
  return ppgReader.begin(Wire);
}

bool initializePressure() {
  return pressureReader.begin();
}

bool initializeHaptic() {
  refreshI2cVisibility();
  if (!hapticDriver.begin(&Wire)) {
    return false;
  }

  hapticDriver.useLRA();
  hapticDriver.selectLibrary(6);
  hapticDriver.setMode(DRV2605_MODE_REALTIME);
  hapticDriver.setRealtimeValue(0x00);
  currentHapticRtp = 0;
  hapticOutputEnabled = false;
  return true;
}

void setupHeaterPwm() {
  ledcSetup(kHeaterPwmChannel, kHeaterPwmFrequencyHz, kHeaterPwmResolutionBits);
  ledcAttachPin(kHeaterControlPin, kHeaterPwmChannel);
  ledcWrite(kHeaterPwmChannel, 0);
}

void updateHeaterOutput(unsigned long nowMs) {
  if (heaterEnabled || nowMs < kHeaterEnableDelayMs) {
    return;
  }

  heaterEnabled = true;
  ledcWrite(kHeaterPwmChannel, kHeaterPwmDuty80Percent);
  Serial.printf("[smoke][boot] heater-enabled duty=80%% gpio=%u\n", static_cast<unsigned>(kHeaterControlPin));
}

void setRgbState(bool redOn, bool greenOn, bool blueOn) {
  digitalWrite(kRgbRedPin, redOn ? HIGH : LOW);
  digitalWrite(kRgbGreenPin, greenOn ? HIGH : LOW);
  digitalWrite(kRgbBluePin, blueOn ? HIGH : LOW);
}

void runRgbSelfTest() {
  Serial.println("[smoke][boot] rgb-self-test R");
  setRgbState(true, false, false);
  delay(kRgbSelfTestHoldMs);

  Serial.println("[smoke][boot] rgb-self-test G");
  setRgbState(false, true, false);
  delay(kRgbSelfTestHoldMs);

  Serial.println("[smoke][boot] rgb-self-test B");
  setRgbState(false, false, true);
  delay(kRgbSelfTestHoldMs);
}

void setupLedRunner() {
  pinMode(kRgbRedPin, OUTPUT);
  pinMode(kRgbGreenPin, OUTPUT);
  pinMode(kRgbBluePin, OUTPUT);
  runRgbSelfTest();
  setRgbState(true, false, false);
  activeLedIndex = 0;
}

void updateLedRunner(unsigned long nowMs) {
  if (nowMs - lastLedRunnerAtMs < kLedRunnerIntervalMs) {
    return;
  }

  lastLedRunnerAtMs = nowMs;
  activeLedIndex = (activeLedIndex + 1) % 3;
  setRgbState(activeLedIndex == 0, activeLedIndex == 1, activeLedIndex == 2);
}

void updateBoardHeartbeat(unsigned long nowMs) {
  if (nowMs - lastBoardHeartbeatAtMs < kBoardHeartbeatIntervalMs) {
    return;
  }

  lastBoardHeartbeatAtMs = nowMs;
  writeBoardLed(!boardHeartbeatOn);
}

void pollMpu() {
  MpuSample sample;
  if (!mpuReady || !readMpuSample(activeMpuAddress, sample)) {
    mpuReady = false;
    return;
  }

  lastMpuSample = sample;
  lastMpuMetrics.accelXg = convertAccelToG(sample.accelX);
  lastMpuMetrics.accelYg = convertAccelToG(sample.accelY);
  lastMpuMetrics.accelZg = convertAccelToG(sample.accelZ);
  lastMpuMetrics.gyroXdps = convertGyroToDegreesPerSecond(sample.gyroX);
  lastMpuMetrics.gyroYdps = convertGyroToDegreesPerSecond(sample.gyroY);
  lastMpuMetrics.gyroZdps = convertGyroToDegreesPerSecond(sample.gyroZ);
  lastMpuMetrics.temperatureC = convertTemperatureCelsius(sample.temperatureRaw);
}

void pollPpg() {
  if (!ppgReady) {
    return;
  }

  ppgReader.update();

  Max30102RawReader::Sample sample;
  if (!ppgReader.readLatestSample(sample)) {
    return;
  }

  if (sample.sequence == lastPpgSequence) {
    return;
  }

  lastPpgSequence = sample.sequence;
  lastPpgSample = sample;
  heartRateEstimator.addSample(sample);
}

void pollPressure() {
  if (!pressureReady || !pressureReader.update()) {
    pressureReady = false;
    return;
  }

  pressureReader.readLatestSample(lastPressureSample);
}

void updateHapticPattern(unsigned long nowMs) {
  if (!hapticReady) {
    return;
  }

  if (nowMs - lastHapticToggleAtMs < kHapticToggleIntervalMs) {
    return;
  }

  lastHapticToggleAtMs = nowMs;
  hapticOutputEnabled = !hapticOutputEnabled;
  currentHapticRtp = hapticOutputEnabled ? kHapticActiveRtp : 0x00;
  hapticDriver.setRealtimeValue(currentHapticRtp);
}

void tryReconnectAll(unsigned long nowMs) {
  if (nowMs - lastReconnectAtMs < kReconnectIntervalMs) {
    return;
  }

  lastReconnectAtMs = nowMs;
  refreshI2cVisibility();

  if (!mpuReady) {
    mpuReady = initializeMpu();
  }

  if (!ppgReady) {
    ppgReady = initializePpg();
  }

  if (!pressureReady) {
    pressureReady = initializePressure();
  }

  if (!hapticReady) {
    hapticReady = initializeHaptic();
  }
}

void printStatus(unsigned long nowMs) {
  refreshI2cVisibility();

  Serial.printf(
    "[smoke] up=%lums | i2c 57=%c 68=%c 69=%c 5A=%c | imu=%s model=%s ax=%0.3f ay=%0.3f az=%0.3f gx=%0.1f gy=%0.1f gz=%0.1f temp=%0.2f | ppg=%s err=%s ir=%lu red=%lu bpm=%0.1f beat=%s contact=%s | pressure=%s raw=%u level=%u | motor=%s rtp=%u | heater=%s pin=GPIO%u ctrl_only | led=%s\n",
      nowMs,
      visibleFlag(max30102Seen),
      visibleFlag(mpuAddressLowSeen),
      visibleFlag(mpuAddressHighSeen),
      visibleFlag(drv2605Seen),
      mpuReady ? "OK" : "MISS",
    activeMpuModelName,
      lastMpuMetrics.accelXg,
      lastMpuMetrics.accelYg,
      lastMpuMetrics.accelZg,
      lastMpuMetrics.gyroXdps,
      lastMpuMetrics.gyroYdps,
      lastMpuMetrics.gyroZdps,
      lastMpuMetrics.temperatureC,
      ppgReady ? "OK" : "MISS",
      ppgReader.lastError(),
      static_cast<unsigned long>(lastPpgSample.ir),
      static_cast<unsigned long>(lastPpgSample.red),
      heartRateEstimator.hasValidBpm() ? heartRateEstimator.bpm() : 0.0f,
      heartRateEstimator.beatDetectedRecently() ? "Y" : "N",
      heartRateEstimator.contactPresent() ? "Y" : "N",
      pressureReady ? "OK" : "MISS",
      static_cast<unsigned>(lastPressureSample.rawAverage),
      static_cast<unsigned>(lastPressureSample.level),
      hapticReady ? (hapticOutputEnabled ? "ON" : "OFF") : "MISS",
      static_cast<unsigned>(currentHapticRtp),
      heaterEnabled ? "PWM80" : "WAIT",
      static_cast<unsigned>(kHeaterControlPin),
      currentLedLabel());
}

}  // namespace

void setup() {
  pinMode(project_config::kUserLedPin, OUTPUT);
  writeBoardLed(false);
  pulseBoardLed(1);

  Serial.begin(kSerialBaudRate);
  delay(kStartupDelayMs);

  const unsigned long serialAttachStartedAtMs = millis();
  while (!Serial && (millis() - serialAttachStartedAtMs) < kSerialAttachWaitMs) {
    delay(10);
  }

  logBootStage("serial-ready");
  pulseBoardLed(2);

  Wire.begin(project_config::kI2cSdaPin, project_config::kI2cSclPin);
  Wire.setClock(project_config::kI2cClockHz);
  Wire.setTimeOut(kI2cTimeoutMs);
  refreshI2cVisibility();

  logBootStage("i2c-ready");
  pulseBoardLed(3);

  logWiringGuide();
  setupLedRunner();

  logBootStage("init-mpu-start");
  mpuReady = initializeMpu();
  Serial.printf("[smoke][boot] init-mpu-%s\n", mpuReady ? "ok" : "miss");
  if (mpuReady) {
    Serial.printf("[smoke][boot] init-mpu-model=%s who=0x%02X addr=0x%02X\n", activeMpuModelName, activeMpuWhoAmI, activeMpuAddress);
  }
  pulseBoardLed(mpuReady ? 4 : 9);

  logBootStage("init-ppg-start");
  ppgReady = initializePpg();
  Serial.printf("[smoke][boot] init-ppg-%s err=%s\n", ppgReady ? "ok" : "miss", ppgReader.lastError());
  pulseBoardLed(ppgReady ? 5 : 9);

  logBootStage("init-pressure-start");
  pressureReady = initializePressure();
  Serial.printf("[smoke][boot] init-pressure-%s\n", pressureReady ? "ok" : "miss");
  pulseBoardLed(pressureReady ? 6 : 9);

  logBootStage("init-haptic-start");
  hapticReady = initializeHaptic();
  Serial.printf("[smoke][boot] init-haptic-%s\n", hapticReady ? "ok" : "miss");
  pulseBoardLed(hapticReady ? 7 : 9);

  logBootStage("heater-pwm-arm");
  setupHeaterPwm();
  pulseBoardLed(8);

  Serial.printf(
      "[smoke] init | i2c 57=%c 68=%c 69=%c 5A=%c | imu=%s | ppg=%s | pressure=%s | motor=%s | heater=wait->80%% gpio=%u | led_runner=D8/D9/D10\n",
      visibleFlag(max30102Seen),
      visibleFlag(mpuAddressLowSeen),
      visibleFlag(mpuAddressHighSeen),
      visibleFlag(drv2605Seen),
      mpuReady ? "OK" : "MISS",
      ppgReady ? "OK" : "MISS",
      pressureReady ? "OK" : "MISS",
      hapticReady ? "OK" : "MISS",
      static_cast<unsigned>(kHeaterControlPin));

  logBootStage("setup-done");
  writeBoardLed(false);
}

void loop() {
  const unsigned long nowMs = millis();

  tryReconnectAll(nowMs);

  if (nowMs - lastMpuPollAtMs >= kMpuPollIntervalMs) {
    lastMpuPollAtMs = nowMs;
    pollMpu();
  }

  if (nowMs - lastPpgPollAtMs >= kPpgPollIntervalMs) {
    lastPpgPollAtMs = nowMs;
    pollPpg();
  }

  if (nowMs - lastPressurePollAtMs >= kPressurePollIntervalMs) {
    lastPressurePollAtMs = nowMs;
    pollPressure();
  }

  updateHapticPattern(nowMs);
  updateLedRunner(nowMs);
  updateHeaterOutput(nowMs);
  updateBoardHeartbeat(nowMs);

  if (nowMs - lastStatusLogAtMs >= kStatusLogIntervalMs) {
    lastStatusLogAtMs = nowMs;
    printStatus(nowMs);
  }
}