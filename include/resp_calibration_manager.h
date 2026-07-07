#pragma once

#include <Arduino.h>

#include "integration_types.h"

namespace hold_integration {

void respCalibrationManagerBegin(uint32_t nowMs);
void respCalibrationManagerTick(uint32_t nowMs, bool enabled, bool runtimeMonitoringEnabled);
CalibrationStatusSnapshot respCalibrationManagerGetSnapshot();
bool respCalibrationManagerConsumeCompletedEvent();
bool respCalibrationManagerConsumeFailedEvent();
bool respCalibrationManagerIsSensorReady();
float respCalibrationManagerGetLatestSignal();
float respCalibrationManagerGetLatestMotionLevel();
uint16_t respCalibrationManagerGetLatestRespRateBpm();

}  // namespace hold_integration