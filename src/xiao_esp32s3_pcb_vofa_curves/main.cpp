/*
 * 创建时间: 2026-07-28
 * 文件主要职责: 在当前 PCB 飞线样机上复用胸口 PPG VOFA 算法，输出 MAX30102 胸口模式完整调试通道。
 * 核心函数输入输出:
 * - setup(): 默认拉高 TPS_EN/M_EN，关闭加热，初始化主 I2C 与 MAX30102，并装载胸口 PPG 参数组。
 * - loop(): 轮询 FIFO，更新胸口 PPG 显示链路与心率估计器，持续输出原 chest_vofa 的 13 通道 CSV。
 * 最后更改时间: 2026-07-28
 * 累加式更改日志:
 * - 2026-07-28: 将 PCB VOFA 工程改为完整复用 chest_vofa 算法与输出，只补充当前 PCB 电源/EN/加热脚状态。
 * 注意事项:
 * - 串口只输出 CSV 数字，不输出文本说明，避免污染 VOFA 曲线。
 * - 当前固件不主动驱动加热，HEAT_CTRL 固定为 LOW。
 */

#include <Arduino.h>
#include <Wire.h>

#include "heart_rate_estimator.h"
#include "max30102_raw_reader.h"
#include "project_config.h"

namespace {

constexpr uint32_t kSerialBaudRate = 115200;
constexpr unsigned long kStartupDelayMs = 300;
constexpr unsigned long kPowerEnableSettleMs = 80;
constexpr unsigned long kReconnectIntervalMs = 2000;
constexpr unsigned long kVofaOutputIntervalMs = project_config::kSensorPollIntervalMs;
constexpr float kChestDisplayDcAlpha = 0.18f;
constexpr float kChestDisplaySignalAlpha = 0.22f;
constexpr float kChestFilteredDisplayGain = 12.0f;

constexpr uint8_t kSensorPowerEnablePin = 43;  // D6, TPS_EN
constexpr uint8_t kHapticEnablePin = 44;       // D7, M_EN
constexpr uint8_t kHeaterControlPin = 2;       // D1, HEAT_CTRL, forced off

struct PpgDisplayState {
  bool initialized = false;
  float dcEstimateIr = 0.0f;
  float detrendedIr = 0.0f;
  float filteredIr = 0.0f;
};

HeartRateEstimator::Profile buildChestProfile() {
  HeartRateEstimator::Profile profile = HeartRateEstimator::defaultFingerProfile();
  profile.presenceIrMeanThreshold = 1200;
  profile.presenceRedMeanThreshold = 0;
  profile.dcAlpha = 0.08f;
  profile.amplitudeMin = 3.0f;
  profile.amplitudeMax = 900.0f;
  profile.signalAlpha = 0.18f;
  profile.beatIntervalMinMs = 360;
  profile.beatIntervalMaxMs = 2400;
  profile.beatStaleTimeoutMs = 4500;
  profile.contactLossResetMs = 3000;
  profile.usePeakTroughDetector = true;
  return profile;
}

Max30102RawReader max30102;
HeartRateEstimator heartRateEstimator;
PpgDisplayState ppgDisplayState;

bool sensorReady = false;
unsigned long lastPollAtMs = 0;
unsigned long lastRetryAtMs = 0;
unsigned long lastVofaAtMs = 0;
uint32_t lastProcessedSequence = 0;

void setupPcbPowerPins() {
  pinMode(kSensorPowerEnablePin, OUTPUT);
  pinMode(kHapticEnablePin, OUTPUT);
  pinMode(kHeaterControlPin, OUTPUT);
  digitalWrite(kSensorPowerEnablePin, HIGH);
  digitalWrite(kHapticEnablePin, HIGH);
  digitalWrite(kHeaterControlPin, LOW);
}

void resetDisplayState() {
  ppgDisplayState = PpgDisplayState{};
}

void updateDisplayState(uint32_t irValue) {
  const float irSample = static_cast<float>(irValue);
  if (!ppgDisplayState.initialized) {
    ppgDisplayState.initialized = true;
    ppgDisplayState.dcEstimateIr = irSample;
    return;
  }

  ppgDisplayState.dcEstimateIr +=
      (irSample - ppgDisplayState.dcEstimateIr) * kChestDisplayDcAlpha;
  ppgDisplayState.detrendedIr = irSample - ppgDisplayState.dcEstimateIr;
  ppgDisplayState.filteredIr +=
      (ppgDisplayState.detrendedIr - ppgDisplayState.filteredIr) * kChestDisplaySignalAlpha;
}

void initializeSensor() {
  Wire.begin(project_config::kI2cSdaPin, project_config::kI2cSclPin);
  Wire.setClock(project_config::kI2cClockHz);

  sensorReady = max30102.begin(Wire);
  if (!sensorReady) {
    return;
  }

  heartRateEstimator.reset();
  heartRateEstimator.setProfile(buildChestProfile());
  resetDisplayState();
  lastProcessedSequence = 0;
}

void printVofaFrame(unsigned long nowMs, const Max30102RawReader::Sample& sample) {
  const float beatMarker = heartRateEstimator.beatDetectedRecently() ? 1000.0f : 0.0f;
  const float bpmValue = heartRateEstimator.hasValidBpm() ? heartRateEstimator.bpm() : 0.0f;
  const float contactPresent = heartRateEstimator.contactPresent() ? 1.0f : 0.0f;
  const float detectorFilteredIr = heartRateEstimator.filteredIr();
  const float signalAmplitude = heartRateEstimator.signalAmplitude();
  const unsigned long lastBeatIntervalMs = heartRateEstimator.lastBeatIntervalMs();

  Serial.printf(
      "%lu,%lu,%lu,%lu,%lu,%.2f,%.2f,%.2f,%.2f,%.0f,%.2f,%.2f,%lu\n",
      nowMs,
      static_cast<unsigned long>(sample.ir),
      static_cast<unsigned long>(sample.red),
      static_cast<unsigned long>(heartRateEstimator.averageIr()),
      static_cast<unsigned long>(heartRateEstimator.averageRed()),
      ppgDisplayState.detrendedIr,
      ppgDisplayState.filteredIr * kChestFilteredDisplayGain,
      beatMarker,
      bpmValue,
      contactPresent,
      detectorFilteredIr,
      signalAmplitude,
      lastBeatIntervalMs);
}

}  // namespace

void setup() {
  setupPcbPowerPins();
  delay(kPowerEnableSettleMs);

  Serial.begin(kSerialBaudRate);
  delay(kStartupDelayMs);
  initializeSensor();
}

void loop() {
  const unsigned long nowMs = millis();

  if (!sensorReady) {
    if (nowMs - lastRetryAtMs < kReconnectIntervalMs) {
      return;
    }

    lastRetryAtMs = nowMs;
    initializeSensor();
    return;
  }

  if (nowMs - lastPollAtMs < project_config::kSensorPollIntervalMs) {
    return;
  }
  lastPollAtMs = nowMs;

  max30102.update();

  Max30102RawReader::Sample sample;
  if (!max30102.readLatestSample(sample)) {
    return;
  }

  if (sample.sequence == lastProcessedSequence) {
    return;
  }
  lastProcessedSequence = sample.sequence;

  updateDisplayState(sample.ir);
  heartRateEstimator.addSample(sample);

  if (nowMs - lastVofaAtMs < kVofaOutputIntervalMs) {
    return;
  }
  lastVofaAtMs = nowMs;
  printVofaFrame(nowMs, sample);
}
