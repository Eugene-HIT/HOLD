#pragma once

#include <Arduino.h>

namespace hold_integration {

struct PressureTriggerSnapshot {
  uint8_t level = 0;
  uint32_t heldMs = 0;
  bool isConfirmed = false;
  bool keepPressedAfterCountdown = false;
};

void pressureTriggerManagerBegin(uint32_t nowMs);
void pressureTriggerManagerTick(uint32_t nowMs);
PressureTriggerSnapshot pressureTriggerManagerGetSnapshot();

}  // namespace hold_integration