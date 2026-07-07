#pragma once

#include <Arduino.h>

#include "integration_types.h"

namespace hold_integration {

void hapticFeedbackManagerBegin(uint32_t nowMs);
void hapticFeedbackManagerTick(uint32_t nowMs);
void hapticFeedbackManagerTriggerConfirmPulse(uint32_t nowMs);
void hapticFeedbackManagerStartCountdownPattern(uint32_t nowMs);
void hapticFeedbackManagerSetBreathGuideState(bool active, GuidePhaseType phase,
											  uint32_t phaseElapsedMs,
											  uint32_t phaseDurationMs);
void hapticFeedbackManagerStop(uint32_t nowMs);

}  // namespace hold_integration