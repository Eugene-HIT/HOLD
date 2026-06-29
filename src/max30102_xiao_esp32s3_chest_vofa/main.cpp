/*
 * 创建时间: 2026-06-23
 * 文件主要职责: 在 XIAO ESP32S3 + MAX30102 上提供胸口贴肤场景专用的 VOFA 波形输出，用于首轮胸口 PPG 参数摸底。
 * 核心函数输入输出:
 * - setup(): 初始化串口、I2C 与 MAX30102，并装载胸口专用 PPG 参数组。
 * - loop(): 轮询 FIFO，更新原始 PPG 与轻处理显示量，持续输出胸口模式 12 通道 VOFA 数据。
 * 最后更改时间: 2026-06-23
 * 累加式更改日志:
 * - 2026-06-23: 基于手指版独立入口新增胸口版最小实验环境，先分离参数组而不污染手指版。
 * - 2026-06-23: 胸口版显示链路改为去呼吸基线 + 心跳带限增强，减少随呼吸上下漂移。
 * - 2026-06-23: 根据胸口实测反馈撤掉显示滤波，只保留快速去直流显示，避免贴肤后收敛过慢。
 * - 2026-06-23: 恢复轻量高频平滑以压低锯齿，同时继续降低胸口 beat 触发门限。
 * - 2026-06-23: 追加 contact / detector_filtered / signal_amplitude 调试通道，便于判断胸口版触发卡点。
 * - 2026-06-23: 根据调试数据继续放宽胸口检测链，使内部 detector 波形更接近当前可见胸口波形。
 * - 2026-06-23: 胸口版增加特大幅值扰动剔除，并将 beat_marker 改为高可见度事件脉冲。
 * 注意事项:
 * - 当前版本只是胸口首轮试验参数组，不是最终胸口产品算法。
 * - 胸口位点波形通常弱于手指，因此本版放宽接触阈值、降低 beat 幅值门限，并提高显示增益。
 */

#include <Arduino.h>
#include <Wire.h>

#include "heart_rate_estimator.h"
#include "max30102_raw_reader.h"
#include "project_config.h"

namespace {

constexpr uint32_t kSerialBaudRate = 115200;
constexpr unsigned long kStartupDelayMs = 300;
constexpr unsigned long kReconnectIntervalMs = 2000;
constexpr unsigned long kVofaOutputIntervalMs = project_config::kSensorPollIntervalMs;
constexpr uint8_t kPpgI2cSdaPin = 3;
constexpr uint8_t kPpgI2cSclPin = 4;
constexpr float kChestDisplayDcAlpha = 0.18f;
constexpr float kChestDisplaySignalAlpha = 0.22f;
constexpr float kChestFilteredDisplayGain = 12.0f;

struct PpgDisplayState {
  bool initialized = false;
  float dcEstimateIr = 0.0f;
  float detrendedIr = 0.0f;
  float filteredIr = 0.0f;
};

HeartRateEstimator::Profile buildChestProfile() {
  HeartRateEstimator::Profile profile = HeartRateEstimator::defaultFingerProfile();
  // 胸口位点先以 IR 为主做接触存在判断，避免 Red 通道偏弱导致整段被重置。
  profile.presenceIrMeanThreshold = 1200;
  profile.presenceRedMeanThreshold = 0;
  // 调试数据表明接触已稳定，但内部 detector 幅值仍偏小，因此继续贴近显示链并下调幅值门限。
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

  // 胸口版显示侧保留快速去直流，优先保证贴肤后能尽快看到原始起伏。
  ppgDisplayState.dcEstimateIr +=
      (irSample - ppgDisplayState.dcEstimateIr) * kChestDisplayDcAlpha;
  ppgDisplayState.detrendedIr = irSample - ppgDisplayState.dcEstimateIr;

  // 这里恢复和手指版同类型的轻量高频平滑，只压锯齿，不再引入慢收敛的低频基线滤波。
  ppgDisplayState.filteredIr +=
      (ppgDisplayState.detrendedIr - ppgDisplayState.filteredIr) * kChestDisplaySignalAlpha;
}

void initializeSensor() {
  Wire.begin(kPpgI2cSdaPin, kPpgI2cSclPin);
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

  Serial.printf(
      "%lu,%lu,%lu,%lu,%lu,%.2f,%.2f,%.2f,%.2f,%.0f,%.2f,%.2f\n",
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
      signalAmplitude);
}

}  // namespace

void setup() {
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