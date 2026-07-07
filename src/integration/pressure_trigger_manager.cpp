#include "pressure_trigger_manager.h"

#include "pressure_film_raw_reader.h"

namespace hold_integration {
namespace {

PressureTriggerSnapshot snapshot;
PressureFilmRawReader pressureReader;
PressureFilmRawReader::Sample pressureSample;
uint32_t holdStartedAtMs = 0;
bool wasPressed = false;

}  // namespace

void pressureTriggerManagerBegin(uint32_t nowMs) {
  (void)nowMs;
  snapshot = PressureTriggerSnapshot{};
  pressureReader.begin();
}

void pressureTriggerManagerTick(uint32_t nowMs) {
  if (!pressureReader.update() || !pressureReader.readLatestSample(pressureSample)) {
    snapshot = PressureTriggerSnapshot{};
    return;
  }

  snapshot.level = pressureSample.level;
  snapshot.isConfirmed = false;
  snapshot.keepPressedAfterCountdown = false;

  const bool pressed = pressureSample.level >= 10;
  if (pressed && !wasPressed) {
    holdStartedAtMs = nowMs;
  }

  if (pressed) {
    snapshot.heldMs = nowMs - holdStartedAtMs;
    snapshot.isConfirmed = snapshot.heldMs >= 2000;
    snapshot.keepPressedAfterCountdown = snapshot.heldMs >= 5000;
  } else {
    snapshot.heldMs = 0;
  }

  wasPressed = pressed;
}

PressureTriggerSnapshot pressureTriggerManagerGetSnapshot() { return snapshot; }

}  // namespace hold_integration