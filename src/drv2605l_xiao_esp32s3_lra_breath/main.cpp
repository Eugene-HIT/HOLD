/*
 * 创建时间: 2026-06-11
 * 文件主要职责: 在 XIAO ESP32S3 + DRV2605L + LRA 上提供独立的深呼吸震动实验入口，用于验证呼吸引导反馈手感。
 * 核心函数输入输出:
 * - setup(): 初始化串口、独立 I2C 与 DRV2605L，切换到 LRA 实时播放模式。
 * - loop(): 按“吸气强到弱 -> 呼气强到弱 -> 短暂停”的节律持续输出实时震动包络。
 * 最后更改时间: 2026-06-11
 * 累加式更改日志:
 * - 2026-06-11: 新建独立 LRA 呼吸震动实验入口，避开现有 IMU 与 PPG I2C 线路。
 * 注意事项:
 * - 本入口只负责验证触感与节律，不承载最终多传感器联动逻辑。
 * - 当前先不写死具体 LRA 型号参数，优先验证“深呼吸式震动包络”是否符合体感预期。
 * - 独立 I2C 使用 D6(GPIO43) / D7(GPIO44)，避免与 IMU 的 D4/D5 和 PPG 的 D2/D3 冲突。
 */

#include <Arduino.h>
#include <Wire.h>

#include <Adafruit_DRV2605.h>

namespace {

constexpr uint32_t kSerialBaudRate = 115200;
constexpr unsigned long kStartupDelayMs = 300;
constexpr unsigned long kReconnectIntervalMs = 2000;
constexpr uint8_t kHapticI2cSdaPin = 43;
constexpr uint8_t kHapticI2cSclPin = 44;
constexpr uint32_t kHapticI2cClockHz = 100000;
constexpr unsigned long kEnvelopeUpdateIntervalMs = 25;
constexpr unsigned long kInhaleDurationMs = 4200;
constexpr unsigned long kExhaleDurationMs = 4200;
constexpr unsigned long kPauseDurationMs = 900;
constexpr uint8_t kInhaleMaxRtp = 0x68;
constexpr uint8_t kInhaleMinRtp = 0x20;
constexpr uint8_t kExhaleMaxRtp = 0x60;
constexpr uint8_t kExhaleMinRtp = 0x18;

TwoWire hapticWire = TwoWire(0);
Adafruit_DRV2605 hapticDriver;

bool driverReady = false;
unsigned long lastReconnectAtMs = 0;
unsigned long lastEnvelopeAtMs = 0;

struct BreathPhaseConfig {
  const char* name;
  unsigned long durationMs;
  uint8_t maxRtp;
  uint8_t minRtp;
};

enum class BreathPhase : uint8_t {
  kInhale = 0,
  kExhale = 1,
  kPause = 2,
};

constexpr BreathPhaseConfig kPhaseConfigs[] = {
    {"INHALE", kInhaleDurationMs, kInhaleMaxRtp, kInhaleMinRtp},
    {"EXHALE", kExhaleDurationMs, kExhaleMaxRtp, kExhaleMinRtp},
    {"PAUSE", kPauseDurationMs, 0x00, 0x00},
};

BreathPhase currentPhase = BreathPhase::kInhale;
unsigned long phaseStartedAtMs = 0;

uint8_t interpolateRtp(const BreathPhaseConfig& config, unsigned long elapsedMs) {
  if (config.durationMs == 0 || config.maxRtp <= config.minRtp) {
    return config.minRtp;
  }

  const unsigned long clampedElapsedMs = min(elapsedMs, config.durationMs);
  const uint32_t delta = static_cast<uint32_t>(config.maxRtp - config.minRtp);
  const uint32_t scaled = (delta * clampedElapsedMs) / config.durationMs;
  return static_cast<uint8_t>(config.maxRtp - scaled);
}

void printPhaseBanner(BreathPhase phase) {
  const BreathPhaseConfig& config = kPhaseConfigs[static_cast<size_t>(phase)];
  Serial.printf(
      "PHASE,%s,duration_ms=%lu,max_rtp=%u,min_rtp=%u\n",
      config.name,
      config.durationMs,
      config.maxRtp,
      config.minRtp);
}

void resetPatternState(unsigned long nowMs) {
  currentPhase = BreathPhase::kInhale;
  phaseStartedAtMs = nowMs;
  lastEnvelopeAtMs = 0;
  printPhaseBanner(currentPhase);
}

bool initializeDriver() {
  hapticWire.begin(kHapticI2cSdaPin, kHapticI2cSclPin);
  hapticWire.setClock(kHapticI2cClockHz);

  if (!hapticDriver.begin(&hapticWire)) {
    return false;
  }

  hapticDriver.useLRA();
  hapticDriver.selectLibrary(6);
  hapticDriver.setMode(DRV2605_MODE_REALTIME);
  hapticDriver.setRealtimeValue(0x00);
  return true;
}

void advancePhase(unsigned long nowMs) {
  switch (currentPhase) {
    case BreathPhase::kInhale:
      currentPhase = BreathPhase::kExhale;
      break;
    case BreathPhase::kExhale:
      currentPhase = BreathPhase::kPause;
      break;
    case BreathPhase::kPause:
      currentPhase = BreathPhase::kInhale;
      break;
  }

  phaseStartedAtMs = nowMs;
  printPhaseBanner(currentPhase);
}

void updateEnvelope(unsigned long nowMs) {
  const BreathPhaseConfig& config = kPhaseConfigs[static_cast<size_t>(currentPhase)];
  const unsigned long elapsedMs = nowMs - phaseStartedAtMs;

  if (elapsedMs >= config.durationMs) {
    advancePhase(nowMs);
  }

  const BreathPhaseConfig& activeConfig = kPhaseConfigs[static_cast<size_t>(currentPhase)];
  const unsigned long activeElapsedMs = nowMs - phaseStartedAtMs;
  const uint8_t rtpValue = currentPhase == BreathPhase::kPause
      ? 0x00
      : interpolateRtp(activeConfig, activeElapsedMs);

  hapticDriver.setRealtimeValue(rtpValue);
}

}  // namespace

void setup() {
  Serial.begin(kSerialBaudRate);
  delay(kStartupDelayMs);

  driverReady = initializeDriver();
  if (driverReady) {
    Serial.println("DRV2605L LRA breath probe ready");
    Serial.println("I2C pins: D6(GPIO43)=SDA, D7(GPIO44)=SCL");
    Serial.println("Pattern: inhale strong->weak, exhale strong->weak, short pause");
    resetPatternState(millis());
  } else {
    Serial.println("DRV2605L not found, retrying...");
  }
}

void loop() {
  const unsigned long nowMs = millis();

  if (!driverReady) {
    if (nowMs - lastReconnectAtMs < kReconnectIntervalMs) {
      return;
    }

    lastReconnectAtMs = nowMs;
    driverReady = initializeDriver();
    if (!driverReady) {
      Serial.println("DRV2605L not found, retrying...");
      return;
    }

    Serial.println("DRV2605L reconnected");
    resetPatternState(nowMs);
    return;
  }

  if (nowMs - lastEnvelopeAtMs < kEnvelopeUpdateIntervalMs) {
    return;
  }
  lastEnvelopeAtMs = nowMs;

  updateEnvelope(nowMs);
}
