#include <Arduino.h>
#include <Wire.h>

#include "active_test_manager.h"
#include "ble_link_manager.h"
#include "data_packager.h"
#include "device_state_machine.h"
#include "haptic_feedback_manager.h"
#include "led_feedback_manager.h"
#include "passive_monitor_manager.h"
#include "passive_ppg_manager.h"
#include "pressure_trigger_manager.h"
#include "project_config.h"
#include "resp_calibration_manager.h"

using namespace hold_integration;

namespace {

constexpr uint8_t kRgbRedPin = 7;
constexpr uint8_t kRgbGreenPin = 8;
constexpr uint8_t kRgbBluePin = 9;
constexpr uint8_t kHeaterControlPin = 2;
constexpr uint8_t kHeaterPwmChannel = 2;
constexpr uint32_t kHeaterPwmFrequencyHz = 5000;
constexpr uint8_t kHeaterPwmResolutionBits = 8;
constexpr uint32_t kHeaterPwmDuty80Percent = 204;
constexpr uint32_t kHeaterEnableDelayMs = 5000;
constexpr uint32_t kDeviceStatePublishIntervalMs = 500;
constexpr uint32_t kCalibrationPublishIntervalMs = 250;
constexpr size_t kActiveWindowProcessedPointsPerFragment = 48;
constexpr size_t kActiveWindowBeatTsPerFragment = 12;

uint32_t lastDeviceStatePublishAtMs = 0;
uint32_t lastCalibrationPublishAtMs = 0;
bool countdownHandled = false;
bool heaterEnabled = false;
bool calibrationTriggerLatched = false;

uint16_t computeActiveWindowFragmentTotal(const hold_integration::ActivePpgWindow &window) {
  const size_t pointFragments =
      (window.processedPointCount + kActiveWindowProcessedPointsPerFragment - 1) /
      kActiveWindowProcessedPointsPerFragment;
  const size_t beatFragments =
      (window.beatCount + kActiveWindowBeatTsPerFragment - 1) /
      kActiveWindowBeatTsPerFragment;
  const size_t total = pointFragments > beatFragments ? pointFragments : beatFragments;
  return static_cast<uint16_t>(total == 0 ? 1 : total);
}

bool consumeManualCalibrationRequest(const hold_integration::PressureTriggerSnapshot &pressure) {
  bool serialRequested = false;
  while (Serial.available() > 0) {
    const int value = Serial.read();
    if (value == 'c' || value == 'C') {
      serialRequested = true;
    }
  }

  const bool pressureRequested = pressure.isConfirmed;
  const bool requested = serialRequested || pressureRequested;
  if (requested && !calibrationTriggerLatched) {
    calibrationTriggerLatched = true;
    return true;
  }

  if (!pressureRequested) {
    calibrationTriggerLatched = false;
  }

  return false;
}

void setupHeaterPwm() {
  ledcSetup(kHeaterPwmChannel, kHeaterPwmFrequencyHz, kHeaterPwmResolutionBits);
  ledcAttachPin(kHeaterControlPin, kHeaterPwmChannel);
  ledcWrite(kHeaterPwmChannel, 0);
}

void updateHeaterOutput(uint32_t nowMs) {
  if (heaterEnabled || nowMs < kHeaterEnableDelayMs) {
    return;
  }

  heaterEnabled = true;
  ledcWrite(kHeaterPwmChannel, kHeaterPwmDuty80Percent);
  Serial.println("[heater] enabled duty=80%");
}

void routeStateTransitions(uint32_t nowMs) {
  if (bleLinkManagerConsumeConnectedEvent()) {
    deviceStateMachineOnBleConnected(nowMs);
  }

  if (bleLinkManagerConsumeDisconnectedEvent()) {
    deviceStateMachineOnBleDisconnected(nowMs);
    calibrationTriggerLatched = false;
  }

  uint32_t breathGuideDurationMs = 0;
  if (bleLinkManagerConsumeBreathGuideRequest(&breathGuideDurationMs)) {
    const hold_integration::DeviceState state = deviceStateMachineGetState();
    if (state != hold_integration::DeviceState::kFingerPpgActiveTest &&
        state != hold_integration::DeviceState::kPressHoldCountdown &&
        state != hold_integration::DeviceState::kErrorRecovery) {
      hapticFeedbackManagerStop(nowMs);
      deviceStateMachineRequestBreathGuide(breathGuideDurationMs == 0 ? 48000 : breathGuideDurationMs,
                                           nowMs);
    }
  }

  const hold_integration::DeviceState currentState = deviceStateMachineGetState();
  const hold_integration::PressureTriggerSnapshot pressure = pressureTriggerManagerGetSnapshot();
  if (currentState == hold_integration::DeviceState::kBleConnectedWaitCalibration &&
      consumeManualCalibrationRequest(pressure)) {
    hapticFeedbackManagerTriggerConfirmPulse(nowMs);
    deviceStateMachineStartCalibration(nowMs);
  }

  if (respCalibrationManagerConsumeCompletedEvent()) {
    deviceStateMachineOnCalibrationCompleted(nowMs);
  }

  if (currentState == hold_integration::DeviceState::kPassiveMonitoring && pressure.isConfirmed) {
    hapticFeedbackManagerTriggerConfirmPulse(nowMs);
    hapticFeedbackManagerStartCountdownPattern(nowMs);
    deviceStateMachineOnPressureTriggerConfirmed(nowMs);
    countdownHandled = false;
  }

  if (deviceStateMachineGetState() == hold_integration::DeviceState::kPressHoldCountdown &&
      pressure.heldMs == 0 && !countdownHandled) {
    countdownHandled = true;
    hapticFeedbackManagerStop(nowMs);
    deviceStateMachineOnCountdownFinished(false, nowMs);
  }

  if (deviceStateMachineGetState() == hold_integration::DeviceState::kPressHoldCountdown &&
      pressure.heldMs >= 5000 && !countdownHandled) {
    countdownHandled = true;
    hapticFeedbackManagerStop(nowMs);
    deviceStateMachineOnCountdownFinished(true, nowMs);
  }

  if (activeTestManagerConsumeCompletedEvent()) {
    deviceStateMachineOnActiveTestCompleted(nowMs);
  }
}

void publishPeriodicSnapshots(uint32_t nowMs) {
  const hold_integration::DeviceState currentState = deviceStateMachineGetState();

  if (nowMs - lastDeviceStatePublishAtMs >= kDeviceStatePublishIntervalMs) {
    lastDeviceStatePublishAtMs = nowMs;
    const hold_integration::DeviceStateSnapshot snapshot = deviceStateMachineBuildSnapshot(nowMs);
    bleLinkManagerPublishDeviceState(snapshot);
  }

  if (deviceStateMachineIsCalibrationRunning() &&
      nowMs - lastCalibrationPublishAtMs >= kCalibrationPublishIntervalMs) {
    lastCalibrationPublishAtMs = nowMs;
    bleLinkManagerPublishCalibrationStatus(respCalibrationManagerGetSnapshot());
  }

  if ((currentState == hold_integration::DeviceState::kRespCalibrating ||
       currentState == hold_integration::DeviceState::kPassiveMonitoring) &&
      nowMs - lastCalibrationPublishAtMs >= kCalibrationPublishIntervalMs) {
    lastCalibrationPublishAtMs = nowMs;
    bleLinkManagerPublishRespDebug(respCalibrationManagerGetSnapshot());
  }

  ActivePpgRealtimeBatch realtimeBatch;
  if (activeTestManagerConsumeRealtimeBatch(&realtimeBatch)) {
    bleLinkManagerPublishActiveRealtimeBatch(realtimeBatch);
  }

  hold_integration::PassiveRespWindow passiveWindow;
  if (passiveMonitorManagerConsumeRespWindow(&passiveWindow)) {
    bleLinkManagerPublishPassiveRespWindow(passiveWindow, 0, 1);
  }

  PassivePpgRealtimeBatch passivePpgBatch;
  if (passivePpgManagerConsumeRealtimeBatch(&passivePpgBatch)) {
    bleLinkManagerPublishPassivePpgRealtimeBatch(passivePpgBatch);
  }

  hold_integration::ActivePpgWindow activeWindow;
  if (activeTestManagerConsumeWindow(&activeWindow)) {
    // 主动检测整分钟波形仍由 active_realtime_batch 持续累计；
    // 这里单独补发完整 beat 时间戳数组，确保前端直接使用固件算法时间戳，
    // 不再只靠 i7 spike 近似还原 HRV 时间线。
    bleLinkManagerPublishActiveWindow(activeWindow,
                                      0,
                                      1,
                                      0,
                                      0,
                                      0,
                                      activeWindow.beatCount);
  }
}

}  // namespace

void setup() {
  auto logBootStage = [](const char *stage) {
    Serial.print("[boot-stage] ");
    Serial.println(stage);
  };

  Serial.begin(115200);
  delay(1200);

  const uint32_t nowMs = millis();
  Serial.println("[boot] xiao_esp32s3_integrated_hold hardware-first starting");
  logBootStage("serial-ready");

  Wire.begin(project_config::kI2cSdaPin, project_config::kI2cSclPin);
  Wire.setClock(project_config::kI2cClockHz);
  Wire.setTimeOut(20);
  logBootStage("i2c-ready");

  setupHeaterPwm();
  logBootStage("heater-pwm-ready");

  logBootStage("ble-begin");
  bleLinkManagerBegin(nowMs);
  logBootStage("ble-ready");

  logBootStage("led-begin");
  ledFeedbackManagerBegin(kRgbRedPin, kRgbGreenPin, kRgbBluePin, nowMs);
  logBootStage("led-ready");

  logBootStage("haptic-begin");
  hapticFeedbackManagerBegin(nowMs);
  logBootStage("haptic-ready");

  logBootStage("pressure-begin");
  pressureTriggerManagerBegin(nowMs);
  logBootStage("pressure-ready");

  logBootStage("resp-begin");
  respCalibrationManagerBegin(nowMs);
  logBootStage("resp-ready");

  logBootStage("passive-monitor-begin");
  passiveMonitorManagerBegin(nowMs);
  logBootStage("passive-monitor-ready");

  logBootStage("passive-ppg-begin");
  passivePpgManagerBegin(nowMs);
  logBootStage("passive-ppg-ready");

  logBootStage("active-ppg-begin");
  activeTestManagerBegin(nowMs);
  logBootStage("active-ppg-ready");

  logBootStage("state-machine-begin");
  deviceStateMachineBegin(nowMs);
  logBootStage("setup-complete");
}

void loop() {
  const uint32_t nowMs = millis();
  const hold_integration::DeviceState currentState = deviceStateMachineGetState();
  const bool respRuntimeMonitoringEnabled =
      currentState == hold_integration::DeviceState::kPassiveMonitoring ||
      currentState == hold_integration::DeviceState::kBreathGuideSession;

  bleLinkManagerTick(nowMs);
  pressureTriggerManagerTick(nowMs);
  respCalibrationManagerTick(nowMs,
                             deviceStateMachineIsCalibrationRunning(),
                             respRuntimeMonitoringEnabled);
  passiveMonitorManagerTick(nowMs,
                            currentState == hold_integration::DeviceState::kPassiveMonitoring,
                            deviceStateMachineBuildSnapshot(nowMs).sessionId);
  passivePpgManagerTick(nowMs,
                        currentState == hold_integration::DeviceState::kPassiveMonitoring,
                        deviceStateMachineBuildSnapshot(nowMs).sessionId);
  activeTestManagerTick(nowMs, deviceStateMachineIsActiveTestRunning(),
                        deviceStateMachineBuildSnapshot(nowMs).sessionId);
  routeStateTransitions(nowMs);
  deviceStateMachineTick(nowMs);
  updateHeaterOutput(nowMs);

  const GuidePhaseType guidePhase = deviceStateMachineIsBreathGuideRunning()
    ? deviceStateMachineGetGuidePhase(nowMs)
    : respCalibrationManagerGetSnapshot().phaseType;
  ledFeedbackManagerSetMode(deviceStateMachineResolveLedMode(), guidePhase);
  ledFeedbackManagerSetGuideProgress(deviceStateMachineGetGuidePhaseElapsedMs(nowMs),
                                     deviceStateMachineGetGuidePhaseDurationMs(nowMs));
  ledFeedbackManagerTick(nowMs);
  hapticFeedbackManagerSetBreathGuideState(deviceStateMachineIsBreathGuideRunning(),
                                           guidePhase,
                                           deviceStateMachineGetGuidePhaseElapsedMs(nowMs),
                                           deviceStateMachineGetGuidePhaseDurationMs(nowMs));
  hapticFeedbackManagerTick(nowMs);
  publishPeriodicSnapshots(nowMs);

  delay(10);
}