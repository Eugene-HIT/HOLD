#pragma once

#include <Arduino.h>

#include "integration_types.h"

namespace hold_integration {

String packDeviceStateJson(const DeviceStateSnapshot &snapshot);
String packCalibrationStatusJson(const CalibrationStatusSnapshot &snapshot);
String packRespDebugJson(const CalibrationStatusSnapshot &snapshot);
String packActiveRealtimeJson(const ActivePpgRealtimeSnapshot &snapshot);
String packActiveRealtimeBatchJson(const ActivePpgRealtimeBatch &batch);
String packPassivePpgRealtimeBatchJson(const PassivePpgRealtimeBatch &batch);
String packPassiveRespWindowJson(const PassiveRespWindow &window,
								 uint16_t fragmentIndex,
								 uint16_t fragmentTotal);
String packActiveWindowJson(const ActivePpgWindow &window,
							uint16_t fragmentIndex,
							uint16_t fragmentTotal,
							size_t processedPointOffset,
							size_t processedPointCount,
							size_t beatOffset,
							size_t beatCount);
String packErrorStatusJson(const ErrorStatusSnapshot &snapshot);

}  // namespace hold_integration