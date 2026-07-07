#pragma once

#include <Arduino.h>

#include "integration_types.h"

namespace hold_integration {

void ledFeedbackManagerBegin(uint8_t redPin, uint8_t greenPin, uint8_t bluePin,
                             uint32_t nowMs);
void ledFeedbackManagerTick(uint32_t nowMs);
void ledFeedbackManagerSetMode(LedMode mode, GuidePhaseType phase);
void ledFeedbackManagerSetGuideProgress(uint32_t phaseElapsedMs, uint32_t phaseDurationMs);
LedMode ledFeedbackManagerGetMode();

}  // namespace hold_integration