#include "device_state_machine.h"

#include <cstring>

namespace hold_integration {
namespace {

struct RuntimeState {
  DeviceState deviceState = DeviceState::kBoot;
  BleLinkState bleLinkState = BleLinkState::kIdle;
  uint32_t sessionId = 1;
  uint32_t activeStateSinceMs = 0;
  uint32_t breathGuideStartedAtMs = 0;
  uint32_t breathGuideDurationMs = 0;
  uint32_t breathGuideUntilMs = 0;
  bool hasActiveError = false;
  ErrorStatusSnapshot errorSnapshot;
  char statusText[32] = "booting";
  char guideText[32] = "";
};

constexpr uint32_t kBreathGuideInhaleMs = 4000;
constexpr uint32_t kBreathGuideExhaleMs = 5000;
constexpr uint32_t kBreathGuideCycleMs = kBreathGuideInhaleMs + kBreathGuideExhaleMs;

RuntimeState runtimeState;

void copyText(char *target, size_t targetSize, const char *source) {
  if (targetSize == 0) {
    return;
  }

  strncpy(target, source == nullptr ? "" : source, targetSize - 1);
  target[targetSize - 1] = '\0';
}

void setState(DeviceState state, const char *statusText, const char *guideText,
              uint32_t nowMs) {
  runtimeState.deviceState = state;
  runtimeState.activeStateSinceMs = nowMs;
  copyText(runtimeState.statusText, sizeof(runtimeState.statusText), statusText);
  copyText(runtimeState.guideText, sizeof(runtimeState.guideText), guideText);
}

GuidePhaseType resolveBreathGuidePhase(uint32_t nowMs,
                                       uint32_t *phaseElapsedMs,
                                       uint32_t *phaseDurationMs,
                                       uint32_t *phaseRemainingMs,
                                       const char **guideText) {
  if (runtimeState.deviceState != DeviceState::kBreathGuideSession ||
      runtimeState.breathGuideStartedAtMs == 0) {
    if (phaseElapsedMs != nullptr) {
      *phaseElapsedMs = 0;
    }
    if (phaseDurationMs != nullptr) {
      *phaseDurationMs = 0;
    }
    if (phaseRemainingMs != nullptr) {
      *phaseRemainingMs = 0;
    }
    if (guideText != nullptr) {
      *guideText = "";
    }
    return GuidePhaseType::kIdle;
  }

  const uint32_t elapsedSinceStart = nowMs - runtimeState.breathGuideStartedAtMs;
  const uint32_t cycleOffsetMs = elapsedSinceStart % kBreathGuideCycleMs;
  if (cycleOffsetMs < kBreathGuideInhaleMs) {
    if (phaseElapsedMs != nullptr) {
      *phaseElapsedMs = cycleOffsetMs;
    }
    if (phaseDurationMs != nullptr) {
      *phaseDurationMs = kBreathGuideInhaleMs;
    }
    if (phaseRemainingMs != nullptr) {
      *phaseRemainingMs = kBreathGuideInhaleMs - cycleOffsetMs;
    }
    if (guideText != nullptr) {
      *guideText = "吸气";
    }
    return GuidePhaseType::kInhale;
  }

  const uint32_t exhaleElapsedMs = cycleOffsetMs - kBreathGuideInhaleMs;
  if (phaseElapsedMs != nullptr) {
    *phaseElapsedMs = exhaleElapsedMs;
  }
  if (phaseDurationMs != nullptr) {
    *phaseDurationMs = kBreathGuideExhaleMs;
  }
  if (phaseRemainingMs != nullptr) {
    *phaseRemainingMs = kBreathGuideExhaleMs - exhaleElapsedMs;
  }
  if (guideText != nullptr) {
    *guideText = "呼气";
  }
  return GuidePhaseType::kExhale;
}

}  // namespace

const char *toString(DeviceState state) {
  switch (state) {
    case DeviceState::kBoot:
      return "BOOT";
    case DeviceState::kBleAdvertising:
      return "BLE_ADVERTISING";
    case DeviceState::kBleConnectedWaitCalibration:
      return "BLE_CONNECTED_WAIT_CALIBRATION";
    case DeviceState::kRespCalibrating:
      return "RESP_CALIBRATING";
    case DeviceState::kPassiveMonitoring:
      return "PASSIVE_MONITORING";
    case DeviceState::kPressHoldConfirm:
      return "PRESS_HOLD_CONFIRM";
    case DeviceState::kPressHoldCountdown:
      return "PRESS_HOLD_COUNTDOWN";
    case DeviceState::kFingerPpgActiveTest:
      return "FINGER_PPG_ACTIVE_TEST";
    case DeviceState::kBreathGuideSession:
      return "BREATH_GUIDE_SESSION";
    case DeviceState::kErrorRecovery:
      return "ERROR_RECOVERY";
  }

  return "UNKNOWN";
}

const char *toString(BleLinkState state) {
  switch (state) {
    case BleLinkState::kIdle:
      return "IDLE";
    case BleLinkState::kAdvertising:
      return "ADVERTISING";
    case BleLinkState::kConnected:
      return "CONNECTED";
    case BleLinkState::kDisconnected:
      return "DISCONNECTED";
  }

  return "UNKNOWN";
}

const char *toString(GuidePhaseType phase) {
  switch (phase) {
    case GuidePhaseType::kIdle:
      return "IDLE";
    case GuidePhaseType::kInhale:
      return "INHALE";
    case GuidePhaseType::kExhale:
      return "EXHALE";
    case GuidePhaseType::kHold:
      return "HOLD";
    case GuidePhaseType::kRest:
      return "REST";
  }

  return "UNKNOWN";
}

const char *toString(LedMode mode) {
  switch (mode) {
    case LedMode::kOff:
      return "OFF";
    case LedMode::kRedBlink:
      return "RED_BLINK";
    case LedMode::kYellowSolid:
      return "YELLOW_SOLID";
    case LedMode::kYellowBreathing:
      return "YELLOW_BREATHING";
    case LedMode::kGreenSolid:
      return "GREEN_SOLID";
    case LedMode::kYellowBlink:
      return "YELLOW_BLINK";
    case LedMode::kBlueSolid:
      return "BLUE_SOLID";
    case LedMode::kErrorFastBlink:
      return "ERROR_FAST_BLINK";
  }

  return "UNKNOWN";
}

void deviceStateMachineBegin(uint32_t nowMs) {
  runtimeState.sessionId = 1;
  runtimeState.bleLinkState = BleLinkState::kAdvertising;
  runtimeState.hasActiveError = false;
  runtimeState.errorSnapshot = ErrorStatusSnapshot{};
  setState(DeviceState::kBleAdvertising, "waiting connection", "scan to connect", nowMs);
}

void deviceStateMachineTick(uint32_t nowMs) {
  if (runtimeState.deviceState == DeviceState::kBreathGuideSession &&
      runtimeState.breathGuideUntilMs != 0 && nowMs >= runtimeState.breathGuideUntilMs) {
    deviceStateMachineFinishBreathGuide(nowMs);
  }
}

void deviceStateMachineOnBleConnected(uint32_t nowMs) {
  runtimeState.bleLinkState = BleLinkState::kConnected;
  runtimeState.sessionId += 1;
  setState(DeviceState::kBleConnectedWaitCalibration, "connected", "wait calibration trigger", nowMs);
}

void deviceStateMachineOnBleDisconnected(uint32_t nowMs) {
  runtimeState.bleLinkState = BleLinkState::kDisconnected;
  setState(DeviceState::kBleAdvertising, "waiting connection", "scan to connect", nowMs);
}

void deviceStateMachineStartCalibration(uint32_t nowMs) {
  setState(DeviceState::kRespCalibrating, "resp calibration", "select main axis", nowMs);
}

void deviceStateMachineOnCalibrationCompleted(uint32_t nowMs) {
  setState(DeviceState::kPassiveMonitoring, "monitoring", "passive running", nowMs);
}

void deviceStateMachineOnCalibrationFailed(uint32_t nowMs, const char *reason) {
  setState(DeviceState::kBleConnectedWaitCalibration, "calibration failed", reason, nowMs);
}

void deviceStateMachineOnPressureTriggerConfirmed(uint32_t nowMs) {
  setState(DeviceState::kPressHoldCountdown, "countdown", "keep press for active test", nowMs);
}

void deviceStateMachineOnCountdownFinished(bool keepPressed, uint32_t nowMs) {
  if (keepPressed) {
    setState(DeviceState::kFingerPpgActiveTest, "active test", "finger test 60s", nowMs);
    return;
  }

  setState(DeviceState::kRespCalibrating, "resp calibration", "restart calibration", nowMs);
}

void deviceStateMachineOnActiveTestCompleted(uint32_t nowMs) {
  setState(DeviceState::kPassiveMonitoring, "monitoring", "active test complete", nowMs);
}

void deviceStateMachineRequestBreathGuide(uint32_t durationMs, uint32_t nowMs) {
  runtimeState.breathGuideStartedAtMs = nowMs;
  runtimeState.breathGuideDurationMs = durationMs;
  runtimeState.breathGuideUntilMs = nowMs + durationMs;
  setState(DeviceState::kBreathGuideSession, "breath guide", "吸气", nowMs);
}

void deviceStateMachineFinishBreathGuide(uint32_t nowMs) {
  runtimeState.breathGuideStartedAtMs = 0;
  runtimeState.breathGuideDurationMs = 0;
  runtimeState.breathGuideUntilMs = 0;
  setState(DeviceState::kPassiveMonitoring, "monitoring", "breath guide complete", nowMs);
}

void deviceStateMachineSetError(ErrorSource errorSource, uint16_t errorCode,
                                const char *errorMessage, bool recoverable,
                                uint32_t nowMs) {
  runtimeState.hasActiveError = true;
  runtimeState.errorSnapshot.sessionId = runtimeState.sessionId;
  runtimeState.errorSnapshot.tsMs = nowMs;
  runtimeState.errorSnapshot.errorSource = errorSource;
  runtimeState.errorSnapshot.errorCode = errorCode;
  runtimeState.errorSnapshot.recoverable = recoverable;
  copyText(runtimeState.errorSnapshot.errorMessage,
           sizeof(runtimeState.errorSnapshot.errorMessage), errorMessage);
  setState(DeviceState::kErrorRecovery, "error recovery", errorMessage, nowMs);
}

DeviceState deviceStateMachineGetState() { return runtimeState.deviceState; }

LedMode deviceStateMachineResolveLedMode() {
  switch (runtimeState.deviceState) {
    case DeviceState::kBleAdvertising:
      return LedMode::kRedBlink;
    case DeviceState::kBleConnectedWaitCalibration:
      return LedMode::kYellowSolid;
    case DeviceState::kRespCalibrating:
    case DeviceState::kBreathGuideSession:
      return LedMode::kYellowBreathing;
    case DeviceState::kPassiveMonitoring:
      return LedMode::kGreenSolid;
    case DeviceState::kPressHoldConfirm:
    case DeviceState::kPressHoldCountdown:
      return LedMode::kYellowBlink;
    case DeviceState::kFingerPpgActiveTest:
      return LedMode::kBlueSolid;
    case DeviceState::kErrorRecovery:
      return LedMode::kErrorFastBlink;
    case DeviceState::kBoot:
    default:
      return LedMode::kOff;
  }
}

DeviceStateSnapshot deviceStateMachineBuildSnapshot(uint32_t nowMs) {
  DeviceStateSnapshot snapshot;
  snapshot.sessionId = runtimeState.sessionId;
  snapshot.tsMs = nowMs;
  snapshot.deviceState = runtimeState.deviceState;
  snapshot.bleLinkState = runtimeState.bleLinkState;
  snapshot.ledMode = deviceStateMachineResolveLedMode();
  snapshot.phaseType = GuidePhaseType::kIdle;
  snapshot.phaseRemainingMs = 0;
  snapshot.isClientConnected = runtimeState.bleLinkState == BleLinkState::kConnected;
  snapshot.hasActiveError = runtimeState.hasActiveError;
  snapshot.errorCode = runtimeState.errorSnapshot.errorCode;
  strncpy(snapshot.statusText, runtimeState.statusText, sizeof(snapshot.statusText) - 1);
  strncpy(snapshot.guideText, runtimeState.guideText, sizeof(snapshot.guideText) - 1);
  snapshot.statusText[sizeof(snapshot.statusText) - 1] = '\0';
  snapshot.guideText[sizeof(snapshot.guideText) - 1] = '\0';
  if (runtimeState.deviceState == DeviceState::kBreathGuideSession) {
    uint32_t phaseElapsedMs = 0;
    uint32_t phaseDurationMs = 0;
    uint32_t phaseRemainingMs = 0;
    const char *guideText = "";
    snapshot.phaseType = resolveBreathGuidePhase(nowMs,
                                                 &phaseElapsedMs,
                                                 &phaseDurationMs,
                                                 &phaseRemainingMs,
                                                 &guideText);
    snapshot.phaseRemainingMs = phaseRemainingMs;
    copyText(snapshot.guideText, sizeof(snapshot.guideText), guideText);
  }
  return snapshot;
}

ErrorStatusSnapshot deviceStateMachineBuildErrorSnapshot(uint32_t nowMs) {
  runtimeState.errorSnapshot.tsMs = nowMs;
  return runtimeState.errorSnapshot;
}

bool deviceStateMachineIsActiveTestRunning() {
  return runtimeState.deviceState == DeviceState::kFingerPpgActiveTest;
}

bool deviceStateMachineIsCalibrationRunning() {
  return runtimeState.deviceState == DeviceState::kRespCalibrating;
}

bool deviceStateMachineIsBreathGuideRunning() {
  return runtimeState.deviceState == DeviceState::kBreathGuideSession;
}

GuidePhaseType deviceStateMachineGetGuidePhase(uint32_t nowMs) {
  return resolveBreathGuidePhase(nowMs, nullptr, nullptr, nullptr, nullptr);
}

uint32_t deviceStateMachineGetGuidePhaseRemainingMs(uint32_t nowMs) {
  uint32_t phaseRemainingMs = 0;
  resolveBreathGuidePhase(nowMs, nullptr, nullptr, &phaseRemainingMs, nullptr);
  return phaseRemainingMs;
}

uint32_t deviceStateMachineGetGuidePhaseElapsedMs(uint32_t nowMs) {
  uint32_t phaseElapsedMs = 0;
  resolveBreathGuidePhase(nowMs, &phaseElapsedMs, nullptr, nullptr, nullptr);
  return phaseElapsedMs;
}

uint32_t deviceStateMachineGetGuidePhaseDurationMs(uint32_t nowMs) {
  uint32_t phaseDurationMs = 0;
  resolveBreathGuidePhase(nowMs, nullptr, &phaseDurationMs, nullptr, nullptr);
  return phaseDurationMs;
}

}  // namespace hold_integration