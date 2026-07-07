#pragma once

#include <Arduino.h>

#include "integration_types.h"

namespace hold_integration {

void activeTestManagerBegin(uint32_t nowMs);
void activeTestManagerTick(uint32_t nowMs, bool enabled, uint32_t sessionId);
bool activeTestManagerConsumeWindow(ActivePpgWindow *window);
bool activeTestManagerConsumeCompletedEvent();
ActivePpgRealtimeSnapshot activeTestManagerGetRealtimeSnapshot();
bool activeTestManagerConsumeRealtimeSnapshot(ActivePpgRealtimeSnapshot *snapshot);
bool activeTestManagerConsumeRealtimeBatch(ActivePpgRealtimeBatch *batch);

}  // namespace hold_integration