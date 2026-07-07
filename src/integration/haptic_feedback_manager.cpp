#include "haptic_feedback_manager.h"

#include <Adafruit_DRV2605.h>
#include <Wire.h>
#include <math.h>

namespace hold_integration {
namespace {

uint32_t confirmPulseUntilMs = 0;
bool countdownPatternActive = false;
uint32_t lastCountdownBeatAtMs = 0;
bool breathGuideActive = false;
GuidePhaseType breathGuidePhase = GuidePhaseType::kIdle;
uint32_t breathGuidePhaseElapsedMs = 0;
uint32_t breathGuidePhaseDurationMs = 0;
bool breathGuideWasActive = false;
bool hapticReady = false;
Adafruit_DRV2605 hapticDriver;

constexpr uint32_t kBreathGuideHapticPulseMs = 1000;

void writeRealtimeValue(uint8_t value) {
  if (!hapticReady) {
    return;
  }

  hapticDriver.setRealtimeValue(value);
}

}  // namespace

void hapticFeedbackManagerBegin(uint32_t nowMs) {
  confirmPulseUntilMs = 0;
  countdownPatternActive = false;
  lastCountdownBeatAtMs = nowMs;
  hapticReady = hapticDriver.begin(&Wire);
  if (!hapticReady) {
    Serial.println("[haptic] driver init miss");
    return;
  }

  hapticDriver.useLRA();
  hapticDriver.selectLibrary(6);
  hapticDriver.setMode(DRV2605_MODE_REALTIME);
  writeRealtimeValue(0x00);
  Serial.println("[haptic] driver init ok");
}

void hapticFeedbackManagerTick(uint32_t nowMs) {
  if (breathGuideActive && breathGuidePhaseDurationMs > 0 &&
      (breathGuidePhase == GuidePhaseType::kInhale || breathGuidePhase == GuidePhaseType::kExhale)) {
    const uint32_t activePulseMs = breathGuidePhaseDurationMs < kBreathGuideHapticPulseMs
      ? breathGuidePhaseDurationMs
      : kBreathGuideHapticPulseMs;
    if (breathGuidePhaseElapsedMs >= activePulseMs) {
      writeRealtimeValue(0x00);
      return;
    }

    const float ratio = activePulseMs > 0
      ? static_cast<float>(breathGuidePhaseElapsedMs) / static_cast<float>(activePulseMs)
      : 0.0f;
    const float waveform = sinf(ratio * PI);
    const uint8_t drive = waveform <= 0.0f ? 0 : static_cast<uint8_t>(waveform * 0x7f);
    writeRealtimeValue(drive);
    return;
  }

  if (confirmPulseUntilMs != 0 && nowMs > confirmPulseUntilMs) {
    confirmPulseUntilMs = 0;
    writeRealtimeValue(0x00);
  }

  if (countdownPatternActive && nowMs - lastCountdownBeatAtMs >= 1000) {
    lastCountdownBeatAtMs = nowMs;
    writeRealtimeValue(0x42);
    confirmPulseUntilMs = nowMs + 150;
  }
}

void hapticFeedbackManagerTriggerConfirmPulse(uint32_t nowMs) {
  confirmPulseUntilMs = nowMs + 500;
  writeRealtimeValue(0x48);
}

void hapticFeedbackManagerStartCountdownPattern(uint32_t nowMs) {
  countdownPatternActive = true;
  lastCountdownBeatAtMs = nowMs;
}

void hapticFeedbackManagerSetBreathGuideState(bool active, GuidePhaseType phase,
                                              uint32_t phaseElapsedMs,
                                              uint32_t phaseDurationMs) {
  const bool wasActive = breathGuideWasActive;
  breathGuideActive = active;
  breathGuidePhase = phase;
  breathGuidePhaseElapsedMs = phaseElapsedMs;
  breathGuidePhaseDurationMs = phaseDurationMs;
  breathGuideWasActive = active;
  if (wasActive && !breathGuideActive) {
    writeRealtimeValue(0x00);
  }
}

void hapticFeedbackManagerStop(uint32_t nowMs) {
  (void)nowMs;
  countdownPatternActive = false;
  confirmPulseUntilMs = 0;
  breathGuideActive = false;
  breathGuideWasActive = false;
  breathGuidePhase = GuidePhaseType::kIdle;
  breathGuidePhaseElapsedMs = 0;
  breathGuidePhaseDurationMs = 0;
  writeRealtimeValue(0x00);
}

}  // namespace hold_integration