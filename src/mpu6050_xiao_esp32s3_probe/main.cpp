/*
 * 创建时间: 2026-06-06
 * 文件主要职责: 在 XIAO ESP32S3 / Plus 上独立验证 MPU6050 模块，并基于单颗 IMU 输出运动强度、呼吸节律、吸气/呼气时间与长叹气计数。
 * 核心函数输入输出:
 * - setup(): 初始化串口与 I2C，总线探测 0x68/0x69 地址，尝试唤醒 MPU6050 并打印接线指导与芯片信息。
 * - loop(): 按固定节拍读取 accel/temp/gyro 原始寄存器，更新单 IMU 呼吸状态机，并周期输出工程单位与呼吸指标。
 * 最后更改时间: 2026-06-28
 * 累加式更改日志:
 * - 2026-06-06: 新建 MPU6050 独立探针入口，避免污染现有反射光、EDA 与主线集成程序。
 * - 2026-06-08: 增加运动强度分级、呼吸间隔/呼吸频率、吸气时间/呼气时间与长叹气计数输出。
 * - 2026-06-28: 放宽 WHO_AM_I 判定，兼容常见 MPU6500/9250 系列，并增加地址级探测输出，便于更换新模块后的快速排查。
 * 注意事项:
 * - 当前算法定位为工程验证版，优先判断“是否有可用呼吸节律”和“当前是否处于剧烈运动”。
 * - 长叹气识别当前采用基于呼气时间和振幅的启发式规则，仅用于实验阶段计数观察。
 * - 模块上的 ADC 引脚通常实际为 AD0，用于切换 I2C 地址；默认建议接地，对应地址 0x68。
 */

#include <Arduino.h>
#include <Wire.h>

#include <math.h>

#include "project_config.h"

namespace {

constexpr uint32_t kSerialBaudRate = 115200;
constexpr uint8_t kMpu6050AddressLow = 0x68;
constexpr uint8_t kMpu6050AddressHigh = 0x69;
constexpr uint8_t kRegisterWhoAmI = 0x75;
constexpr uint8_t kRegisterPowerManagement1 = 0x6B;
constexpr uint8_t kRegisterAccelXoutH = 0x3B;
constexpr unsigned long kStartupDelayMs = 300;
constexpr unsigned long kReadIntervalMs = 20;
constexpr unsigned long kReconnectIntervalMs = 1000;
constexpr unsigned long kLogIntervalMs = 1000;
constexpr uint32_t kI2cTimeoutMs = 20;

constexpr float kAccelScaleLsbPerG = 16384.0f;
constexpr float kGyroScaleLsbPerDps = 131.0f;
constexpr float kRespGravityAlpha = 0.02f;
constexpr float kRespBaselineAlpha = 0.005f;
constexpr float kRespSignalAlpha = 0.18f;
constexpr float kMotionAccAlpha = 0.15f;
constexpr float kMotionGyroAlpha = 0.15f;
constexpr float kMinimumBreathAmplitudeG = 0.010f;
constexpr unsigned long kMinimumHalfBreathMs = 700;
constexpr unsigned long kMaximumHalfBreathMs = 7000;
constexpr unsigned long kBreathStaleTimeoutMs = 15000;

enum class MotionLevel {
  kStill,
  kLight,
  kIntense,
};

enum class ExtremumType {
  kUnknown,
  kPeak,
  kTrough,
};

struct Mpu6050Sample {
  int16_t accelX = 0;
  int16_t accelY = 0;
  int16_t accelZ = 0;
  int16_t temperatureRaw = 0;
  int16_t gyroX = 0;
  int16_t gyroY = 0;
  int16_t gyroZ = 0;
};

struct MotionMetrics {
  float accelXg = 0.0f;
  float accelYg = 0.0f;
  float accelZg = 0.0f;
  float gyroXdps = 0.0f;
  float gyroYdps = 0.0f;
  float gyroZdps = 0.0f;
  float accelNormG = 0.0f;
  float gyroNormDps = 0.0f;
  float accelDynamicG = 0.0f;
  MotionLevel motionLevel = MotionLevel::kStill;
};

struct RespirationMetrics {
  bool hasBreath = false;
  float breathRateBpm = 0.0f;
  float breathIntervalSeconds = 0.0f;
  float inhaleSeconds = 0.0f;
  float exhaleSeconds = 0.0f;
  float inhaleExhaleRatio = 0.0f;
  float dominantAxisValueG = 0.0f;
  float filteredSignalG = 0.0f;
  float cycleAmplitudeG = 0.0f;
  uint32_t sighCount = 0;
  unsigned long lastBreathAtMs = 0;
};

struct ImuIdentity {
  uint8_t whoAmI;
  const char* modelName;
  float temperatureScale;
  float temperatureOffset;
};

bool sensorReady = false;
uint8_t activeAddress = 0;
uint8_t activeWhoAmI = 0;
const char* activeModelName = "UNKNOWN";
unsigned long lastReadAtMs = 0;
unsigned long lastReconnectAtMs = 0;
unsigned long lastLogAtMs = 0;
uint32_t sampleIndex = 0;

float gravityXg = 0.0f;
float gravityYg = -1.0f;
float gravityZg = 0.0f;
float smoothedAccelDynamicG = 0.0f;
float smoothedGyroNormDps = 0.0f;
float respBaselineG = 0.0f;
float respFilteredSignalG = 0.0f;
float previousRespFilteredSignalG = 0.0f;
float previousRespDerivative = 0.0f;
unsigned long previousSignalAtMs = 0;

ExtremumType lastExtremumType = ExtremumType::kUnknown;
float lastPeakValueG = 0.0f;
unsigned long lastPeakAtMs = 0;
float lastTroughValueG = 0.0f;
unsigned long lastTroughAtMs = 0;
unsigned long previousTroughAtMs = 0;
float averageCycleAmplitudeG = 0.0f;
float averageExhaleSeconds = 0.0f;

RespirationMetrics respiration;

constexpr ImuIdentity kSupportedImuIdentities[] = {
  {0x68, "MPU6050/MPU6000", 340.0f, 36.53f},
  {0x70, "MPU6500", 333.87f, 21.0f},
  {0x71, "MPU9250/MPU9255-family", 333.87f, 21.0f},
  {0x73, "MPU9255", 333.87f, 21.0f},
};

float applyExponentialSmoothing(float previous, float sample, float alpha) {
  return previous + alpha * (sample - previous);
}

float squareValue(float value) {
  return value * value;
}

float computeVectorNorm(float x, float y, float z) {
  return sqrtf(squareValue(x) + squareValue(y) + squareValue(z));
}

const char* toMotionLevelText(MotionLevel motionLevel) {
  switch (motionLevel) {
    case MotionLevel::kStill:
      return "STILL";
    case MotionLevel::kLight:
      return "LIGHT";
    case MotionLevel::kIntense:
      return "INTENSE";
  }

  return "UNKNOWN";
}

bool isMotionTooStrongForBreath(MotionLevel motionLevel) {
  return motionLevel == MotionLevel::kIntense;
}

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

void logWiringGuide() {
  Serial.println("[wiring] XIAO 3V3 -> MPU6050 VCC");
  Serial.println("[wiring] XIAO GND -> MPU6050 GND");
  Serial.println("[wiring] XIAO D4(GPIO5/SDA) -> MPU6050 SDA");
  Serial.println("[wiring] XIAO D5(GPIO6/SCL) -> MPU6050 SCL");
  Serial.println("[wiring] MPU6050 AD0/ADC -> GND (默认地址 0x68)");
  Serial.println("[wiring] MPU6050 INT/XDA/XCL 本阶段先不接");
}

bool probeAddress(uint8_t address) {
  Wire.beginTransmission(address);
  return Wire.endTransmission() == 0;
}

bool readRegister(uint8_t address, uint8_t reg, uint8_t& value) {
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

bool writeRegister(uint8_t address, uint8_t reg, uint8_t value) {
  Wire.beginTransmission(address);
  Wire.write(reg);
  Wire.write(value);
  return Wire.endTransmission() == 0;
}

bool readSample(uint8_t address, Mpu6050Sample& sample) {
  Wire.beginTransmission(address);
  Wire.write(kRegisterAccelXoutH);
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
  return true;
}

float convertTemperatureCelsius(int16_t rawTemperature) {
  const ImuIdentity* identity = identifyImu(activeWhoAmI);
  if (identity == nullptr) {
    return static_cast<float>(rawTemperature) / 340.0f + 36.53f;
  }

  return static_cast<float>(rawTemperature) / identity->temperatureScale + identity->temperatureOffset;
}

void logAddressVisibility() {
  const bool address68Visible = probeAddress(kMpu6050AddressLow);
  const bool address69Visible = probeAddress(kMpu6050AddressHigh);
  Serial.printf(
      "[i2c-probe] 0x68=%s | 0x69=%s\n",
      address68Visible ? "ACK" : "MISS",
      address69Visible ? "ACK" : "MISS");
}

MotionMetrics updateMotionMetrics(const Mpu6050Sample& sample) {
  MotionMetrics metrics;
  metrics.accelXg = convertAccelToG(sample.accelX);
  metrics.accelYg = convertAccelToG(sample.accelY);
  metrics.accelZg = convertAccelToG(sample.accelZ);
  metrics.gyroXdps = convertGyroToDegreesPerSecond(sample.gyroX);
  metrics.gyroYdps = convertGyroToDegreesPerSecond(sample.gyroY);
  metrics.gyroZdps = convertGyroToDegreesPerSecond(sample.gyroZ);
  metrics.accelNormG = computeVectorNorm(metrics.accelXg, metrics.accelYg, metrics.accelZg);
  metrics.gyroNormDps = computeVectorNorm(metrics.gyroXdps, metrics.gyroYdps, metrics.gyroZdps);

  gravityXg = applyExponentialSmoothing(gravityXg, metrics.accelXg, kRespGravityAlpha);
  gravityYg = applyExponentialSmoothing(gravityYg, metrics.accelYg, kRespGravityAlpha);
  gravityZg = applyExponentialSmoothing(gravityZg, metrics.accelZg, kRespGravityAlpha);

  const float rawAccelDynamicG = fabsf(metrics.accelNormG - 1.0f);
  smoothedAccelDynamicG = applyExponentialSmoothing(smoothedAccelDynamicG, rawAccelDynamicG, kMotionAccAlpha);
  smoothedGyroNormDps = applyExponentialSmoothing(smoothedGyroNormDps, metrics.gyroNormDps, kMotionGyroAlpha);

  metrics.accelDynamicG = smoothedAccelDynamicG;

  // 先用角速度范数识别明显体动，再用加速度偏离 1g 的程度补足轻微运动判断。
  if (smoothedGyroNormDps > 45.0f || smoothedAccelDynamicG > 0.22f) {
    metrics.motionLevel = MotionLevel::kIntense;
  } else if (smoothedGyroNormDps > 12.0f || smoothedAccelDynamicG > 0.08f) {
    metrics.motionLevel = MotionLevel::kLight;
  } else {
    metrics.motionLevel = MotionLevel::kStill;
  }

  return metrics;
}

float selectDominantRespirationAxis(const MotionMetrics& metrics) {
  const float absGravityX = fabsf(gravityXg);
  const float absGravityY = fabsf(gravityYg);
  const float absGravityZ = fabsf(gravityZg);

  if (absGravityX >= absGravityY && absGravityX >= absGravityZ) {
    return metrics.accelXg;
  }

  if (absGravityY >= absGravityX && absGravityY >= absGravityZ) {
    return metrics.accelYg;
  }

  return metrics.accelZg;
}

void refreshBreathAvailability(unsigned long nowMs) {
  if (nowMs - respiration.lastBreathAtMs <= kBreathStaleTimeoutMs) {
    return;
  }

  respiration.hasBreath = false;
}

bool isLikelySigh(float exhaleSeconds, float cycleAmplitudeG) {
  const bool longExhale = averageExhaleSeconds > 0.0f && exhaleSeconds > averageExhaleSeconds * 1.6f && exhaleSeconds > 2.5f;
  const bool strongAmplitude = averageCycleAmplitudeG > 0.0f && cycleAmplitudeG > averageCycleAmplitudeG * 1.5f;
  return longExhale || strongAmplitude;
}

void finalizeBreathCycle(unsigned long troughAtMs, float troughValueG) {
  if (previousTroughAtMs == 0 || lastPeakAtMs <= previousTroughAtMs || lastPeakAtMs >= troughAtMs) {
    return;
  }

  const unsigned long breathIntervalMs = troughAtMs - previousTroughAtMs;
  const unsigned long inhaleMs = lastPeakAtMs - previousTroughAtMs;
  const unsigned long exhaleMs = troughAtMs - lastPeakAtMs;
  const float cycleAmplitudeG = lastPeakValueG - lastTroughValueG;

  if (breathIntervalMs < 1500 || breathIntervalMs > 12000) {
    return;
  }

  if (inhaleMs < kMinimumHalfBreathMs || inhaleMs > kMaximumHalfBreathMs) {
    return;
  }

  if (exhaleMs < kMinimumHalfBreathMs || exhaleMs > kMaximumHalfBreathMs) {
    return;
  }

  if (cycleAmplitudeG < kMinimumBreathAmplitudeG) {
    return;
  }

  respiration.hasBreath = true;
  respiration.breathIntervalSeconds = static_cast<float>(breathIntervalMs) / 1000.0f;
  respiration.breathRateBpm = 60000.0f / static_cast<float>(breathIntervalMs);
  respiration.inhaleSeconds = static_cast<float>(inhaleMs) / 1000.0f;
  respiration.exhaleSeconds = static_cast<float>(exhaleMs) / 1000.0f;
  respiration.inhaleExhaleRatio = respiration.exhaleSeconds > 0.0f ? respiration.inhaleSeconds / respiration.exhaleSeconds : 0.0f;
  respiration.cycleAmplitudeG = cycleAmplitudeG;
  respiration.lastBreathAtMs = troughAtMs;

  averageCycleAmplitudeG = averageCycleAmplitudeG == 0.0f
      ? cycleAmplitudeG
      : applyExponentialSmoothing(averageCycleAmplitudeG, cycleAmplitudeG, 0.20f);
  averageExhaleSeconds = averageExhaleSeconds == 0.0f
      ? respiration.exhaleSeconds
      : applyExponentialSmoothing(averageExhaleSeconds, respiration.exhaleSeconds, 0.20f);

  if (isLikelySigh(respiration.exhaleSeconds, cycleAmplitudeG)) {
    ++respiration.sighCount;
  }

  lastTroughAtMs = troughAtMs;
  lastTroughValueG = troughValueG;
}

void updateRespirationMetrics(unsigned long nowMs, const MotionMetrics& motion) {
  respiration.dominantAxisValueG = selectDominantRespirationAxis(motion);
  respBaselineG = applyExponentialSmoothing(respBaselineG, respiration.dominantAxisValueG, kRespBaselineAlpha);

  const float detrendedSignalG = respiration.dominantAxisValueG - respBaselineG;
  respFilteredSignalG = applyExponentialSmoothing(respFilteredSignalG, detrendedSignalG, kRespSignalAlpha);
  respiration.filteredSignalG = respFilteredSignalG;

  if (previousSignalAtMs == 0) {
    previousSignalAtMs = nowMs;
    previousRespFilteredSignalG = respFilteredSignalG;
    return;
  }

  const float currentDerivative = respFilteredSignalG - previousRespFilteredSignalG;

  // 在剧烈运动时暂停极值识别，避免把大幅体动误判成呼吸周期。
  if (!isMotionTooStrongForBreath(motion.motionLevel)) {
    const bool peakDetected = previousRespDerivative > 0.0f && currentDerivative <= 0.0f;
    const bool troughDetected = previousRespDerivative < 0.0f && currentDerivative >= 0.0f;

    if (peakDetected) {
      const unsigned long halfCycleMs = nowMs - lastTroughAtMs;
      const float amplitudeG = previousRespFilteredSignalG - lastTroughValueG;
      if (lastTroughAtMs != 0 && halfCycleMs >= kMinimumHalfBreathMs && halfCycleMs <= kMaximumHalfBreathMs && amplitudeG >= kMinimumBreathAmplitudeG) {
        lastPeakAtMs = nowMs;
        lastPeakValueG = previousRespFilteredSignalG;
        lastExtremumType = ExtremumType::kPeak;
      }
    }

    if (troughDetected) {
      const bool hasPreviousPeak = lastPeakAtMs != 0 && lastPeakAtMs > lastTroughAtMs;
      const unsigned long exhaleMs = nowMs - lastPeakAtMs;
      const float amplitudeG = lastPeakValueG - previousRespFilteredSignalG;
      if (hasPreviousPeak && exhaleMs >= kMinimumHalfBreathMs && exhaleMs <= kMaximumHalfBreathMs && amplitudeG >= kMinimumBreathAmplitudeG) {
        previousTroughAtMs = lastTroughAtMs;
        finalizeBreathCycle(nowMs, previousRespFilteredSignalG);
        lastExtremumType = ExtremumType::kTrough;
      } else if (lastExtremumType == ExtremumType::kUnknown) {
        lastTroughAtMs = nowMs;
        lastTroughValueG = previousRespFilteredSignalG;
        lastExtremumType = ExtremumType::kTrough;
      }
    }
  }

  previousRespDerivative = currentDerivative;
  previousRespFilteredSignalG = respFilteredSignalG;
  previousSignalAtMs = nowMs;
  refreshBreathAvailability(nowMs);
}

bool tryInitializeAt(uint8_t address) {
  if (!probeAddress(address)) {
    return false;
  }

  uint8_t whoAmI = 0;
  if (!readRegister(address, kRegisterWhoAmI, whoAmI)) {
    Serial.printf("[mpu6050] addr=0x%02X | WHO_AM_I read failed\n", address);
    return false;
  }

  Serial.printf("[mpu6050] addr=0x%02X | WHO_AM_I=0x%02X\n", address, whoAmI);
  const ImuIdentity* identity = identifyImu(whoAmI);
  if (identity == nullptr) {
    Serial.println("[mpu6050] unexpected WHO_AM_I, continue probing other address");
    return false;
  }

  Serial.printf("[mpu6050] identified model=%s\n", identity->modelName);

  if (!writeRegister(address, kRegisterPowerManagement1, 0x00)) {
    Serial.println("[mpu6050] wake-up write failed");
    return false;
  }

  delay(100);
  activeAddress = address;
  activeWhoAmI = whoAmI;
  activeModelName = identity->modelName;
  sensorReady = true;
  Serial.printf("[mpu6050] init ok | active_addr=0x%02X | model=%s\n", activeAddress, activeModelName);
  return true;
}

void tryInitializeSensor() {
  sensorReady = false;
  activeAddress = 0;
  activeWhoAmI = 0;
  activeModelName = "UNKNOWN";

  logAddressVisibility();

  if (tryInitializeAt(kMpu6050AddressLow)) {
    return;
  }

  if (tryInitializeAt(kMpu6050AddressHigh)) {
    return;
  }

  Serial.println("[mpu6050] no valid device found at 0x68 or 0x69");
}

void printSample(unsigned long nowMs, const Mpu6050Sample& sample, const MotionMetrics& motion) {
  ++sampleIndex;
  Serial.printf(
      "[mpu6050] seq=%lu | up=%lums | motion=%-7s | addr=0x%02X | acc_g=(%6.3f,%6.3f,%6.3f) | gyro_dps=(%7.2f,%7.2f,%7.2f) | acc_norm=%.3f | gyro_norm=%.2f | temp=%.2fC\n",
      static_cast<unsigned long>(sampleIndex),
      nowMs,
      toMotionLevelText(motion.motionLevel),
      activeAddress,
      motion.accelXg,
      motion.accelYg,
      motion.accelZg,
      motion.gyroXdps,
      motion.gyroYdps,
      motion.gyroZdps,
      motion.accelNormG,
      motion.gyroNormDps,
      convertTemperatureCelsius(sample.temperatureRaw));

  if (!respiration.hasBreath) {
    Serial.printf(
        "[resp] signal_g=% .4f | axis_g=% .4f | motion=%-7s | breath=searching | sigh_count=%lu\n",
        respiration.filteredSignalG,
        respiration.dominantAxisValueG,
        toMotionLevelText(motion.motionLevel),
        static_cast<unsigned long>(respiration.sighCount));
    return;
  }

  Serial.printf(
      "[resp] breath_bpm=%5.2f | interval_s=%4.2f | inhale_s=%4.2f | exhale_s=%4.2f | ie_ratio=%4.2f | amp_g=% .4f | sigh_count=%lu\n",
      respiration.breathRateBpm,
      respiration.breathIntervalSeconds,
      respiration.inhaleSeconds,
      respiration.exhaleSeconds,
      respiration.inhaleExhaleRatio,
      respiration.cycleAmplitudeG,
      static_cast<unsigned long>(respiration.sighCount));
}

}  // namespace

void setup() {
  Serial.begin(kSerialBaudRate);
  delay(kStartupDelayMs);

  Serial.println();
  Serial.println("[system] MPU6050 probe starting on XIAO ESP32S3 / Plus");
  Serial.println("[system] Goal: verify module address, WHO_AM_I, wake-up, motion level and single-IMU respiration metrics");
  logWiringGuide();

  Wire.begin(project_config::kI2cSdaPin, project_config::kI2cSclPin);
  Wire.setClock(project_config::kI2cClockHz);
  Wire.setTimeOut(kI2cTimeoutMs);

  Serial.printf("[i2c] SDA=GPIO%u | SCL=GPIO%u | clock=%luHz\n",
                project_config::kI2cSdaPin,
                project_config::kI2cSclPin,
                static_cast<unsigned long>(project_config::kI2cClockHz));

  tryInitializeSensor();
}

void loop() {
  const unsigned long nowMs = millis();

  if (!sensorReady) {
    if (nowMs - lastReconnectAtMs < kReconnectIntervalMs) {
      return;
    }

    lastReconnectAtMs = nowMs;
    tryInitializeSensor();
    return;
  }

  if (nowMs - lastReadAtMs < kReadIntervalMs) {
    return;
  }

  lastReadAtMs = nowMs;

  Mpu6050Sample sample;
  if (!readSample(activeAddress, sample)) {
    Serial.println("[mpu6050] sample read failed, sensor will be re-probed");
    sensorReady = false;
    return;
  }

  const MotionMetrics motion = updateMotionMetrics(sample);
  updateRespirationMetrics(nowMs, motion);

  if (nowMs - lastLogAtMs < kLogIntervalMs) {
    return;
  }

  lastLogAtMs = nowMs;
  printSample(nowMs, sample, motion);
  Serial.printf("[mpu6050] model=%s | who_am_i=0x%02X\n", activeModelName, activeWhoAmI);
}