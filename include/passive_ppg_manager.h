#pragma once

#include <Arduino.h>

#include "integration_types.h"

namespace hold_integration {

void passivePpgManagerBegin(uint32_t nowMs);
void passivePpgManagerTick(uint32_t nowMs, bool enabled, uint32_t sessionId);
bool passivePpgManagerConsumeRealtimeBatch(PassivePpgRealtimeBatch *batch);

}  // namespace hold_integration