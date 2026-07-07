#include "passive_monitor_manager.h"

#include "resp_calibration_manager.h"

namespace hold_integration {
namespace {

PassiveRespWindow readyWindow;
bool windowReady = false;
uint32_t activeWindowId = 0;
uint32_t activeWindowStartMs = 0;
uint16_t pointIndex = 0;

}  // namespace

void passiveMonitorManagerBegin(uint32_t nowMs) {
  readyWindow = PassiveRespWindow{};
  activeWindowId = 0;
  activeWindowStartMs = nowMs;
  pointIndex = 0;
  windowReady = false;
}

void passiveMonitorManagerTick(uint32_t nowMs, bool enabled, uint32_t sessionId) {
  if (!enabled) {
    pointIndex = 0;
    activeWindowStartMs = nowMs;
    return;
  }

  if (activeWindowId == 0) {
    activeWindowId = 1;
    activeWindowStartMs = nowMs;
  }

  if (pointIndex < kPassiveRespPointCapacity && nowMs % 200 == 0) {
    const float signal = respCalibrationManagerGetLatestSignal();
    const int32_t normalized = static_cast<int32_t>(signal * 5000.0f + 32768.0f);
    readyWindow.points[pointIndex] = normalized < 0 ? 0 : (normalized > 65535 ? 65535 : static_cast<uint16_t>(normalized));
    pointIndex += 1;
  }

  if (nowMs - activeWindowStartMs >= 10000) {
    readyWindow.sessionId = sessionId;
    readyWindow.windowId = activeWindowId;
    readyWindow.windowStartTsMs = activeWindowStartMs;
    readyWindow.windowEndTsMs = nowMs;
    readyWindow.respRateBpm = respCalibrationManagerGetLatestRespRateBpm();
    readyWindow.qualityScore = respCalibrationManagerIsSensorReady() ? 88 : 30;
    readyWindow.motionLevel = respCalibrationManagerGetLatestMotionLevel();
    readyWindow.pointCount = pointIndex;
    windowReady = true;
    activeWindowId += 1;
    activeWindowStartMs = nowMs;
    pointIndex = 0;
  }
}

bool passiveMonitorManagerConsumeRespWindow(PassiveRespWindow *window) {
  if (!windowReady || window == nullptr) {
    return false;
  }

  *window = readyWindow;
  windowReady = false;
  return true;
}

}  // namespace hold_integration