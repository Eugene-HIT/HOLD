#pragma once

#include <Arduino.h>

#include "integration_types.h"

namespace hold_integration {

void passiveMonitorManagerBegin(uint32_t nowMs);
void passiveMonitorManagerTick(uint32_t nowMs, bool enabled, uint32_t sessionId);
bool passiveMonitorManagerConsumeRespWindow(PassiveRespWindow *window);

}  // namespace hold_integration