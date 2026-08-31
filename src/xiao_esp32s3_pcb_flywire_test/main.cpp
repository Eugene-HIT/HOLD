/*
 * 创建时间: 2026-07-28
 * 文件主要职责: 提供 PCB 飞线阶段模块功能测试入口，默认使能外设电源与马达 EN，关闭加热控制，仅通过串口、规律震动与规律 LED 验证功能。
 * 核心函数输入输出:
 * - setup(): 拉高 TPS_EN/M_EN，关闭 HEAT_CTRL，初始化主 I2C、MPU、MAX30102、压力读取、DRV2605L 与 RGB。
 * - loop(): 周期打印 I2C/IMU/PPG/压感状态，规律切换 LRA 震动与 RGB 流水灯。
 * 最后更改时间: 2026-07-28
 * 累加式更改日志:
 * - 2026-07-28: 新建飞线测试工程，匹配当前接线: TPS_EN=D6/GPIO43，M_EN=D7/GPIO44，HEAT_CTRL=D1/GPIO2。
 * 注意事项:
 * - 加热控制脚始终输出 LOW，本测试不主动加热。
 * - TPS_EN 与 M_EN 在上电初始化阶段默认拉高，使 SW_OUT 与 DRV2605L 处于可测试状态。
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
constexpr unsigned long kPowerEnableSettleMs = 80;
constexpr unsigned long kStatusLogIntervalMs = 250;
constexpr unsigned long kI2cRescanIntervalMs = 1000;
constexpr unsigned long kMpuPollIntervalMs = 20;
constexpr unsigned long kPpgPollIntervalMs = project_config::kSensorPollIntervalMs;
constexpr unsigned long kPressurePollIntervalMs = project_config::kPressurePollIntervalMs;
constexpr unsigned long kReconnectIntervalMs = 1500;
constexpr uint32_t kI2cTimeoutMs = 20;

constexpr uint8_t kSensorPowerEnablePin = 43;  // D6, TPS_EN
constexpr uint8_t kHapticEnablePin = 44;      // D7, M_EN
constexpr uint8_t kHeaterControlPin = 2;      // D1, HEAT_CTRL, keep off in this test

constexpr uint8_t kRgbRedPin = 7;    // D8
constexpr uint8_t kRgbGreenPin = 8;  // D9
constexpr uint8_t kRgbBluePin = 9;   // D10
constexpr unsigned long kLedStepIntervalMs = 300;

constexpr uint8_t kMpuAddressLow = 0x68;
constexpr uint8_t kMpuAddressHigh = 0x69;
constexpr uint8_t kDrv2605Address = 0x5A;
constexpr uint8_t kMpuRegisterWhoAmI = 0x75;
constexpr uint8_t kMpuRegisterPowerManagement1 = 0x6B;
constexpr uint8_t kMpuRegisterAccelXoutH = 0x3B;
constexpr float kAccelScaleLsbPerG = 16384.0f;
constexpr float kGyroScaleLsbPerDps = 131.0f;

constexpr unsigned long kHapticPlayIntervalMs = 1500;
constexpr uint8_t kDrv2605DevResetBit = 0x80;
constexpr uint8_t kDrv2605LraFeedbackValue = 0xA8;
constexpr uint8_t kDrv2605LraOpenLoopBit = 0x01;
constexpr uint8_t kDrv2605RatedVoltage3200Mv = (3200UL * 255UL) / 5600UL;

struct MpuSample {
  int16_t accelX = 0;
  int16_t accelY = 0;
  int16_t accelZ = 0;
  int16_t temperatureRaw = 0;
  int16_t gyroX = 0;
  int16_t gyroY = 0;
  int16_t gyroZ = 0;
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

constexpr ImuIdentity kSupportedImuIdentities[] = {
    {0x68, "MPU6050/MPU6000", 340.0f, 36.53f},
    {0x70, "MPU6500", 333.87f, 21.0f},
    {0x71, "MPU9250/MPU9255-family", 333.87f, 21.0f},
    {0x73, "MPU9255", 333.87f, 21.0f},
};

Max30102RawReader ppgReader;
HeartRateEstimator heartRateEstimator;
PressureFilmRawReader pressureReader;
Adafruit_DRV2605 hapticDriver;

bool mpuReady = false;
bool ppgReady = false;
bool pressureReady = false;
bool hapticReady = false;
bool hapticOutputActive = false;
bool mpuAddressLowSeen = false;
bool mpuAddressHighSeen = false;
bool max30102Seen = false;
bool drv2605Seen = false;
uint8_t activeMpuAddress = 0;
uint8_t activeMpuWhoAmI = 0;
uint8_t lastHapticStatus = 0;
uint8_t lastHapticMode = 0;
uint8_t lastHapticFeedback = 0;
uint8_t lastHapticControl3 = 0;
uint8_t activeLedIndex = 0;
const char* activeMpuModelName = "MISS";

unsigned long lastStatusLogAtMs = 0;
unsigned long lastI2cRescanAtMs = 0;
unsigned long lastMpuPollAtMs = 0;
unsigned long lastPpgPollAtMs = 0;
unsigned long lastPressurePollAtMs = 0;
unsigned long lastReconnectAtMs = 0;
unsigned long lastHapticPlayAtMs = 0;
unsigned long lastLedStepAtMs = 0;
uint32_t lastPpgSequence = 0;

MpuMetrics lastMpuMetrics{};
Max30102RawReader::Sample lastPpgSample{};
PressureFilmRawReader::Sample lastPressureSample{};

char visibleFlag(bool visible) {
  return visible ? 'Y' : 'N';
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

  if (Wire.requestFrom(address, static_cast<uint8_t>(1), static_cast<uint8_t>(true)) != 1) {
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

  constexpr uint8_t kBytesRequested = 14;
  if (Wire.requestFrom(address, kBytesRequested, static_cast<uint8_t>(true)) != kBytesRequested) {
    return false;
  }

  sample.accelX = static_cast<int16_t>((Wire.read() << 8) | Wire.read());
  sample.accelY = static_cast<int16_t>((Wire.read() << 8) | Wire.read());
  sample.accelZ = static_cast<int16_t>((Wire.read() << 8) | Wire.read());
  sample.temperatureRaw = static_cast<int16_t>((Wire.read() << 8) | Wire.read());
  sample.gyroX = static_cast<int16_t>((Wire.read() << 8) | Wire.read());
  sample.gyroY = static_cast<int16_t>((Wire.read() << 8) | Wire.read());
  sample.gyroZ = static_cast<int16_t>((Wire.read() << 8) | Wire.read());
  return true;
}

bool initializeMpuAt(uint8_t address) {
  uint8_t whoAmI = 0;
  if (!readMpuRegister(address, kMpuRegisterWhoAmI, whoAmI)) {
    return false;
  }

  const ImuIdentity* identity = identifyImu(whoAmI);
  if (identity == nullptr || !writeMpuRegister(address, kMpuRegisterPowerManagement1, 0x00)) {
    return false;
  }

  activeMpuAddress = address;
  activeMpuWhoAmI = whoAmI;
  activeMpuModelName = identity->modelName;
  return true;
}

bool initializeMpu() {
  activeMpuAddress = 0;
  activeMpuWhoAmI = 0;
  activeMpuModelName = "MISS";

  if (initializeMpuAt(kMpuAddressLow)) {
    return true;
  }

  if (initializeMpuAt(kMpuAddressHigh)) {
    return true;
  }

  return false;
}

bool initializePpg() {
  heartRateEstimator.reset();
  lastPpgSequence = 0;
  return ppgReader.begin(Wire);
}

bool initializePressure() {
  return pressureReader.begin();
}

bool initializeHaptic() {
  if (!hapticDriver.begin(&Wire)) {
    hapticOutputActive = false;
    return false;
  }

  hapticDriver.writeRegister8(DRV2605_REG_MODE, 0x00);
  hapticDriver.writeRegister8(DRV2605_REG_MODE, kDrv2605DevResetBit);
  delay(100);
  hapticDriver.writeRegister8(DRV2605_REG_MODE, 0x00);
  hapticDriver.writeRegister8(DRV2605_REG_FEEDBACK, kDrv2605LraFeedbackValue);
  hapticDriver.writeRegister8(DRV2605_REG_RATEDV, kDrv2605RatedVoltage3200Mv);
  hapticDriver.writeRegister8(DRV2605_REG_CLAMPV, kDrv2605RatedVoltage3200Mv);
  hapticDriver.writeRegister8(DRV2605_REG_CONTROL3,
                              hapticDriver.readRegister8(DRV2605_REG_CONTROL3) | kDrv2605LraOpenLoopBit);
  hapticDriver.selectLibrary(6);
  hapticDriver.setMode(DRV2605_MODE_INTTRIG);
  hapticDriver.setWaveform(0, 1);
  hapticDriver.setWaveform(1, 0x80 | 60);
  hapticDriver.setWaveform(2, 1);
  hapticDriver.setWaveform(3, 0);
  hapticDriver.writeRegister8(DRV2605_REG_OVERDRIVE, 0);
  hapticDriver.writeRegister8(DRV2605_REG_SUSTAINPOS, 0);
  hapticDriver.writeRegister8(DRV2605_REG_SUSTAINNEG, 0);
  hapticDriver.writeRegister8(DRV2605_REG_BREAK, 0);
  hapticOutputActive = false;
  lastHapticStatus = hapticDriver.readRegister8(DRV2605_REG_STATUS);
  lastHapticMode = hapticDriver.readRegister8(DRV2605_REG_MODE);
  lastHapticFeedback = hapticDriver.readRegister8(DRV2605_REG_FEEDBACK);
  lastHapticControl3 = hapticDriver.readRegister8(DRV2605_REG_CONTROL3);
  return true;
}

void setRgbState(bool redOn, bool greenOn, bool blueOn) {
  digitalWrite(kRgbRedPin, redOn ? HIGH : LOW);
  digitalWrite(kRgbGreenPin, greenOn ? HIGH : LOW);
  digitalWrite(kRgbBluePin, blueOn ? HIGH : LOW);
}

void setupOutputs() {
  pinMode(kSensorPowerEnablePin, OUTPUT);
  pinMode(kHapticEnablePin, OUTPUT);
  pinMode(kHeaterControlPin, OUTPUT);
  pinMode(kRgbRedPin, OUTPUT);
  pinMode(kRgbGreenPin, OUTPUT);
  pinMode(kRgbBluePin, OUTPUT);
  pinMode(project_config::kUserLedPin, OUTPUT);

  digitalWrite(kHeaterControlPin, LOW);
  digitalWrite(kSensorPowerEnablePin, HIGH);
  digitalWrite(kHapticEnablePin, HIGH);
  digitalWrite(project_config::kUserLedPin, project_config::kLedOffLevel);
  setRgbState(true, false, false);
}

void pollMpu() {
  MpuSample sample;
  if (!mpuReady || !readMpuSample(activeMpuAddress, sample)) {
    mpuReady = false;
    return;
  }

  lastMpuMetrics.accelXg = static_cast<float>(sample.accelX) / kAccelScaleLsbPerG;
  lastMpuMetrics.accelYg = static_cast<float>(sample.accelY) / kAccelScaleLsbPerG;
  lastMpuMetrics.accelZg = static_cast<float>(sample.accelZ) / kAccelScaleLsbPerG;
  lastMpuMetrics.gyroXdps = static_cast<float>(sample.gyroX) / kGyroScaleLsbPerDps;
  lastMpuMetrics.gyroYdps = static_cast<float>(sample.gyroY) / kGyroScaleLsbPerDps;
  lastMpuMetrics.gyroZdps = static_cast<float>(sample.gyroZ) / kGyroScaleLsbPerDps;
  lastMpuMetrics.temperatureC = convertTemperatureCelsius(sample.temperatureRaw);
}

void pollPpg() {
  if (!ppgReady) {
    return;
  }

  ppgReader.update();

  Max30102RawReader::Sample sample;
  if (!ppgReader.readLatestSample(sample) || sample.sequence == lastPpgSequence) {
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

void updateRgbPattern(unsigned long nowMs) {
  if (nowMs - lastLedStepAtMs < kLedStepIntervalMs) {
    return;
  }

  lastLedStepAtMs = nowMs;
  activeLedIndex = (activeLedIndex + 1) % 3;
  setRgbState(activeLedIndex == 0, activeLedIndex == 1, activeLedIndex == 2);
}

void updateHapticPattern(unsigned long nowMs) {
  if (!hapticReady || nowMs - lastHapticPlayAtMs < kHapticPlayIntervalMs) {
    return;
  }

  lastHapticPlayAtMs = nowMs;
  hapticDriver.setMode(DRV2605_MODE_INTTRIG);
  hapticDriver.setWaveform(0, 1);
  hapticDriver.setWaveform(1, 0x80 | 60);
  hapticDriver.setWaveform(2, 1);
  hapticDriver.setWaveform(3, 0);
  hapticDriver.go();
  hapticOutputActive = true;
  lastHapticStatus = hapticDriver.readRegister8(DRV2605_REG_STATUS);
  lastHapticMode = hapticDriver.readRegister8(DRV2605_REG_MODE);
  lastHapticFeedback = hapticDriver.readRegister8(DRV2605_REG_FEEDBACK);
  lastHapticControl3 = hapticDriver.readRegister8(DRV2605_REG_CONTROL3);
}

void tryReconnectAll(unsigned long nowMs) {
  if (nowMs - lastReconnectAtMs < kReconnectIntervalMs) {
    return;
  }

  lastReconnectAtMs = nowMs;

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

void printWiringGuide() {
  Serial.println("[flywire][wiring] TPS_EN: D6/GPIO43 -> J8-P1, default HIGH");
  Serial.println("[flywire][wiring] M_EN: D7/GPIO44 -> J2-P3, default HIGH");
  Serial.println("[flywire][wiring] HEAT_CTRL: D1/GPIO2 -> J1-P3, forced LOW in this test");
  Serial.println("[flywire][wiring] I2C: D4/GPIO5=SDA, D5/GPIO6=SCL -> MPU6050 + MAX30102 + DRV2605L");
  Serial.println("[flywire][wiring] Pressure ADC: D0/GPIO1 -> J4-P3 ADC_PIN");
  Serial.println("[flywire][wiring] RGB: D8/GPIO7=R, D9/GPIO8=G, D10/GPIO9=B");
}

void printStatus(unsigned long nowMs) {
  Serial.printf(
      "[flywire] up=%lums | en tps=HIGH gpio%u motor=HIGH gpio%u heat=LOW gpio%u | i2c 57=%c 68=%c 69=%c 5A=%c | imu=%s model=%s addr=0x%02X ax=%0.3f ay=%0.3f az=%0.3f gx=%0.1f gy=%0.1f gz=%0.1f temp=%0.2f | ppg=%s err=%s ir=%lu red=%lu bpm=%0.1f contact=%s | pressure=%s raw=%u level=%u base=%u peak=%u err=%s | motor=%s rom=1,wait60,1 status=0x%02X mode=0x%02X fb=0x%02X c3=0x%02X | led=%u\n",
      nowMs,
      static_cast<unsigned>(kSensorPowerEnablePin),
      static_cast<unsigned>(kHapticEnablePin),
      static_cast<unsigned>(kHeaterControlPin),
      visibleFlag(max30102Seen),
      visibleFlag(mpuAddressLowSeen),
      visibleFlag(mpuAddressHighSeen),
      visibleFlag(drv2605Seen),
      mpuReady ? "OK" : "MISS",
      activeMpuModelName,
      activeMpuAddress,
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
      heartRateEstimator.contactPresent() ? "Y" : "N",
      pressureReady ? "OK" : "MISS",
      static_cast<unsigned>(lastPressureSample.rawAverage),
      static_cast<unsigned>(lastPressureSample.level),
      static_cast<unsigned>(pressureReader.baselineRaw()),
      static_cast<unsigned>(pressureReader.peakDeltaRaw()),
      pressureReader.lastError(),
      hapticReady ? (hapticOutputActive ? "ROM_GO" : "READY") : "MISS",
      lastHapticStatus,
      lastHapticMode,
      lastHapticFeedback,
      lastHapticControl3,
      static_cast<unsigned>(activeLedIndex));
}

}  // namespace

void setup() {
  setupOutputs();
  delay(kPowerEnableSettleMs);

  Serial.begin(kSerialBaudRate);
  delay(kStartupDelayMs);

  const unsigned long serialAttachStartedAtMs = millis();
  while (!Serial && (millis() - serialAttachStartedAtMs) < kSerialAttachWaitMs) {
    delay(10);
  }

  Serial.println("[flywire][boot] serial-ready");
  printWiringGuide();

  Wire.begin(project_config::kI2cSdaPin, project_config::kI2cSclPin);
  Wire.setClock(project_config::kI2cClockHz);
  Wire.setTimeOut(kI2cTimeoutMs);
  refreshI2cVisibility();

  Serial.printf("[flywire][boot] i2c-visible 57=%c 68=%c 69=%c 5A=%c\n",
                visibleFlag(max30102Seen),
                visibleFlag(mpuAddressLowSeen),
                visibleFlag(mpuAddressHighSeen),
                visibleFlag(drv2605Seen));

  mpuReady = initializeMpu();
  Serial.printf("[flywire][boot] init-mpu-%s model=%s who=0x%02X addr=0x%02X\n",
                mpuReady ? "ok" : "miss",
                activeMpuModelName,
                activeMpuWhoAmI,
                activeMpuAddress);

  ppgReady = initializePpg();
  Serial.printf("[flywire][boot] init-ppg-%s err=%s\n", ppgReady ? "ok" : "miss", ppgReader.lastError());

  pressureReady = initializePressure();
  Serial.printf("[flywire][boot] init-pressure-%s base=%u err=%s\n",
                pressureReady ? "ok" : "miss",
                static_cast<unsigned>(pressureReader.baselineRaw()),
                pressureReader.lastError());

  hapticReady = initializeHaptic();
  Serial.printf("[flywire][boot] init-haptic-%s status=0x%02X mode=0x%02X fb=0x%02X c3=0x%02X\n",
                hapticReady ? "ok" : "miss",
                lastHapticStatus,
                lastHapticMode,
                lastHapticFeedback,
                lastHapticControl3);

  Serial.println("[flywire][boot] setup-done, status lines follow");
}

void loop() {
  const unsigned long nowMs = millis();

  if (nowMs - lastI2cRescanAtMs >= kI2cRescanIntervalMs) {
    lastI2cRescanAtMs = nowMs;
    refreshI2cVisibility();
  }

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
  updateRgbPattern(nowMs);

  if (nowMs - lastStatusLogAtMs >= kStatusLogIntervalMs) {
    lastStatusLogAtMs = nowMs;
    printStatus(nowMs);
  }
}