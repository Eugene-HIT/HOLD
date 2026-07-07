#pragma once

#include <Arduino.h>

#include "integration_types.h"

namespace hold_integration {

void deviceStateMachineBegin(uint32_t nowMs);
void deviceStateMachineTick(uint32_t nowMs);

void deviceStateMachineOnBleConnected(uint32_t nowMs);
void deviceStateMachineOnBleDisconnected(uint32_t nowMs);
void deviceStateMachineStartCalibration(uint32_t nowMs);
void deviceStateMachineOnCalibrationCompleted(uint32_t nowMs);
void deviceStateMachineOnCalibrationFailed(uint32_t nowMs, const char *reason);
void deviceStateMachineOnPressureTriggerConfirmed(uint32_t nowMs);
void deviceStateMachineOnCountdownFinished(bool keepPressed, uint32_t nowMs);
void deviceStateMachineOnActiveTestCompleted(uint32_t nowMs);
void deviceStateMachineRequestBreathGuide(uint32_t durationMs, uint32_t nowMs);
void deviceStateMachineFinishBreathGuide(uint32_t nowMs);
void deviceStateMachineSetError(ErrorSource errorSource, uint16_t errorCode,
                                const char *errorMessage, bool recoverable,
                                uint32_t nowMs);

DeviceState deviceStateMachineGetState();
LedMode deviceStateMachineResolveLedMode();
DeviceStateSnapshot deviceStateMachineBuildSnapshot(uint32_t nowMs);
ErrorStatusSnapshot deviceStateMachineBuildErrorSnapshot(uint32_t nowMs);

bool deviceStateMachineIsActiveTestRunning();
bool deviceStateMachineIsCalibrationRunning();
bool deviceStateMachineIsBreathGuideRunning();
GuidePhaseType deviceStateMachineGetGuidePhase(uint32_t nowMs);
uint32_t deviceStateMachineGetGuidePhaseRemainingMs(uint32_t nowMs);
uint32_t deviceStateMachineGetGuidePhaseElapsedMs(uint32_t nowMs);
uint32_t deviceStateMachineGetGuidePhaseDurationMs(uint32_t nowMs);

}  // namespace hold_integration