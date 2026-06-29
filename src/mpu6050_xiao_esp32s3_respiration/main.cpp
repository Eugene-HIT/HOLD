/*
 * 创建时间: 2026-06-08
 * 文件主要职责: 在 XIAO ESP32S3 / Plus + MPU6050 上实现“引导式个体化校准 + 个人参数运行”的单 IMU 呼吸实验入口。
 * 核心函数输入输出:
 * - setup(): 初始化串口、I2C 和 MPU6050，打印接线说明，并进入引导式校准流程。
 * - loop(): 固定采样读取 IMU；校准阶段按提示学习个人基线与叹气特征，运行阶段输出呼吸周期、吸气/呼气时间和叹气计数。
 * 最后更改时间: 2026-06-09
 * 累加式更改日志:
 * - 2026-06-08: 新建单 IMU 呼吸实验入口。
 * - 2026-06-08: 由固定阈值实验切换到“引导式个体化校准 + 轻量学习”第一版实现。
 * - 2026-06-09: 新增运行阶段 VOFA 调试输出，便于观察原始载波、基线与判定量曲线。
 * 注意事项:
 * - 当前版本不做复杂模型训练，而是根据校准阶段统计个人参数。
 * - 第一版默认每次上电重新校准，暂不写入 Flash 持久化。
 * - 当前目标是形成可验证的工程闭环，而不是医学级识别精度。
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
constexpr uint8_t kExpectedWhoAmI = 0x68;

constexpr unsigned long kStartupDelayMs = 300;
constexpr unsigned long kSampleIntervalMs = 20;
constexpr unsigned long kLogIntervalMs = 1000;
constexpr unsigned long kReconnectIntervalMs = 1000;
constexpr unsigned long kBreathDetectorWarmupMs = 3000;
constexpr unsigned long kMinExtremumGapMs = 250;
constexpr unsigned long kBreathDisplayStaleMs = 6000;

constexpr unsigned long kCalibrationStillMs = 10000;
constexpr unsigned long kNormalInhalePromptMs = 2000;
constexpr unsigned long kNormalExhalePromptMs = 3000;
constexpr uint8_t kNormalCycles = 6;
constexpr unsigned long kDeepInhalePromptMs = 3000;
constexpr unsigned long kDeepExhalePromptMs = 4000;
constexpr uint8_t kDeepCycles = 3;
constexpr unsigned long kSighInhalePromptMs = 2000;
constexpr unsigned long kSighExhalePromptMs = 6000;
constexpr uint8_t kSighCycles = 3;

constexpr unsigned long kDefaultMinHalfBreathMs = 560;
constexpr unsigned long kDefaultMinBreathIntervalMs = 1300;
constexpr unsigned long kDefaultMaxBreathIntervalMs = 10000;
constexpr unsigned long kAcceptanceLockMinMs = 900;
constexpr unsigned long kAcceptanceLockMaxMs = 2200;
constexpr float kAcceptanceLockRatio = 0.50f;

constexpr float kAccelLsbPerG = 16384.0f;
constexpr float kGyroLsbPerDps = 131.0f;
constexpr float kGravityEstimateAlpha = 0.02f;
constexpr float kBreathBaselineAlpha = 0.003f;
constexpr float kBreathSmoothAlpha = 0.18f;
constexpr float kBreathDetectionLowPassAlpha = 0.12f;
constexpr float kFallbackAmplitudeThresholdG = 0.0045f;

struct Mpu6050Sample {
  int16_t accelX = 0;
  int16_t accelY = 0;
  int16_t accelZ = 0;
  int16_t temperatureRaw = 0;
  int16_t gyroX = 0;
  int16_t gyroY = 0;
  int16_t gyroZ = 0;
};

struct Vector3f {
  float x = 0.0f;
  float y = 0.0f;
  float z = 0.0f;

  Vector3f() = default;
  Vector3f(float xValue, float yValue, float zValue)
      : x(xValue), y(yValue), z(zValue) {}
};

enum class MotionLevel {
  kStill,
  kLight,
  kVigorous,
};

enum class BreathRejectReason {
  kNone,
  kWarmup,
  kMotionGated,
  kPeakNeedTrough,
  kPeakHalfTooShort,
  kTroughNeedPeak,
  kTroughHalfTooShort,
  kIntervalOutOfRange,
  kAmplitudeTooLow,
};

enum class CalibrationStage {
  kStillBaseline,
  kNormalInhale,
  kNormalExhale,
  kDeepInhale,
  kDeepExhale,
  kSighInhale,
  kSighExhale,
  kRuntime,
};

struct BreathState {
  bool hasBreathInterval = false;
  float breathIntervalSeconds = 0.0f;
  bool hasBreathRate = false;
  float breathRateBpm = 0.0f;
  bool hasInhaleSeconds = false;
  float inhaleSeconds = 0.0f;
  bool hasExhaleSeconds = false;
  float exhaleSeconds = 0.0f;
  uint32_t sighCount = 0;
  float breathSignalG = 0.0f;
  float breathAmplitudeG = 0.0f;
  float averageBreathIntervalSeconds = 0.0f;
  float averageInhaleSeconds = 0.0f;
  float averageExhaleSeconds = 0.0f;
  float averageAmplitudeG = 0.0f;
};

struct AxisRangeAccumulator {
  bool initialized = false;
  float minValues[3] = {0.0f, 0.0f, 0.0f};
  float maxValues[3] = {0.0f, 0.0f, 0.0f};

  void observe(const Vector3f& sample) {
    const float values[3] = {sample.x, sample.y, sample.z};
    if (!initialized) {
      initialized = true;
      for (uint8_t index = 0; index < 3; ++index) {
        minValues[index] = values[index];
        maxValues[index] = values[index];
      }
      return;
    }

    for (uint8_t index = 0; index < 3; ++index) {
      if (values[index] < minValues[index]) {
        minValues[index] = values[index];
      }
      if (values[index] > maxValues[index]) {
        maxValues[index] = values[index];
      }
    }
  }

  float rangeForAxis(uint8_t axisIndex) const {
    if (!initialized || axisIndex > 2) {
      return 0.0f;
    }
    return maxValues[axisIndex] - minValues[axisIndex];
  }

  uint8_t dominantAxisIndex() const {
    float bestRange = -1.0f;
    uint8_t bestIndex = 2;
    for (uint8_t index = 0; index < 3; ++index) {
      const float currentRange = rangeForAxis(index);
      if (currentRange > bestRange) {
        bestRange = currentRange;
        bestIndex = index;
      }
    }
    return bestIndex;
  }
};

struct MotionAccumulator {
  uint32_t sampleCount = 0;
  float gyroSum = 0.0f;
  float gyroMax = 0.0f;
  float dynamicAccelSum = 0.0f;
  float dynamicAccelMax = 0.0f;

  void observe(float gyroNormDps, float dynamicAccelNormG) {
    ++sampleCount;
    gyroSum += gyroNormDps;
    dynamicAccelSum += dynamicAccelNormG;
    if (gyroNormDps > gyroMax) {
      gyroMax = gyroNormDps;
    }
    if (dynamicAccelNormG > dynamicAccelMax) {
      dynamicAccelMax = dynamicAccelNormG;
    }
  }

  float gyroMean() const {
    return sampleCount == 0 ? 0.0f : gyroSum / static_cast<float>(sampleCount);
  }

  float dynamicAccelMean() const {
    return sampleCount == 0 ? 0.0f : dynamicAccelSum / static_cast<float>(sampleCount);
  }
};

struct SignalAccumulator {
  uint32_t sampleCount = 0;
  float signedSum = 0.0f;
  float absoluteSum = 0.0f;
  float minValue = 0.0f;
  float maxValue = 0.0f;
  bool initialized = false;

  void observe(float value) {
    ++sampleCount;
    signedSum += value;
    absoluteSum += fabsf(value);

    if (!initialized) {
      initialized = true;
      minValue = value;
      maxValue = value;
      return;
    }

    if (value < minValue) {
      minValue = value;
    }
    if (value > maxValue) {
      maxValue = value;
    }
  }

  float mean() const {
    return sampleCount == 0 ? 0.0f : signedSum / static_cast<float>(sampleCount);
  }

  float meanAbsolute() const {
    return sampleCount == 0 ? 0.0f : absoluteSum / static_cast<float>(sampleCount);
  }

  float peakToPeak() const {
    return initialized ? maxValue - minValue : 0.0f;
  }
};

struct PersonalProfile {
  bool ready = false;
  uint8_t lockedAxisIndex = 2;
  char lockedAxis = 'z';
  float normalAmplitudeG = 0.0f;
  float deepAmplitudeG = 0.0f;
  float sighAmplitudeG = 0.0f;
  float normalPhaseDeltaG = 0.0f;
  float deepPhaseDeltaG = 0.0f;
  float sighPhaseDeltaG = 0.0f;
  float amplitudeThresholdG = kFallbackAmplitudeThresholdG;
  float stillGyroThresholdDps = 12.0f;
  float lightGyroThresholdDps = 35.0f;
  float vigorousGyroThresholdDps = 120.0f;
  float stillDynamicAccelThresholdG = 0.015f;
  float lightDynamicAccelThresholdG = 0.08f;
  float vigorousDynamicAccelThresholdG = 0.22f;
  unsigned long minHalfBreathMs = kDefaultMinHalfBreathMs;
  unsigned long minBreathIntervalMs = kDefaultMinBreathIntervalMs;
  unsigned long maxBreathIntervalMs = kDefaultMaxBreathIntervalMs;
  unsigned long expectedNormalIntervalMs = kNormalInhalePromptMs + kNormalExhalePromptMs;
  unsigned long expectedInhaleMs = kNormalInhalePromptMs;
  unsigned long expectedExhaleMs = kNormalExhalePromptMs;
  unsigned long sighExhaleThresholdMs = 4500;
  unsigned long sighIntervalThresholdMs = 6500;
  float sighAmplitudeThresholdG = 0.02f;
  float acceptanceLockRatio = kAcceptanceLockRatio;
};

struct RuntimeState {
  bool sensorReady = false;
  bool runtimeLogPaused = true;
  uint8_t activeAddress = 0;
  unsigned long startedAtMs = 0;
  unsigned long lastSampleAtMs = 0;
  unsigned long lastReconnectAtMs = 0;
  unsigned long lastLogAtMs = 0;
  uint32_t sampleIndex = 0;
  Vector3f gravityEstimateG = Vector3f(0.0f, 0.0f, 1.0f);

  CalibrationStage calibrationStage = CalibrationStage::kStillBaseline;
  unsigned long calibrationStageStartedAtMs = 0;
  bool calibrationPromptPrinted = false;
  uint8_t normalCycleIndex = 0;
  uint8_t deepCycleIndex = 0;
  uint8_t sighCycleIndex = 0;
  MotionAccumulator stillMotionStats;
  AxisRangeAccumulator normalAxisStats;
  AxisRangeAccumulator deepAxisStats;
  AxisRangeAccumulator sighAxisStats;
  AxisRangeAccumulator combinedAxisStats;
  SignalAccumulator normalSignalStats;
  SignalAccumulator normalInhaleSignalStats;
  SignalAccumulator normalExhaleSignalStats;
  SignalAccumulator deepSignalStats;
  SignalAccumulator deepInhaleSignalStats;
  SignalAccumulator deepExhaleSignalStats;
  SignalAccumulator sighSignalStats;
  SignalAccumulator sighInhaleSignalStats;
  SignalAccumulator sighExhaleSignalStats;
  PersonalProfile profile;

  float breathBaselineG = 0.0f;
  float breathFilteredG = 0.0f;
  float breathDetectionFilteredG = 0.0f;
  float previousBreathDetectionFilteredG = 0.0f;
  float previousBreathFilteredG = 0.0f;
  float previousBreathSlope = 0.0f;
  bool detectorPrimed = false;
  MotionLevel motionLevel = MotionLevel::kStill;
  float accelNormG = 1.0f;
  float dynamicAccelNormG = 0.0f;
  float gyroNormDps = 0.0f;
  float pitchDeg = 0.0f;
  float rollDeg = 0.0f;
  float breathCarrierG = 0.0f;
  float breathDetrendedG = 0.0f;
  float currentBreathSlopeG = 0.0f;
  unsigned long lastPeakAtMs = 0;
  unsigned long lastTroughAtMs = 0;
  float lastPeakValueG = 0.0f;
  float lastTroughValueG = 0.0f;
  bool hasPeak = false;
  bool hasTrough = false;
  float averageBreathIntervalMs = 0.0f;
  float averageInhaleMs = 0.0f;
  float averageExhaleMs = 0.0f;
  float averageAmplitudeG = 0.0f;
  float latestBreathIntervalMs = 0.0f;
  float latestInhaleMs = 0.0f;
  float latestExhaleMs = 0.0f;
  float latestAmplitudeG = 0.0f;
  uint32_t averagedBreathCount = 0;
  uint32_t sighCount = 0;
  unsigned long lastSighAtMs = 0;
  uint32_t detectedPeakCount = 0;
  uint32_t detectedTroughCount = 0;
  uint32_t acceptedCycleCount = 0;
  unsigned long lastAcceptedCycleAtMs = 0;
  BreathRejectReason lastRejectReason = BreathRejectReason::kNone;
  unsigned long lastRejectDurationMs = 0;
  float lastRejectAmplitudeG = 0.0f;
};

RuntimeState runtimeState;

float squaref(float value) {
  return value * value;
}

float vectorNorm(const Vector3f& value) {
  return sqrtf(squaref(value.x) + squaref(value.y) + squaref(value.z));
}

Vector3f normalizeVector(const Vector3f& value) {
  const float norm = vectorNorm(value);
  if (norm <= 0.0001f) {
    return Vector3f(0.0f, 0.0f, 1.0f);
  }
  return Vector3f(value.x / norm, value.y / norm, value.z / norm);
}

float maxFloat(float left, float right) {
  return left > right ? left : right;
}

float minFloat(float left, float right) {
  return left < right ? left : right;
}

float boolToFloat(bool value) {
  return value ? 1.0f : 0.0f;
}

float maxFloat3(float first, float second, float third) {
  return maxFloat(maxFloat(first, second), third);
}

unsigned long maxUnsignedLong(unsigned long left, unsigned long right) {
  return left > right ? left : right;
}

unsigned long clampUnsignedLong(unsigned long value, unsigned long minValue, unsigned long maxValue) {
  if (value < minValue) {
    return minValue;
  }
  if (value > maxValue) {
    return maxValue;
  }
  return value;
}

float updateAverage(float previousAverage, uint32_t sampleCount, float value) {
  if (sampleCount == 0) {
    return value;
  }
  return previousAverage + (value - previousAverage) / static_cast<float>(sampleCount + 1);
}

float computeExtremumConfirmDeltaG() {
  return maxFloat(0.0035f, runtimeState.profile.amplitudeThresholdG * 0.45f);
}

char axisChar(uint8_t axisIndex) {
  switch (axisIndex) {
    case 0:
      return 'x';
    case 1:
      return 'y';
    default:
      return 'z';
  }
}

float axisValue(const Vector3f& value, uint8_t axisIndex) {
  switch (axisIndex) {
    case 0:
      return value.x;
    case 1:
      return value.y;
    default:
      return value.z;
  }
}

float convertTemperatureCelsius(int16_t rawTemperature) {
  return static_cast<float>(rawTemperature) / 340.0f + 36.53f;
}

float convertAccelToG(int16_t rawAcceleration) {
  return static_cast<float>(rawAcceleration) / kAccelLsbPerG;
}

float convertGyroToDps(int16_t rawGyro) {
  return static_cast<float>(rawGyro) / kGyroLsbPerDps;
}

const char* motionLevelToText(MotionLevel level) {
  switch (level) {
    case MotionLevel::kStill:
      return "still";
    case MotionLevel::kLight:
      return "light";
    case MotionLevel::kVigorous:
      return "vigorous";
  }
  return "unknown";
}

const char* rejectReasonToText(BreathRejectReason reason) {
  switch (reason) {
    case BreathRejectReason::kNone:
      return "none";
    case BreathRejectReason::kWarmup:
      return "warmup";
    case BreathRejectReason::kMotionGated:
      return "motion_gated";
    case BreathRejectReason::kPeakNeedTrough:
      return "peak_need_trough";
    case BreathRejectReason::kPeakHalfTooShort:
      return "peak_half_short";
    case BreathRejectReason::kTroughNeedPeak:
      return "trough_need_peak";
    case BreathRejectReason::kTroughHalfTooShort:
      return "trough_half_short";
    case BreathRejectReason::kIntervalOutOfRange:
      return "interval_out_of_range";
    case BreathRejectReason::kAmplitudeTooLow:
      return "amplitude_too_low";
  }
  return "unknown";
}

uint8_t motionLevelToCode(MotionLevel level) {
  switch (level) {
    case MotionLevel::kStill:
      return 0;
    case MotionLevel::kLight:
      return 1;
    case MotionLevel::kVigorous:
      return 2;
  }
  return 255;
}

uint8_t rejectReasonToCode(BreathRejectReason reason) {
  switch (reason) {
    case BreathRejectReason::kNone:
      return 0;
    case BreathRejectReason::kWarmup:
      return 1;
    case BreathRejectReason::kMotionGated:
      return 2;
    case BreathRejectReason::kPeakNeedTrough:
      return 3;
    case BreathRejectReason::kPeakHalfTooShort:
      return 4;
    case BreathRejectReason::kTroughNeedPeak:
      return 5;
    case BreathRejectReason::kTroughHalfTooShort:
      return 6;
    case BreathRejectReason::kIntervalOutOfRange:
      return 7;
    case BreathRejectReason::kAmplitudeTooLow:
      return 8;
  }
  return 255;
}

const char* calibrationStageToText(CalibrationStage stage) {
  switch (stage) {
    case CalibrationStage::kStillBaseline:
      return "静止基线";
    case CalibrationStage::kNormalInhale:
      return "正常呼吸-吸气";
    case CalibrationStage::kNormalExhale:
      return "正常呼吸-呼气";
    case CalibrationStage::kDeepInhale:
      return "深呼吸-吸气";
    case CalibrationStage::kDeepExhale:
      return "深呼吸-呼气";
    case CalibrationStage::kSighInhale:
      return "叹气-吸气";
    case CalibrationStage::kSighExhale:
      return "叹气-长呼气";
    case CalibrationStage::kRuntime:
      return "运行模式";
  }
  return "未知阶段";
}

unsigned long stageDurationMs(CalibrationStage stage) {
  switch (stage) {
    case CalibrationStage::kStillBaseline:
      return kCalibrationStillMs;
    case CalibrationStage::kNormalInhale:
      return kNormalInhalePromptMs;
    case CalibrationStage::kNormalExhale:
      return kNormalExhalePromptMs;
    case CalibrationStage::kDeepInhale:
      return kDeepInhalePromptMs;
    case CalibrationStage::kDeepExhale:
      return kDeepExhalePromptMs;
    case CalibrationStage::kSighInhale:
      return kSighInhalePromptMs;
    case CalibrationStage::kSighExhale:
      return kSighExhalePromptMs;
    case CalibrationStage::kRuntime:
      return 0;
  }
  return 0;
}

unsigned long computeAcceptanceLockMs() {
  float referenceIntervalMs = runtimeState.latestBreathIntervalMs;
  if (referenceIntervalMs <= 0.0f) {
    referenceIntervalMs = runtimeState.averageBreathIntervalMs;
  }
  if (referenceIntervalMs <= 0.0f) {
    referenceIntervalMs = static_cast<float>(runtimeState.profile.expectedNormalIntervalMs);
  }

  return clampUnsignedLong(
      static_cast<unsigned long>(referenceIntervalMs * runtimeState.profile.acceptanceLockRatio),
      kAcceptanceLockMinMs,
      kAcceptanceLockMaxMs);
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

void resetRuntimeDetectorState() {
  runtimeState.runtimeLogPaused = true;
  runtimeState.breathBaselineG = 0.0f;
  runtimeState.breathFilteredG = 0.0f;
  runtimeState.breathDetectionFilteredG = 0.0f;
  runtimeState.previousBreathDetectionFilteredG = 0.0f;
  runtimeState.breathDetrendedG = 0.0f;
  runtimeState.currentBreathSlopeG = 0.0f;
  runtimeState.previousBreathFilteredG = 0.0f;
  runtimeState.previousBreathSlope = 0.0f;
  runtimeState.detectorPrimed = false;
  runtimeState.lastPeakAtMs = 0;
  runtimeState.lastTroughAtMs = 0;
  runtimeState.lastPeakValueG = 0.0f;
  runtimeState.lastTroughValueG = 0.0f;
  runtimeState.hasPeak = false;
  runtimeState.hasTrough = false;
  runtimeState.averageBreathIntervalMs = 0.0f;
  runtimeState.averageInhaleMs = 0.0f;
  runtimeState.averageExhaleMs = 0.0f;
  runtimeState.averageAmplitudeG = 0.0f;
  runtimeState.latestBreathIntervalMs = 0.0f;
  runtimeState.latestInhaleMs = 0.0f;
  runtimeState.latestExhaleMs = 0.0f;
  runtimeState.latestAmplitudeG = 0.0f;
  runtimeState.averagedBreathCount = 0;
  runtimeState.sighCount = 0;
  runtimeState.lastSighAtMs = 0;
  runtimeState.detectedPeakCount = 0;
  runtimeState.detectedTroughCount = 0;
  runtimeState.acceptedCycleCount = 0;
  runtimeState.lastAcceptedCycleAtMs = 0;
  runtimeState.lastRejectReason = BreathRejectReason::kNone;
  runtimeState.lastRejectDurationMs = 0;
  runtimeState.lastRejectAmplitudeG = 0.0f;
}

void resetCalibrationState(unsigned long nowMs) {
  runtimeState.calibrationStage = CalibrationStage::kStillBaseline;
  runtimeState.calibrationStageStartedAtMs = nowMs;
  runtimeState.calibrationPromptPrinted = false;
  runtimeState.normalCycleIndex = 0;
  runtimeState.deepCycleIndex = 0;
  runtimeState.sighCycleIndex = 0;
  runtimeState.stillMotionStats = MotionAccumulator();
  runtimeState.normalAxisStats = AxisRangeAccumulator();
  runtimeState.deepAxisStats = AxisRangeAccumulator();
  runtimeState.sighAxisStats = AxisRangeAccumulator();
  runtimeState.combinedAxisStats = AxisRangeAccumulator();
  runtimeState.normalSignalStats = SignalAccumulator();
  runtimeState.normalInhaleSignalStats = SignalAccumulator();
  runtimeState.normalExhaleSignalStats = SignalAccumulator();
  runtimeState.deepSignalStats = SignalAccumulator();
  runtimeState.deepInhaleSignalStats = SignalAccumulator();
  runtimeState.deepExhaleSignalStats = SignalAccumulator();
  runtimeState.sighSignalStats = SignalAccumulator();
  runtimeState.sighInhaleSignalStats = SignalAccumulator();
  runtimeState.sighExhaleSignalStats = SignalAccumulator();
  runtimeState.profile = PersonalProfile();
}

bool tryInitializeAt(uint8_t address) {
  if (!probeAddress(address)) {
    return false;
  }

  uint8_t whoAmI = 0;
  if (!readRegister(address, kRegisterWhoAmI, whoAmI)) {
    Serial.printf("[mpu6050-cal] addr=0x%02X | WHO_AM_I read failed\n", address);
    return false;
  }

  Serial.printf("[mpu6050-cal] addr=0x%02X | WHO_AM_I=0x%02X\n", address, whoAmI);
  if (whoAmI != kExpectedWhoAmI) {
    Serial.println("[mpu6050-cal] unexpected WHO_AM_I, continue probing other address");
    return false;
  }

  if (!writeRegister(address, kRegisterPowerManagement1, 0x00)) {
    Serial.println("[mpu6050-cal] wake-up write failed");
    return false;
  }

  delay(100);
  runtimeState.activeAddress = address;
  runtimeState.sensorReady = true;
  runtimeState.startedAtMs = millis();
  runtimeState.gravityEstimateG = Vector3f(0.0f, 0.0f, 1.0f);
  resetRuntimeDetectorState();
  resetCalibrationState(runtimeState.startedAtMs);
  Serial.printf("[mpu6050-cal] init ok | active_addr=0x%02X\n", runtimeState.activeAddress);
  return true;
}

void tryInitializeSensor() {
  runtimeState.sensorReady = false;
  runtimeState.activeAddress = 0;

  if (tryInitializeAt(kMpu6050AddressLow)) {
    return;
  }
  if (tryInitializeAt(kMpu6050AddressHigh)) {
    return;
  }

  Serial.println("[mpu6050-cal] no valid device found at 0x68 or 0x69");
}

MotionLevel classifyMotionLevel(float gyroNormDps, float dynamicAccelNormG) {
  const float stillGyroThreshold = runtimeState.profile.ready
      ? runtimeState.profile.stillGyroThresholdDps
      : 12.0f;
  const float lightGyroThreshold = runtimeState.profile.ready
      ? runtimeState.profile.lightGyroThresholdDps
      : 35.0f;
  const float vigorousGyroThreshold = runtimeState.profile.ready
      ? runtimeState.profile.vigorousGyroThresholdDps
      : 120.0f;
  const float stillDynamicAccelThreshold = runtimeState.profile.ready
      ? runtimeState.profile.stillDynamicAccelThresholdG
      : 0.015f;
  const float lightDynamicAccelThreshold = runtimeState.profile.ready
      ? runtimeState.profile.lightDynamicAccelThresholdG
      : 0.08f;
  const float vigorousDynamicAccelThreshold = runtimeState.profile.ready
      ? runtimeState.profile.vigorousDynamicAccelThresholdG
      : 0.22f;

  if (gyroNormDps <= stillGyroThreshold && dynamicAccelNormG <= stillDynamicAccelThreshold) {
    return MotionLevel::kStill;
  }
  if (gyroNormDps <= lightGyroThreshold && dynamicAccelNormG <= lightDynamicAccelThreshold) {
    return MotionLevel::kLight;
  }
  if (gyroNormDps <= vigorousGyroThreshold && dynamicAccelNormG <= vigorousDynamicAccelThreshold) {
    return MotionLevel::kLight;
  }
  return MotionLevel::kVigorous;
}

float selectRespirationCarrier(const Vector3f& accelG, const Vector3f& gravityDirection) {
  if (runtimeState.profile.ready) {
    return axisValue(accelG, runtimeState.profile.lockedAxisIndex);
  }

  const float absGravityX = fabsf(gravityDirection.x);
  const float absGravityY = fabsf(gravityDirection.y);
  const float absGravityZ = fabsf(gravityDirection.z);
  if (absGravityX >= absGravityY && absGravityX >= absGravityZ) {
    return accelG.x;
  }
  if (absGravityY >= absGravityX && absGravityY >= absGravityZ) {
    return accelG.y;
  }
  return accelG.z;
}

void printCalibrationPrompt() {
  if (runtimeState.calibrationPromptPrinted) {
    return;
  }

  runtimeState.calibrationPromptPrinted = true;
  switch (runtimeState.calibrationStage) {
    case CalibrationStage::kStillBaseline:
      Serial.println("[guide] 阶段 1/4 | 静止基线 | 请保持静止并正常呼吸 10 秒");
      break;
    case CalibrationStage::kNormalInhale:
      Serial.printf("[guide] 阶段 2/4 | 正常呼吸 %u/%u | 吸气 2 秒\n",
                    static_cast<unsigned>(runtimeState.normalCycleIndex + 1),
                    static_cast<unsigned>(kNormalCycles));
      break;
    case CalibrationStage::kNormalExhale:
      Serial.printf("[guide] 阶段 2/4 | 正常呼吸 %u/%u | 呼气 3 秒\n",
                    static_cast<unsigned>(runtimeState.normalCycleIndex + 1),
                    static_cast<unsigned>(kNormalCycles));
      break;
    case CalibrationStage::kDeepInhale:
      Serial.printf("[guide] 阶段 3/4 | 深呼吸 %u/%u | 深吸气 3 秒\n",
                    static_cast<unsigned>(runtimeState.deepCycleIndex + 1),
                    static_cast<unsigned>(kDeepCycles));
      break;
    case CalibrationStage::kDeepExhale:
      Serial.printf("[guide] 阶段 3/4 | 深呼吸 %u/%u | 深呼气 4 秒\n",
                    static_cast<unsigned>(runtimeState.deepCycleIndex + 1),
                    static_cast<unsigned>(kDeepCycles));
      break;
    case CalibrationStage::kSighInhale:
      Serial.printf("[guide] 阶段 4/4 | 叹气 %u/%u | 吸气 2 秒\n",
                    static_cast<unsigned>(runtimeState.sighCycleIndex + 1),
                    static_cast<unsigned>(kSighCycles));
      break;
    case CalibrationStage::kSighExhale:
      Serial.printf("[guide] 阶段 4/4 | 叹气 %u/%u | 长呼气 6 秒\n",
                    static_cast<unsigned>(runtimeState.sighCycleIndex + 1),
                    static_cast<unsigned>(kSighCycles));
      break;
    case CalibrationStage::kRuntime:
      Serial.println("[guide] 校准完成，已进入运行模式");
      break;
  }
}

void enterCalibrationStage(CalibrationStage stage, unsigned long nowMs) {
  runtimeState.calibrationStage = stage;
  runtimeState.calibrationStageStartedAtMs = nowMs;
  runtimeState.calibrationPromptPrinted = false;
}

void finalizeCalibration(unsigned long nowMs) {
  const uint8_t axisIndex = runtimeState.combinedAxisStats.dominantAxisIndex();
  PersonalProfile profile;
  profile.ready = true;
  profile.lockedAxisIndex = axisIndex;
  profile.lockedAxis = axisChar(axisIndex);
  const float normalAxisRangeG = runtimeState.normalAxisStats.rangeForAxis(axisIndex);
  const float deepAxisRangeG = runtimeState.deepAxisStats.rangeForAxis(axisIndex);
  const float sighAxisRangeG = runtimeState.sighAxisStats.rangeForAxis(axisIndex);
  const float normalSignalRangeG = runtimeState.normalSignalStats.peakToPeak();
  const float deepSignalRangeG = runtimeState.deepSignalStats.peakToPeak();
  const float sighSignalRangeG = runtimeState.sighSignalStats.peakToPeak();
  profile.normalPhaseDeltaG = fabsf(runtimeState.normalInhaleSignalStats.mean() - runtimeState.normalExhaleSignalStats.mean());
  profile.deepPhaseDeltaG = fabsf(runtimeState.deepInhaleSignalStats.mean() - runtimeState.deepExhaleSignalStats.mean());
  profile.sighPhaseDeltaG = fabsf(runtimeState.sighInhaleSignalStats.mean() - runtimeState.sighExhaleSignalStats.mean());
    const float normalSignalCapG = maxFloat(normalAxisRangeG * 1.20f, profile.normalPhaseDeltaG * 3.20f);
    const float deepSignalCapG = maxFloat(deepAxisRangeG * 1.20f, profile.deepPhaseDeltaG * 3.20f);
    const float sighSignalCapG = maxFloat(sighAxisRangeG * 1.20f, profile.sighPhaseDeltaG * 3.20f);
    const float normalEffectiveSignalG = maxFloat(minFloat(normalSignalRangeG, normalSignalCapG), profile.normalPhaseDeltaG * 1.80f);
    const float deepEffectiveSignalG = maxFloat(minFloat(deepSignalRangeG, deepSignalCapG), profile.deepPhaseDeltaG * 1.80f);
    const float sighEffectiveSignalG = maxFloat(minFloat(sighSignalRangeG, sighSignalCapG), profile.sighPhaseDeltaG * 1.80f);
  profile.normalAmplitudeG = normalEffectiveSignalG;
  profile.deepAmplitudeG = deepEffectiveSignalG;
  profile.sighAmplitudeG = sighEffectiveSignalG;
  profile.amplitudeThresholdG = maxFloat3(
      0.0025f,
      profile.normalAmplitudeG * 0.18f,
      profile.deepAmplitudeG * 0.10f);

  const float stillGyroMean = runtimeState.stillMotionStats.gyroMean();
  const float stillGyroMax = runtimeState.stillMotionStats.gyroMax;
  const float stillDynamicMean = runtimeState.stillMotionStats.dynamicAccelMean();
  const float stillDynamicMax = runtimeState.stillMotionStats.dynamicAccelMax;
  profile.stillGyroThresholdDps = maxFloat(12.0f, stillGyroMax * 1.15f);
  profile.lightGyroThresholdDps = maxFloat(maxFloat(24.0f, stillGyroMean * 2.4f), stillGyroMax * 1.6f);
  profile.vigorousGyroThresholdDps = maxFloat(90.0f, profile.lightGyroThresholdDps * 2.8f);
  profile.stillDynamicAccelThresholdG = maxFloat(0.015f, stillDynamicMax * 1.2f);
  profile.lightDynamicAccelThresholdG = maxFloat(maxFloat(0.04f, stillDynamicMean * 2.4f), stillDynamicMax * 1.8f);
  profile.vigorousDynamicAccelThresholdG = maxFloat(0.18f, profile.lightDynamicAccelThresholdG * 2.8f);

  profile.expectedInhaleMs = kNormalInhalePromptMs;
  profile.expectedExhaleMs = kNormalExhalePromptMs;
  profile.expectedNormalIntervalMs = kNormalInhalePromptMs + kNormalExhalePromptMs;
  profile.minHalfBreathMs = maxUnsignedLong(360UL, static_cast<unsigned long>(kNormalInhalePromptMs * 0.18f));
  profile.minBreathIntervalMs = maxUnsignedLong(900UL, static_cast<unsigned long>(profile.expectedNormalIntervalMs * 0.20f));
  profile.maxBreathIntervalMs = kDefaultMaxBreathIntervalMs;
  profile.sighExhaleThresholdMs = maxUnsignedLong(4500UL, static_cast<unsigned long>(profile.expectedExhaleMs * 1.7f));
  profile.sighIntervalThresholdMs = maxUnsignedLong(6500UL, static_cast<unsigned long>(profile.expectedNormalIntervalMs * 1.35f));
  profile.sighAmplitudeThresholdG = maxFloat3(
      0.02f,
      profile.normalAmplitudeG * 1.30f,
      profile.deepAmplitudeG * 0.70f);

  runtimeState.profile = profile;
  resetRuntimeDetectorState();
  runtimeState.startedAtMs = nowMs;

  Serial.println();
  Serial.println("================ PROFILE READY ===============");
  Serial.print("locked_axis: ");
  Serial.println(runtimeState.profile.lockedAxis);
  Serial.print("normal_amplitude_g: ");
  Serial.println(runtimeState.profile.normalAmplitudeG, 4);
  Serial.print("normal_axis_range_g: ");
  Serial.println(normalAxisRangeG, 4);
  Serial.print("normal_signal_range_g: ");
  Serial.println(normalSignalRangeG, 4);
  Serial.print("normal_signal_cap_g: ");
  Serial.println(normalSignalCapG, 4);
  Serial.print("normal_phase_delta_g: ");
  Serial.println(runtimeState.profile.normalPhaseDeltaG, 4);
  Serial.print("deep_amplitude_g: ");
  Serial.println(runtimeState.profile.deepAmplitudeG, 4);
  Serial.print("deep_axis_range_g: ");
  Serial.println(deepAxisRangeG, 4);
  Serial.print("deep_signal_range_g: ");
  Serial.println(deepSignalRangeG, 4);
  Serial.print("deep_signal_cap_g: ");
  Serial.println(deepSignalCapG, 4);
  Serial.print("deep_phase_delta_g: ");
  Serial.println(runtimeState.profile.deepPhaseDeltaG, 4);
  Serial.print("sigh_amplitude_g: ");
  Serial.println(runtimeState.profile.sighAmplitudeG, 4);
  Serial.print("sigh_axis_range_g: ");
  Serial.println(sighAxisRangeG, 4);
  Serial.print("sigh_signal_range_g: ");
  Serial.println(sighSignalRangeG, 4);
  Serial.print("sigh_signal_cap_g: ");
  Serial.println(sighSignalCapG, 4);
  Serial.print("sigh_phase_delta_g: ");
  Serial.println(runtimeState.profile.sighPhaseDeltaG, 4);
  Serial.print("amplitude_threshold_g: ");
  Serial.println(runtimeState.profile.amplitudeThresholdG, 4);
  Serial.print("min_half_breath_ms: ");
  Serial.println(runtimeState.profile.minHalfBreathMs);
  Serial.print("min_breath_interval_ms: ");
  Serial.println(runtimeState.profile.minBreathIntervalMs);
  Serial.print("sigh_exhale_threshold_ms: ");
  Serial.println(runtimeState.profile.sighExhaleThresholdMs);
  Serial.println("==============================================");
  Serial.println("[resp] 运行期日志已暂停，等待第一条有效呼吸后自动恢复输出");

  enterCalibrationStage(CalibrationStage::kRuntime, nowMs);
}

void observeCalibrationSample(const Vector3f& accelG, float calibrationSignalG) {
  switch (runtimeState.calibrationStage) {
    case CalibrationStage::kStillBaseline:
      runtimeState.stillMotionStats.observe(runtimeState.gyroNormDps, runtimeState.dynamicAccelNormG);
      break;
    case CalibrationStage::kNormalInhale:
      runtimeState.normalSignalStats.observe(calibrationSignalG);
      runtimeState.normalInhaleSignalStats.observe(calibrationSignalG);
      runtimeState.normalAxisStats.observe(accelG);
      runtimeState.combinedAxisStats.observe(accelG);
      break;
    case CalibrationStage::kNormalExhale:
      runtimeState.normalSignalStats.observe(calibrationSignalG);
      runtimeState.normalExhaleSignalStats.observe(calibrationSignalG);
      runtimeState.normalAxisStats.observe(accelG);
      runtimeState.combinedAxisStats.observe(accelG);
      break;
    case CalibrationStage::kDeepInhale:
      runtimeState.deepSignalStats.observe(calibrationSignalG);
      runtimeState.deepInhaleSignalStats.observe(calibrationSignalG);
      runtimeState.deepAxisStats.observe(accelG);
      runtimeState.combinedAxisStats.observe(accelG);
      break;
    case CalibrationStage::kDeepExhale:
      runtimeState.deepSignalStats.observe(calibrationSignalG);
      runtimeState.deepExhaleSignalStats.observe(calibrationSignalG);
      runtimeState.deepAxisStats.observe(accelG);
      runtimeState.combinedAxisStats.observe(accelG);
      break;
    case CalibrationStage::kSighInhale:
      runtimeState.sighSignalStats.observe(calibrationSignalG);
      runtimeState.sighInhaleSignalStats.observe(calibrationSignalG);
      runtimeState.sighAxisStats.observe(accelG);
      runtimeState.combinedAxisStats.observe(accelG);
      break;
    case CalibrationStage::kSighExhale:
      runtimeState.sighSignalStats.observe(calibrationSignalG);
      runtimeState.sighExhaleSignalStats.observe(calibrationSignalG);
      runtimeState.sighAxisStats.observe(accelG);
      runtimeState.combinedAxisStats.observe(accelG);
      break;
    case CalibrationStage::kRuntime:
      break;
  }
}

void updateCalibration(unsigned long nowMs) {
  printCalibrationPrompt();
  const unsigned long elapsedMs = nowMs - runtimeState.calibrationStageStartedAtMs;
  if (elapsedMs < stageDurationMs(runtimeState.calibrationStage)) {
    return;
  }

  switch (runtimeState.calibrationStage) {
    case CalibrationStage::kStillBaseline:
      enterCalibrationStage(CalibrationStage::kNormalInhale, nowMs);
      break;
    case CalibrationStage::kNormalInhale:
      enterCalibrationStage(CalibrationStage::kNormalExhale, nowMs);
      break;
    case CalibrationStage::kNormalExhale:
      ++runtimeState.normalCycleIndex;
      if (runtimeState.normalCycleIndex < kNormalCycles) {
        enterCalibrationStage(CalibrationStage::kNormalInhale, nowMs);
      } else {
        enterCalibrationStage(CalibrationStage::kDeepInhale, nowMs);
      }
      break;
    case CalibrationStage::kDeepInhale:
      enterCalibrationStage(CalibrationStage::kDeepExhale, nowMs);
      break;
    case CalibrationStage::kDeepExhale:
      ++runtimeState.deepCycleIndex;
      if (runtimeState.deepCycleIndex < kDeepCycles) {
        enterCalibrationStage(CalibrationStage::kDeepInhale, nowMs);
      } else {
        enterCalibrationStage(CalibrationStage::kSighInhale, nowMs);
      }
      break;
    case CalibrationStage::kSighInhale:
      enterCalibrationStage(CalibrationStage::kSighExhale, nowMs);
      break;
    case CalibrationStage::kSighExhale:
      ++runtimeState.sighCycleIndex;
      if (runtimeState.sighCycleIndex < kSighCycles) {
        enterCalibrationStage(CalibrationStage::kSighInhale, nowMs);
      } else {
        finalizeCalibration(nowMs);
      }
      break;
    case CalibrationStage::kRuntime:
      break;
  }
}

void updateBreathAverages(unsigned long nowMs, float intervalMs, float inhaleMs, float exhaleMs, float amplitudeG) {
  runtimeState.latestBreathIntervalMs = intervalMs;
  runtimeState.latestInhaleMs = inhaleMs;
  runtimeState.latestExhaleMs = exhaleMs;
  runtimeState.latestAmplitudeG = amplitudeG;
  runtimeState.averageBreathIntervalMs = updateAverage(runtimeState.averageBreathIntervalMs, runtimeState.averagedBreathCount, intervalMs);
  runtimeState.averageInhaleMs = updateAverage(runtimeState.averageInhaleMs, runtimeState.averagedBreathCount, inhaleMs);
  runtimeState.averageExhaleMs = updateAverage(runtimeState.averageExhaleMs, runtimeState.averagedBreathCount, exhaleMs);
  runtimeState.averageAmplitudeG = updateAverage(runtimeState.averageAmplitudeG, runtimeState.averagedBreathCount, amplitudeG);
  ++runtimeState.averagedBreathCount;
  ++runtimeState.acceptedCycleCount;
  runtimeState.lastAcceptedCycleAtMs = nowMs;
  runtimeState.lastRejectReason = BreathRejectReason::kNone;
  runtimeState.lastRejectDurationMs = 0;
  runtimeState.lastRejectAmplitudeG = amplitudeG;

  if (runtimeState.runtimeLogPaused) {
    runtimeState.runtimeLogPaused = false;
    if (!project_config::kEnableMpu6050RespirationVofaStream) {
      Serial.println("[resp] 已检测到第一条有效呼吸，恢复运行期输出");
    }
  }
}

void maybeCountSigh(unsigned long nowMs, float intervalMs, float exhaleMs, float amplitudeG) {
  if (!runtimeState.profile.ready || runtimeState.averagedBreathCount < 2) {
    return;
  }

  if (nowMs - runtimeState.lastSighAtMs < 6000) {
    return;
  }

  const bool longExhale = exhaleMs >= static_cast<float>(runtimeState.profile.sighExhaleThresholdMs);
  const bool longInterval = intervalMs >= static_cast<float>(runtimeState.profile.sighIntervalThresholdMs);
  const bool deepAmplitude = amplitudeG >= runtimeState.profile.sighAmplitudeThresholdG;
  if (longExhale && (longInterval || deepAmplitude)) {
    ++runtimeState.sighCount;
    runtimeState.lastSighAtMs = nowMs;
  }
}

void acceptPeak(unsigned long nowMs, float valueG) {
  ++runtimeState.detectedPeakCount;

  if (runtimeState.hasPeak && (!runtimeState.hasTrough || runtimeState.lastPeakAtMs > runtimeState.lastTroughAtMs)) {
    if (valueG > runtimeState.lastPeakValueG) {
      runtimeState.lastPeakValueG = valueG;
    }
    runtimeState.lastRejectReason = BreathRejectReason::kPeakNeedTrough;
    runtimeState.lastRejectDurationMs = nowMs - runtimeState.lastPeakAtMs;
    return;
  }

  if (!runtimeState.hasTrough) {
    runtimeState.lastPeakAtMs = nowMs;
    runtimeState.lastPeakValueG = valueG;
    runtimeState.hasPeak = true;
    runtimeState.lastRejectReason = BreathRejectReason::kPeakNeedTrough;
    return;
  }

  const unsigned long inhaleMs = nowMs - runtimeState.lastTroughAtMs;
  if (runtimeState.lastPeakAtMs != 0 && nowMs - runtimeState.lastPeakAtMs < kMinExtremumGapMs) {
    runtimeState.lastRejectReason = BreathRejectReason::kPeakHalfTooShort;
    runtimeState.lastRejectDurationMs = nowMs - runtimeState.lastPeakAtMs;
    return;
  }
  if (inhaleMs < runtimeState.profile.minHalfBreathMs) {
    runtimeState.lastRejectReason = BreathRejectReason::kPeakHalfTooShort;
    runtimeState.lastRejectDurationMs = inhaleMs;
    return;
  }

  runtimeState.lastPeakAtMs = nowMs;
  runtimeState.lastPeakValueG = valueG;
  runtimeState.hasPeak = true;
}

void acceptTrough(unsigned long nowMs, float valueG) {
  ++runtimeState.detectedTroughCount;

  if (runtimeState.hasTrough && (!runtimeState.hasPeak || runtimeState.lastTroughAtMs > runtimeState.lastPeakAtMs)) {
    if (valueG < runtimeState.lastTroughValueG) {
      runtimeState.lastTroughValueG = valueG;
    }
    runtimeState.lastRejectReason = BreathRejectReason::kTroughNeedPeak;
    runtimeState.lastRejectDurationMs = nowMs - runtimeState.lastTroughAtMs;
    return;
  }

  if (!runtimeState.hasPeak) {
    runtimeState.lastTroughAtMs = nowMs;
    runtimeState.lastTroughValueG = valueG;
    runtimeState.hasTrough = true;
    runtimeState.lastRejectReason = BreathRejectReason::kTroughNeedPeak;
    return;
  }

  const unsigned long exhaleMs = nowMs - runtimeState.lastPeakAtMs;
  if (runtimeState.lastTroughAtMs != 0 && nowMs - runtimeState.lastTroughAtMs < kMinExtremumGapMs) {
    runtimeState.lastRejectReason = BreathRejectReason::kTroughHalfTooShort;
    runtimeState.lastRejectDurationMs = nowMs - runtimeState.lastTroughAtMs;
    return;
  }
  if (exhaleMs < runtimeState.profile.minHalfBreathMs) {
    runtimeState.lastRejectReason = BreathRejectReason::kTroughHalfTooShort;
    runtimeState.lastRejectDurationMs = exhaleMs;
    return;
  }

  const unsigned long previousTroughAtMs = runtimeState.lastTroughAtMs;
  const float previousTroughValueG = runtimeState.lastTroughValueG;
  runtimeState.lastTroughAtMs = nowMs;
  runtimeState.lastTroughValueG = valueG;
  runtimeState.hasTrough = true;

  if (previousTroughAtMs == 0 || previousTroughAtMs >= nowMs) {
    return;
  }

  const unsigned long intervalMs = nowMs - previousTroughAtMs;
  if (intervalMs < runtimeState.profile.minBreathIntervalMs || intervalMs > runtimeState.profile.maxBreathIntervalMs) {
    runtimeState.lastRejectReason = BreathRejectReason::kIntervalOutOfRange;
    runtimeState.lastRejectDurationMs = intervalMs;
    return;
  }

  if (runtimeState.motionLevel == MotionLevel::kVigorous) {
    runtimeState.lastRejectReason = BreathRejectReason::kMotionGated;
    runtimeState.lastRejectDurationMs = intervalMs;
    return;
  }

  const unsigned long acceptanceLockMs = computeAcceptanceLockMs();
  if (runtimeState.lastAcceptedCycleAtMs != 0 && nowMs - runtimeState.lastAcceptedCycleAtMs < acceptanceLockMs) {
    runtimeState.lastRejectReason = BreathRejectReason::kIntervalOutOfRange;
    runtimeState.lastRejectDurationMs = nowMs - runtimeState.lastAcceptedCycleAtMs;
    return;
  }

  const float inhaleMs = static_cast<float>(runtimeState.lastPeakAtMs - previousTroughAtMs);
  const float amplitudeG = runtimeState.lastPeakValueG - previousTroughValueG;
  if (amplitudeG < runtimeState.profile.amplitudeThresholdG) {
    runtimeState.lastRejectReason = BreathRejectReason::kAmplitudeTooLow;
    runtimeState.lastRejectAmplitudeG = amplitudeG;
    return;
  }

  updateBreathAverages(nowMs, static_cast<float>(intervalMs), inhaleMs, static_cast<float>(exhaleMs), amplitudeG);
  maybeCountSigh(nowMs, static_cast<float>(intervalMs), static_cast<float>(exhaleMs), amplitudeG);
}

void updateBreathDetector(unsigned long nowMs, float breathSignalG) {
  runtimeState.breathBaselineG += (breathSignalG - runtimeState.breathBaselineG) * kBreathBaselineAlpha;
  const float detrendedSignalG = breathSignalG - runtimeState.breathBaselineG;
  runtimeState.breathDetrendedG = detrendedSignalG;
  runtimeState.breathFilteredG += (detrendedSignalG - runtimeState.breathFilteredG) * kBreathSmoothAlpha;
  runtimeState.breathDetectionFilteredG +=
      (runtimeState.breathFilteredG - runtimeState.breathDetectionFilteredG) * kBreathDetectionLowPassAlpha;

  if (nowMs - runtimeState.startedAtMs < kBreathDetectorWarmupMs) {
    runtimeState.previousBreathDetectionFilteredG = runtimeState.breathDetectionFilteredG;
    runtimeState.previousBreathFilteredG = runtimeState.breathFilteredG;
    runtimeState.previousBreathSlope = 0.0f;
    runtimeState.currentBreathSlopeG = 0.0f;
    runtimeState.lastRejectReason = BreathRejectReason::kWarmup;
    return;
  }

  const float slope = runtimeState.breathDetectionFilteredG - runtimeState.previousBreathDetectionFilteredG;
  runtimeState.currentBreathSlopeG = slope;
  if (!runtimeState.detectorPrimed) {
    runtimeState.previousBreathDetectionFilteredG = runtimeState.breathDetectionFilteredG;
    runtimeState.previousBreathFilteredG = runtimeState.breathFilteredG;
    runtimeState.previousBreathSlope = slope;
    runtimeState.detectorPrimed = true;
    return;
  }

  if (runtimeState.motionLevel != MotionLevel::kVigorous) {
    const float extremumConfirmDeltaG = computeExtremumConfirmDeltaG();
    if (runtimeState.previousBreathSlope > 0.0f && slope <= 0.0f) {
      bool shouldAcceptPeak = true;
      if (runtimeState.hasTrough) {
        shouldAcceptPeak = (runtimeState.previousBreathDetectionFilteredG - runtimeState.lastTroughValueG) >= extremumConfirmDeltaG;
      } else {
        shouldAcceptPeak = runtimeState.previousBreathDetectionFilteredG >= extremumConfirmDeltaG;
      }

      if (shouldAcceptPeak) {
        acceptPeak(nowMs - kSampleIntervalMs, runtimeState.previousBreathDetectionFilteredG);
      }
    } else if (runtimeState.previousBreathSlope < 0.0f && slope >= 0.0f) {
      bool shouldAcceptTrough = true;
      if (runtimeState.hasPeak) {
        shouldAcceptTrough = (runtimeState.lastPeakValueG - runtimeState.previousBreathDetectionFilteredG) >= extremumConfirmDeltaG;
      } else {
        shouldAcceptTrough = (-runtimeState.previousBreathDetectionFilteredG) >= extremumConfirmDeltaG;
      }

      if (shouldAcceptTrough) {
        acceptTrough(nowMs - kSampleIntervalMs, runtimeState.previousBreathDetectionFilteredG);
      }
    }
  } else {
    runtimeState.lastRejectReason = BreathRejectReason::kMotionGated;
  }

  runtimeState.previousBreathDetectionFilteredG = runtimeState.breathDetectionFilteredG;
  runtimeState.previousBreathFilteredG = runtimeState.breathFilteredG;
  runtimeState.previousBreathSlope = slope;
}

BreathState buildBreathState(unsigned long nowMs) {
  BreathState state;
  state.sighCount = runtimeState.sighCount;
  state.breathSignalG = runtimeState.breathFilteredG;

  if (runtimeState.averagedBreathCount == 0) {
    return state;
  }

  state.averageBreathIntervalSeconds = runtimeState.averageBreathIntervalMs / 1000.0f;
  state.averageInhaleSeconds = runtimeState.averageInhaleMs / 1000.0f;
  state.averageExhaleSeconds = runtimeState.averageExhaleMs / 1000.0f;
  state.averageAmplitudeG = runtimeState.averageAmplitudeG;

  const bool latestBreathFresh = runtimeState.lastAcceptedCycleAtMs != 0 &&
      nowMs - runtimeState.lastAcceptedCycleAtMs <= kBreathDisplayStaleMs;
  state.hasBreathInterval = latestBreathFresh && runtimeState.latestBreathIntervalMs > 0.0f;
  state.breathIntervalSeconds = runtimeState.latestBreathIntervalMs / 1000.0f;
  state.hasBreathRate = latestBreathFresh && runtimeState.latestBreathIntervalMs > 0.0f;
  if (state.hasBreathRate) {
    state.breathRateBpm = 60000.0f / runtimeState.latestBreathIntervalMs;
  }
  state.hasInhaleSeconds = latestBreathFresh && runtimeState.latestInhaleMs > 0.0f;
  if (state.hasInhaleSeconds) {
    state.inhaleSeconds = runtimeState.latestInhaleMs / 1000.0f;
  }
  state.hasExhaleSeconds = latestBreathFresh && runtimeState.latestExhaleMs > 0.0f;
  if (state.hasExhaleSeconds) {
    state.exhaleSeconds = runtimeState.latestExhaleMs / 1000.0f;
  }
  state.breathAmplitudeG = latestBreathFresh ? runtimeState.latestAmplitudeG : 0.0f;
  return state;
}

void printFloatField(const char* label, bool valid, float value, uint8_t decimals = 2) {
  Serial.print(label);
  Serial.print(": ");
  if (valid) {
    Serial.println(value, decimals);
  } else {
    Serial.println("n/a");
  }
}

void printRuntimeStatus(unsigned long nowMs, const Mpu6050Sample& sample, const BreathState& breathState) {
  ++runtimeState.sampleIndex;

  Serial.println();
  Serial.println("================ MPU6050 RESP ================");
  Serial.print("sample: ");
  Serial.println(runtimeState.sampleIndex);
  Serial.print("uptime_ms: ");
  Serial.println(nowMs);
  Serial.print("addr: 0x");
  Serial.println(runtimeState.activeAddress, HEX);
  Serial.print("motion_level: ");
  Serial.println(motionLevelToText(runtimeState.motionLevel));

  Serial.println("-- raw --");
  Serial.printf("acc_raw: %d, %d, %d\n", sample.accelX, sample.accelY, sample.accelZ);
  Serial.printf("gyro_raw: %d, %d, %d\n", sample.gyroX, sample.gyroY, sample.gyroZ);
  printFloatField("temp_c", true, convertTemperatureCelsius(sample.temperatureRaw));

  Serial.println("-- engineering --");
  printFloatField("acc_norm_g", true, runtimeState.accelNormG, 3);
  printFloatField("dynamic_acc_norm_g", true, runtimeState.dynamicAccelNormG, 3);
  printFloatField("gyro_norm_dps", true, runtimeState.gyroNormDps, 2);
  printFloatField("pitch_deg", true, runtimeState.pitchDeg, 1);
  printFloatField("roll_deg", true, runtimeState.rollDeg, 1);

  Serial.println("-- breathing --");
  Serial.print("dominant_axis: ");
  Serial.println(runtimeState.profile.lockedAxis);
  printFloatField("breath_carrier_g", true, runtimeState.breathCarrierG, 4);
  printFloatField("breath_signal_g", true, breathState.breathSignalG, 4);
  printFloatField("breath_amplitude_g", breathState.breathAmplitudeG > 0.0f, breathState.breathAmplitudeG, 4);
  printFloatField("breath_interval_s", breathState.hasBreathInterval, breathState.breathIntervalSeconds, 2);
  printFloatField("breath_rate_bpm", breathState.hasBreathRate, breathState.breathRateBpm, 2);
  printFloatField("inhale_s", breathState.hasInhaleSeconds, breathState.inhaleSeconds, 2);
  printFloatField("exhale_s", breathState.hasExhaleSeconds, breathState.exhaleSeconds, 2);
  printFloatField("avg_interval_s", breathState.averageBreathIntervalSeconds > 0.0f, breathState.averageBreathIntervalSeconds, 2);
  printFloatField("avg_inhale_s", breathState.averageInhaleSeconds > 0.0f, breathState.averageInhaleSeconds, 2);
  printFloatField("avg_exhale_s", breathState.averageExhaleSeconds > 0.0f, breathState.averageExhaleSeconds, 2);
  Serial.print("detected_peaks: ");
  Serial.println(runtimeState.detectedPeakCount);
  Serial.print("detected_troughs: ");
  Serial.println(runtimeState.detectedTroughCount);
  Serial.print("accepted_cycles: ");
  Serial.println(runtimeState.acceptedCycleCount);
  Serial.print("last_reject: ");
  Serial.println(rejectReasonToText(runtimeState.lastRejectReason));
  printFloatField("last_reject_amp_g", runtimeState.lastRejectAmplitudeG > 0.0f, runtimeState.lastRejectAmplitudeG, 4);
  printFloatField("last_reject_duration_s", runtimeState.lastRejectDurationMs > 0, static_cast<float>(runtimeState.lastRejectDurationMs) / 1000.0f, 2);
  Serial.print("sigh_count: ");
  Serial.println(breathState.sighCount);
  Serial.println("==============================================");
}

void printRuntimeVofaFrame(unsigned long nowMs, const Mpu6050Sample& sample) {
  Serial.printf(
  "%lu,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%d,%d,%d,%d,%d,%d\n",
      nowMs,
      runtimeState.breathCarrierG,
      runtimeState.breathBaselineG,
      runtimeState.breathDetrendedG,
      runtimeState.breathFilteredG,
      runtimeState.currentBreathSlopeG,
      runtimeState.profile.amplitudeThresholdG,
      runtimeState.lastPeakValueG,
      runtimeState.lastTroughValueG,
      runtimeState.dynamicAccelNormG,
      runtimeState.gyroNormDps,
      static_cast<float>(motionLevelToCode(runtimeState.motionLevel)),
      static_cast<float>(rejectReasonToCode(runtimeState.lastRejectReason)),
      boolToFloat(runtimeState.hasPeak),
      boolToFloat(runtimeState.hasTrough),
      static_cast<float>(runtimeState.acceptedCycleCount),
      static_cast<float>(runtimeState.detectedPeakCount - runtimeState.detectedTroughCount),
      sample.accelX,
      sample.accelY,
      sample.accelZ,
      sample.gyroX,
      sample.gyroY,
      sample.gyroZ);
}

void updateMotionAndSignal(unsigned long nowMs, const Mpu6050Sample& sample) {
  const Vector3f accelG(
      convertAccelToG(sample.accelX),
      convertAccelToG(sample.accelY),
      convertAccelToG(sample.accelZ));
  const Vector3f gyroDps(
      convertGyroToDps(sample.gyroX),
      convertGyroToDps(sample.gyroY),
      convertGyroToDps(sample.gyroZ));

  runtimeState.gravityEstimateG.x += (accelG.x - runtimeState.gravityEstimateG.x) * kGravityEstimateAlpha;
  runtimeState.gravityEstimateG.y += (accelG.y - runtimeState.gravityEstimateG.y) * kGravityEstimateAlpha;
  runtimeState.gravityEstimateG.z += (accelG.z - runtimeState.gravityEstimateG.z) * kGravityEstimateAlpha;

  const Vector3f gravityDirection = normalizeVector(runtimeState.gravityEstimateG);
  runtimeState.breathCarrierG = selectRespirationCarrier(accelG, gravityDirection);
  runtimeState.accelNormG = vectorNorm(accelG);
  runtimeState.dynamicAccelNormG = fabsf(runtimeState.accelNormG - 1.0f);
  runtimeState.gyroNormDps = vectorNorm(gyroDps);
  runtimeState.motionLevel = classifyMotionLevel(runtimeState.gyroNormDps, runtimeState.dynamicAccelNormG);
  runtimeState.pitchDeg = atan2f(gravityDirection.x, sqrtf(squaref(gravityDirection.y) + squaref(gravityDirection.z))) * 180.0f / PI;
  runtimeState.rollDeg = atan2f(gravityDirection.y, gravityDirection.z) * 180.0f / PI;

  runtimeState.breathBaselineG += (runtimeState.breathCarrierG - runtimeState.breathBaselineG) * kBreathBaselineAlpha;
  const float calibrationDetrendedSignalG = runtimeState.breathCarrierG - runtimeState.breathBaselineG;
  runtimeState.breathDetrendedG = calibrationDetrendedSignalG;
  runtimeState.breathFilteredG += (calibrationDetrendedSignalG - runtimeState.breathFilteredG) * kBreathSmoothAlpha;

  observeCalibrationSample(accelG, runtimeState.breathFilteredG);
  if (runtimeState.calibrationStage == CalibrationStage::kRuntime) {
    updateBreathDetector(nowMs, runtimeState.breathCarrierG);
  }
}

}  // namespace

void setup() {
  Serial.begin(kSerialBaudRate);
  delay(kStartupDelayMs);

  Serial.println();
  Serial.println("[system] Single-IMU personalized calibration experiment starting on XIAO ESP32S3 / Plus");
  Serial.println("[system] Flow: still baseline -> guided normal breath -> guided deep breath -> guided sigh -> runtime");
  Serial.println("[system] Goal: learn personal thresholds instead of continuing to hard-tune global constants");
  logWiringGuide();

  Wire.begin(project_config::kI2cSdaPin, project_config::kI2cSclPin);
  Wire.setClock(project_config::kI2cClockHz);
  Serial.printf("[i2c] SDA=GPIO%u | SCL=GPIO%u | clock=%luHz\n",
                project_config::kI2cSdaPin,
                project_config::kI2cSclPin,
                static_cast<unsigned long>(project_config::kI2cClockHz));

  tryInitializeSensor();
}

void loop() {
  const unsigned long nowMs = millis();

  if (!runtimeState.sensorReady) {
    if (nowMs - runtimeState.lastReconnectAtMs < kReconnectIntervalMs) {
      return;
    }

    runtimeState.lastReconnectAtMs = nowMs;
    tryInitializeSensor();
    return;
  }

  if (nowMs - runtimeState.lastSampleAtMs < kSampleIntervalMs) {
    return;
  }
  runtimeState.lastSampleAtMs = nowMs;

  Mpu6050Sample sample;
  if (!readSample(runtimeState.activeAddress, sample)) {
    Serial.println("[mpu6050-cal] sample read failed, sensor will be re-probed");
    runtimeState.sensorReady = false;
    return;
  }

  updateMotionAndSignal(nowMs, sample);
  if (runtimeState.calibrationStage != CalibrationStage::kRuntime) {
    updateCalibration(nowMs);
  }

  if (runtimeState.calibrationStage != CalibrationStage::kRuntime) {
    return;
  }

  if (project_config::kEnableMpu6050RespirationVofaStream) {
    if (nowMs - runtimeState.lastLogAtMs < project_config::kMpu6050RespirationVofaStreamIntervalMs) {
      return;
    }
    runtimeState.lastLogAtMs = nowMs;
    printRuntimeVofaFrame(nowMs, sample);
    return;
  }

  if (runtimeState.runtimeLogPaused) {
    return;
  }

  if (nowMs - runtimeState.lastLogAtMs < kLogIntervalMs) {
    return;
  }
  runtimeState.lastLogAtMs = nowMs;
  printRuntimeStatus(nowMs, sample, buildBreathState(nowMs));
}