#pragma once

#include <Arduino.h>

#include "integration_types.h"

namespace hold_integration {

void bleLinkManagerBegin(uint32_t nowMs);
void bleLinkManagerTick(uint32_t nowMs);

bool bleLinkManagerConsumeConnectedEvent();
bool bleLinkManagerConsumeDisconnectedEvent();
bool bleLinkManagerConsumeBreathGuideRequest(uint32_t *durationMs);

BleLinkState bleLinkManagerGetLinkState();
bool bleLinkManagerIsClientConnected();

void bleLinkManagerPublishDeviceState(const DeviceStateSnapshot &snapshot);
void bleLinkManagerPublishCalibrationStatus(const CalibrationStatusSnapshot &snapshot);
void bleLinkManagerPublishRespDebug(const CalibrationStatusSnapshot &snapshot);
void bleLinkManagerPublishActiveRealtime(const ActivePpgRealtimeSnapshot &snapshot);
void bleLinkManagerPublishActiveRealtimeBatch(const ActivePpgRealtimeBatch &batch);
void bleLinkManagerPublishPassivePpgRealtimeBatch(const PassivePpgRealtimeBatch &batch);
void bleLinkManagerPublishPassiveRespWindow(const PassiveRespWindow &window,
                                            uint16_t fragmentIndex,
                                            uint16_t fragmentTotal);
void bleLinkManagerPublishActiveWindow(const ActivePpgWindow &window,
                                       uint16_t fragmentIndex,
                                       uint16_t fragmentTotal,
                                       size_t processedPointOffset,
                                       size_t processedPointCount,
                                       size_t beatOffset,
                                       size_t beatCount);
void bleLinkManagerPublishDebugLog(const char *message);

}  // namespace hold_integration