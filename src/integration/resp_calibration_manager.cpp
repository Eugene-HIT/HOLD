#include "resp_calibration_manager.h"

#include <cstring>
#include <math.h>

#include <Wire.h>

namespace hold_integration {
namespace {

constexpr uint8_t kMpuAddressLow = 0x68;
constexpr uint8_t kMpuAddressHigh = 0x69;
constexpr uint8_t kRegisterWhoAmI = 0x75;
constexpr uint8_t kRegisterPowerManagement1 = 0x6B;
constexpr uint8_t kRegisterAccelXoutH = 0x3B;
constexpr float kAccelLsbPerG = 16384.0f;
constexpr float kGyroLsbPerDps = 131.0f;
constexpr float kGravityEstimateAlpha = 0.02f;
constexpr float kBreathBaselineAlpha = 0.003f;
constexpr float kBreathSmoothAlpha = 0.18f;
constexpr float kBreathDetectionLowPassAlpha = 0.12f;
constexpr float kRespExtremumConfirmMinG = 0.0035f;
constexpr float kRespAmplitudeThresholdG = 0.0045f;
constexpr uint32_t kRespDetectorWarmupMs = 3000;
constexpr uint32_t kRespSampleIntervalMs = 20;
constexpr uint32_t kRespMinExtremumGapMs = 250;
constexpr uint32_t kRespMinHalfBreathMs = 560;
constexpr uint32_t kRespMinBreathIntervalMs = 1300;
constexpr uint32_t kRespMaxBreathIntervalMs = 10000;
constexpr uint32_t kRespDisplayStaleMs = 6000;
constexpr uint32_t kAxisSelectionSettleMs = 1200;

struct MpuSample {
  int16_t accelX = 0;
  int16_t accelY = 0;
  int16_t accelZ = 0;
  int16_t temperatureRaw = 0;
  int16_t gyroX = 0;
  int16_t gyroY = 0;
  int16_t gyroZ = 0;
};

CalibrationStatusSnapshot snapshot;
bool completedEventPending = false;
bool failedEventPending = false;
bool wasEnabled = false;
uint32_t calibrationStartedAtMs = 0;
uint32_t lastReconnectAtMs = 0;
uint8_t activeAddress = 0;
bool sensorReady = false;
float gravityX = 0.0f;
float gravityY = 0.0f;
float gravityZ = 1.0f;
uint8_t lockedAxisIndex = 2;
bool axisLocked = false;
float breathBaselineG = 0.0f;
float breathFilteredG = 0.0f;
float breathDetectionFilteredG = 0.0f;
float previousBreathDetectionFilteredG = 0.0f;
float previousBreathFilteredG = 0.0f;
uint32_t lastSampleAtMs = 0;
uint32_t startedAtMs = 0;
uint32_t lastPeakAtMs = 0;
uint32_t lastTroughAtMs = 0;
float lastPeakValueG = 0.0f;
float lastTroughValueG = 0.0f;
bool hasPeak = false;
bool hasTrough = false;
bool detectorPrimed = false;
bool respBeatMarkerPending = false;
uint32_t lastAcceptedCycleAtMs = 0;
float latestAmplitudeG = 0.0f;
float latestBreathIntervalMs = 0.0f;
uint32_t acceptedCycleCount = 0;
float previousSlope = 0.0f;
uint16_t latestRespRateBpm = 0;

void copyText(char *target, size_t targetSize, const char *source) {
  strncpy(target, source == nullptr ? "" : source, targetSize - 1);
  target[targetSize - 1] = '\0';
}

float maxFloat(float left, float right) {
  return left > right ? left : right;
}

float axisValue(float x, float y, float z, uint8_t axisIndex) {
  switch (axisIndex) {
    case 0:
      return x;
    case 1:
      return y;
    default:
      return z;
  }
}

float computeExtremumConfirmDeltaG() {
  return maxFloat(kRespExtremumConfirmMinG, kRespAmplitudeThresholdG * 0.45f);
}

void resetDetectorState() {
  breathBaselineG = 0.0f;
  breathFilteredG = 0.0f;
  breathDetectionFilteredG = 0.0f;
  previousBreathDetectionFilteredG = 0.0f;
  previousBreathFilteredG = 0.0f;
  previousSlope = 0.0f;
  lastPeakAtMs = 0;
  lastTroughAtMs = 0;
  lastPeakValueG = 0.0f;
  lastTroughValueG = 0.0f;
  hasPeak = false;
  hasTrough = false;
  detectorPrimed = false;
  lastAcceptedCycleAtMs = 0;
  latestAmplitudeG = 0.0f;
  latestBreathIntervalMs = 0.0f;
  latestRespRateBpm = 0;
  acceptedCycleCount = 0;
  respBeatMarkerPending = false;
}

void acceptPeak(uint32_t atMs, float peakValue) {
  if (hasPeak && (!hasTrough || lastPeakAtMs > lastTroughAtMs)) {
    if (peakValue > lastPeakValueG) {
      lastPeakValueG = peakValue;
    }
    copyText(snapshot.rejectReason, sizeof(snapshot.rejectReason), "peak_need_trough");
    return;
  }

  if (!hasTrough) {
    lastPeakAtMs = atMs;
    lastPeakValueG = peakValue;
    hasPeak = true;
    copyText(snapshot.rejectReason, sizeof(snapshot.rejectReason), "peak_need_trough");
    return;
  }

  if (hasTrough && atMs > lastTroughAtMs && atMs - lastTroughAtMs < kRespMinExtremumGapMs) {
    copyText(snapshot.rejectReason, sizeof(snapshot.rejectReason), "peak_half_short");
    return;
  }

  if (atMs > lastTroughAtMs && atMs - lastTroughAtMs < kRespMinHalfBreathMs) {
    copyText(snapshot.rejectReason, sizeof(snapshot.rejectReason), "peak_half_short");
    return;
  }

  lastPeakAtMs = atMs;
  lastPeakValueG = peakValue;
  hasPeak = true;
}

void acceptTrough(uint32_t atMs, float troughValue) {
  if (hasTrough && (!hasPeak || lastTroughAtMs > lastPeakAtMs)) {
    if (troughValue < lastTroughValueG) {
      lastTroughValueG = troughValue;
    }
    copyText(snapshot.rejectReason, sizeof(snapshot.rejectReason), "trough_need_peak");
    return;
  }

  if (!hasPeak) {
    lastTroughAtMs = atMs;
    lastTroughValueG = troughValue;
    hasTrough = true;
    copyText(snapshot.rejectReason, sizeof(snapshot.rejectReason), "trough_need_peak");
    return;
  }

  if (hasPeak && atMs > lastPeakAtMs && atMs - lastPeakAtMs < kRespMinExtremumGapMs) {
    copyText(snapshot.rejectReason, sizeof(snapshot.rejectReason), "trough_half_short");
    return;
  }

  const uint32_t exhaleMs = atMs - lastPeakAtMs;
  if (exhaleMs < kRespMinHalfBreathMs) {
    copyText(snapshot.rejectReason, sizeof(snapshot.rejectReason), "trough_half_short");
    return;
  }

  const uint32_t previousTroughAtMs = lastTroughAtMs;
  const float previousTroughValueG = lastTroughValueG;

  lastTroughAtMs = atMs;
  lastTroughValueG = troughValue;
  hasTrough = true;

  if (previousTroughAtMs == 0 || previousTroughAtMs >= atMs) {
    return;
  }

  const uint32_t intervalMs = atMs - previousTroughAtMs;
  if (intervalMs < kRespMinBreathIntervalMs || intervalMs > kRespMaxBreathIntervalMs) {
    copyText(snapshot.rejectReason, sizeof(snapshot.rejectReason), "interval_out_of_range");
    return;
  }

  const float amplitudeG = lastPeakValueG - previousTroughValueG;
  if (amplitudeG < kRespAmplitudeThresholdG) {
    copyText(snapshot.rejectReason, sizeof(snapshot.rejectReason), "amplitude_too_low");
    return;
  }

  latestBreathIntervalMs = static_cast<float>(intervalMs);
  lastAcceptedCycleAtMs = atMs;
  latestAmplitudeG = amplitudeG;
  acceptedCycleCount += 1;
  respBeatMarkerPending = true;
  if (latestBreathIntervalMs > 0.0f) {
    latestRespRateBpm = static_cast<uint16_t>(60000.0f / latestBreathIntervalMs);
  }
  copyText(snapshot.rejectReason, sizeof(snapshot.rejectReason), "none");
}

float squaref(float value) {
  return value * value;
}

float vectorNorm(float x, float y, float z) {
  return sqrtf(squaref(x) + squaref(y) + squaref(z));
}

bool probeAddress(uint8_t address) {
  Wire.beginTransmission(address);
  return Wire.endTransmission() == 0;
}

bool readRegister(uint8_t address, uint8_t reg, uint8_t &value) {
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

bool readSample(uint8_t address, MpuSample &sample) {
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

bool tryInitializeAt(uint8_t address) {
  if (!probeAddress(address)) {
    return false;
  }

  uint8_t whoAmI = 0;
  if (!readRegister(address, kRegisterWhoAmI, whoAmI)) {
    return false;
  }

  if (whoAmI != 0x68 && whoAmI != 0x70 && whoAmI != 0x71 && whoAmI != 0x73) {
    return false;
  }

  if (!writeRegister(address, kRegisterPowerManagement1, 0x00)) {
    return false;
  }

  activeAddress = address;
  sensorReady = true;
  axisLocked = false;
  lockedAxisIndex = 2;
  resetDetectorState();
  Serial.printf("[resp-cal] imu init ok addr=0x%02X who=0x%02X\n", address, whoAmI);
  return true;
}

void tryInitializeSensor() {
  sensorReady = false;
  activeAddress = 0;
  if (tryInitializeAt(kMpuAddressLow)) {
    return;
  }
  if (tryInitializeAt(kMpuAddressHigh)) {
    return;
  }
  Serial.println("[resp-cal] imu init miss");
}

void updateSignal(uint32_t nowMs) {
  if (!sensorReady || nowMs - lastSampleAtMs < 20) {
    return;
  }

  lastSampleAtMs = nowMs;
  MpuSample sample;
  if (!readSample(activeAddress, sample)) {
    sensorReady = false;
    return;
  }

  const float accelX = static_cast<float>(sample.accelX) / kAccelLsbPerG;
  const float accelY = static_cast<float>(sample.accelY) / kAccelLsbPerG;
  const float accelZ = static_cast<float>(sample.accelZ) / kAccelLsbPerG;
  const float gyroX = static_cast<float>(sample.gyroX) / kGyroLsbPerDps;
  const float gyroY = static_cast<float>(sample.gyroY) / kGyroLsbPerDps;
  const float gyroZ = static_cast<float>(sample.gyroZ) / kGyroLsbPerDps;

  gravityX += (accelX - gravityX) * kGravityEstimateAlpha;
  gravityY += (accelY - gravityY) * kGravityEstimateAlpha;
  gravityZ += (accelZ - gravityZ) * kGravityEstimateAlpha;

  const float absX = fabsf(gravityX);
  const float absY = fabsf(gravityY);
  const float absZ = fabsf(gravityZ);
  if (!axisLocked) {
    if (absX >= absY && absX >= absZ) {
      lockedAxisIndex = 0;
    } else if (absY >= absX && absY >= absZ) {
      lockedAxisIndex = 1;
    } else {
      lockedAxisIndex = 2;
    }
    axisLocked = true;
  }

  const float carrier = axisValue(accelX, accelY, accelZ, lockedAxisIndex);
  copyText(snapshot.axisName, sizeof(snapshot.axisName),
           lockedAxisIndex == 0 ? "X" : (lockedAxisIndex == 1 ? "Y" : "Z"));
  snapshot.respCarrierValue = carrier;

  breathBaselineG += (carrier - breathBaselineG) * kBreathBaselineAlpha;
  const float detrended = carrier - breathBaselineG;
  snapshot.respDetrendedValue = detrended;
  breathFilteredG += (detrended - breathFilteredG) * kBreathSmoothAlpha;
  breathDetectionFilteredG +=
      (breathFilteredG - breathDetectionFilteredG) * kBreathDetectionLowPassAlpha;
  snapshot.respSignalValue = breathFilteredG;
  snapshot.respBeatMarkerValue = respBeatMarkerPending ? maxFloat(latestAmplitudeG * 1.8f, 0.08f) : 0.0f;
  snapshot.respAmplitude = latestAmplitudeG > 0.0f ? latestAmplitudeG : fabsf(breathFilteredG);

  const float dynX = accelX - gravityX;
  const float dynY = accelY - gravityY;
  const float dynZ = accelZ - gravityZ;
  snapshot.motionLevel = vectorNorm(dynX, dynY, dynZ) + vectorNorm(gyroX, gyroY, gyroZ) * 0.01f;

  if (lastAcceptedCycleAtMs != 0 && nowMs - lastAcceptedCycleAtMs > kRespDisplayStaleMs) {
    latestRespRateBpm = 0;
  }

  if (nowMs - startedAtMs < kRespDetectorWarmupMs) {
    previousBreathDetectionFilteredG = breathDetectionFilteredG;
    previousBreathFilteredG = breathFilteredG;
    previousSlope = 0.0f;
    snapshot.respSlopeValue = 0.0f;
    copyText(snapshot.rejectReason, sizeof(snapshot.rejectReason), "warmup");
  } else {
    const float slope = breathDetectionFilteredG - previousBreathDetectionFilteredG;
    snapshot.respSlopeValue = slope;

    if (!detectorPrimed) {
      previousBreathDetectionFilteredG = breathDetectionFilteredG;
      previousBreathFilteredG = breathFilteredG;
      previousSlope = slope;
      detectorPrimed = true;
    } else {
      const float extremumConfirmDeltaG = computeExtremumConfirmDeltaG();
      if (previousSlope > 0.0f && slope <= 0.0f) {
        bool shouldAcceptPeak = true;
        if (hasTrough) {
          shouldAcceptPeak =
              (previousBreathDetectionFilteredG - lastTroughValueG) >= extremumConfirmDeltaG;
        } else {
          shouldAcceptPeak = previousBreathDetectionFilteredG >= extremumConfirmDeltaG;
        }
        if (shouldAcceptPeak) {
          acceptPeak(nowMs - kRespSampleIntervalMs, previousBreathDetectionFilteredG);
        }
      } else if (previousSlope < 0.0f && slope >= 0.0f) {
        bool shouldAcceptTrough = true;
        if (hasPeak) {
          shouldAcceptTrough =
              (lastPeakValueG - previousBreathDetectionFilteredG) >= extremumConfirmDeltaG;
        } else {
          shouldAcceptTrough = (-previousBreathDetectionFilteredG) >= extremumConfirmDeltaG;
        }
        if (shouldAcceptTrough) {
          acceptTrough(nowMs - kRespSampleIntervalMs, previousBreathDetectionFilteredG);
        }
      }

      previousBreathDetectionFilteredG = breathDetectionFilteredG;
      previousBreathFilteredG = breathFilteredG;
      previousSlope = slope;
    }
  }

  snapshot.respRateBpm = latestRespRateBpm;
  respBeatMarkerPending = false;
}

}  // namespace

void respCalibrationManagerBegin(uint32_t nowMs) {
  snapshot = CalibrationStatusSnapshot{};
  snapshot.tsMs = nowMs;
  copyText(snapshot.statusText, sizeof(snapshot.statusText), "idle");
  copyText(snapshot.axisName, sizeof(snapshot.axisName), "Z");
  calibrationStartedAtMs = nowMs;
  startedAtMs = nowMs;
  lastReconnectAtMs = nowMs;
  tryInitializeSensor();
}

void respCalibrationManagerTick(uint32_t nowMs, bool enabled, bool runtimeMonitoringEnabled) {
  if (!sensorReady && nowMs - lastReconnectAtMs >= 1000) {
    lastReconnectAtMs = nowMs;
    tryInitializeSensor();
  }

  const bool shouldSample = enabled || runtimeMonitoringEnabled;
  if (shouldSample) {
    updateSignal(nowMs);
  }

  if (enabled && !wasEnabled) {
    calibrationStartedAtMs = nowMs;
    startedAtMs = nowMs;
    axisLocked = false;
    resetDetectorState();
    snapshot.calibrationStep = 1;
    completedEventPending = false;
    failedEventPending = false;
  }

  wasEnabled = enabled;
  if (!enabled) {
    copyText(snapshot.statusText, sizeof(snapshot.statusText), "idle");
    copyText(snapshot.guideText, sizeof(snapshot.guideText), "");
    snapshot.phaseType = GuidePhaseType::kIdle;
    return;
  }

  const uint32_t elapsedMs = nowMs - calibrationStartedAtMs;
  snapshot.tsMs = nowMs;
  copyText(snapshot.statusText, sizeof(snapshot.statusText), "resp calibration");

  snapshot.calibrationStep = axisLocked ? 2 : 1;
  snapshot.phaseType = GuidePhaseType::kRest;
  snapshot.phaseRemainingMs = elapsedMs < kAxisSelectionSettleMs
    ? (kAxisSelectionSettleMs - elapsedMs)
    : 0;
  copyText(snapshot.guideText,
           sizeof(snapshot.guideText),
           axisLocked ? "axis locked, entering monitoring" : "selecting main axis");

  if (axisLocked && elapsedMs >= kAxisSelectionSettleMs && !completedEventPending) {
    snapshot.calibrationStep = 3;
    snapshot.phaseRemainingMs = 0;
    copyText(snapshot.guideText, sizeof(snapshot.guideText), "profile ready");
    completedEventPending = true;
  }
}

CalibrationStatusSnapshot respCalibrationManagerGetSnapshot() { return snapshot; }

bool respCalibrationManagerConsumeCompletedEvent() {
  const bool hadEvent = completedEventPending;
  completedEventPending = false;
  return hadEvent;
}

bool respCalibrationManagerConsumeFailedEvent() {
  const bool hadEvent = failedEventPending;
  failedEventPending = false;
  return hadEvent;
}

bool respCalibrationManagerIsSensorReady() { return sensorReady; }

float respCalibrationManagerGetLatestSignal() { return breathFilteredG; }

float respCalibrationManagerGetLatestMotionLevel() { return snapshot.motionLevel; }

uint16_t respCalibrationManagerGetLatestRespRateBpm() { return latestRespRateBpm; }

}  // namespace hold_integration