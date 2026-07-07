#pragma once

#include <Arduino.h>

namespace hold_integration {

enum class DeviceState : uint8_t {
  kBoot = 0,
  kBleAdvertising,
  kBleConnectedWaitCalibration,
  kRespCalibrating,
  kPassiveMonitoring,
  kPressHoldConfirm,
  kPressHoldCountdown,
  kFingerPpgActiveTest,
  kBreathGuideSession,
  kErrorRecovery,
};

enum class BleLinkState : uint8_t {
  kIdle = 0,
  kAdvertising,
  kConnected,
  kDisconnected,
};

enum class GuidePhaseType : uint8_t {
  kIdle = 0,
  kInhale,
  kExhale,
  kHold,
  kRest,
};

enum class LedMode : uint8_t {
  kOff = 0,
  kRedBlink,
  kYellowSolid,
  kYellowBreathing,
  kGreenSolid,
  kYellowBlink,
  kBlueSolid,
  kErrorFastBlink,
};

enum class ErrorSource : uint8_t {
  kNone = 0,
  kBle,
  kImu,
  kChestPpg,
  kFingerPpg,
  kPressure,
  kHaptic,
  kSystem,
};

constexpr uint16_t kPassiveRespPointCapacity = 300;
constexpr uint16_t kPassivePpgPointCapacity = 300;
constexpr uint16_t kActiveProcessedPointCapacity = 1500;
constexpr uint16_t kActiveBeatCapacity = 180;
constexpr uint16_t kActiveRealtimeBatchCapacity = 10;

struct DeviceStateSnapshot {
  uint32_t sessionId = 0;
  uint32_t tsMs = 0;
  DeviceState deviceState = DeviceState::kBoot;
  BleLinkState bleLinkState = BleLinkState::kIdle;
  LedMode ledMode = LedMode::kOff;
  GuidePhaseType phaseType = GuidePhaseType::kIdle;
  uint32_t phaseRemainingMs = 0;
  bool isClientConnected = false;
  bool hasActiveError = false;
  uint16_t errorCode = 0;
  char deviceName[24] = "HOLD-DEVICE";
  char statusText[32] = "booting";
  char guideText[32] = "";
};

struct CalibrationStatusSnapshot {
  uint32_t sessionId = 0;
  uint32_t tsMs = 0;
  uint16_t calibrationStep = 0;
  GuidePhaseType phaseType = GuidePhaseType::kIdle;
  uint32_t phaseRemainingMs = 0;
  uint16_t respRateBpm = 0;
  float respCarrierValue = 0.0f;
  float respDetrendedValue = 0.0f;
  float respSignalValue = 0.0f;
  float respBeatMarkerValue = 0.0f;
  float respSlopeValue = 0.0f;
  float respAmplitude = 0.0f;
  float motionLevel = 0.0f;
  char axisName[8] = "Z";
  char rejectReason[32] = "";
  char statusText[32] = "idle";
  char guideText[32] = "";
};

struct PassiveRespWindow {
  uint32_t sessionId = 0;
  uint32_t windowId = 0;
  uint32_t windowStartTsMs = 0;
  uint32_t windowEndTsMs = 0;
  uint16_t respRateBpm = 0;
  uint8_t qualityScore = 0;
  float motionLevel = 0.0f;
  uint16_t pointCount = 0;
  uint16_t points[kPassiveRespPointCapacity] = {0};
};

struct PassivePpgWindow {
  uint32_t sessionId = 0;
  uint32_t windowId = 0;
  uint32_t windowStartTsMs = 0;
  uint32_t windowEndTsMs = 0;
  bool hasSkinContact = false;
  uint16_t heartRateBpm = 0;
  uint8_t qualityScore = 0;
  uint16_t pointCount = 0;
  uint16_t points[kPassivePpgPointCapacity] = {0};
};

struct ActivePpgWindow {
  uint32_t sessionId = 0;
  uint32_t measurementId = 0;
  uint32_t sampleStartTsMs = 0;
  uint32_t sampleEndTsMs = 0;
  uint16_t heartRateBpm = 0;
  uint8_t qualityScore = 0;
  uint16_t processedPointCount = 0;
  uint16_t beatCount = 0;
  uint16_t rrIntervalCount = 0;
  uint16_t processedPoints[kActiveProcessedPointCapacity] = {0};
  uint32_t beatTsMs[kActiveBeatCapacity] = {0};
  uint16_t rrIntervalsMs[kActiveBeatCapacity] = {0};
};

struct ActivePpgRealtimeSnapshot {
  uint32_t sessionId = 0;
  uint32_t measurementId = 0;
  uint32_t tsMs = 0;
  float filteredPoint = 0.0f;
  float beatMarkerPoint = 0.0f;
  uint16_t heartRateBpm = 0;
  uint16_t lastBeatIntervalMs = 0;
  uint8_t qualityScore = 0;
  uint16_t beatCount = 0;
  bool contactPresent = false;
  bool active = false;
};

struct ActivePpgRealtimeBatch {
  uint32_t sessionId = 0;
  uint32_t measurementId = 0;
  uint32_t tsMsEnd = 0;
  uint16_t sampleIntervalMs = 0;
  uint8_t sampleCount = 0;
  int16_t filteredPoints[kActiveRealtimeBatchCapacity] = {0};
  int16_t beatMarkerPoints[kActiveRealtimeBatchCapacity] = {0};
  uint16_t heartRateBpm = 0;
  uint16_t lastBeatIntervalMs = 0;
  uint8_t qualityScore = 0;
  uint16_t beatCount = 0;
  bool contactPresent = false;
  bool active = false;
};

struct PassivePpgRealtimeBatch {
  uint32_t sessionId = 0;
  uint32_t tsMsEnd = 0;
  uint16_t sampleIntervalMs = 0;
  uint8_t sampleCount = 0;
  int16_t filteredPoints[kActiveRealtimeBatchCapacity] = {0};
  int16_t beatMarkerPoints[kActiveRealtimeBatchCapacity] = {0};
  uint16_t heartRateBpm = 0;
  uint8_t qualityScore = 0;
  bool contactPresent = false;
  bool active = false;
};

struct ErrorStatusSnapshot {
  uint32_t sessionId = 0;
  uint32_t tsMs = 0;
  ErrorSource errorSource = ErrorSource::kNone;
  uint16_t errorCode = 0;
  bool recoverable = true;
  char errorMessage[48] = "";
};

const char *toString(DeviceState state);
const char *toString(BleLinkState state);
const char *toString(GuidePhaseType phase);
const char *toString(LedMode mode);

}  // namespace hold_integration