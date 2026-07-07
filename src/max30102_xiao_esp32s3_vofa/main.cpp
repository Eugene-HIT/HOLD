/*
 * 创建时间: 2026-06-09
 * 文件主要职责: 在 XIAO ESP32S3 + MAX30102 上提供独立的 8 通道 VOFA 波形输出，用于手指与胸前位点对比展示。
 * 核心函数输入输出:
 * - setup(): 初始化串口、I2C 与 MAX30102，准备进入纯 VOFA 输出模式。
 * - loop(): 轮询 FIFO，更新原始 PPG 与轻处理显示量，持续输出 8 通道 FireWater 数据。
 * 最后更改时间: 2026-06-30
 * 累加式更改日志:
 * - 2026-06-09: 新建独立 PPG VOFA 实验入口，复用 MAX30102 reader 与心率估计模块。
 * - 2026-06-30: 将指部 VOFA 入口的 MAX30102 接线切回整机一致的主 I2C D4/D5，便于在完整设备接线下直接做 VOFA 波形测试。
 * 注意事项:
 * - 本入口只服务于“可视化展示与位点对比”，不是最终产品算法实现。
 * - 当前 8 通道输出同时兼顾手指与胸前对比，因此更偏基础波形与轻处理量展示。
 * - VOFA 通道顺序固定，便于直接录制对比视频。
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

struct PpgDisplayState {
  bool initialized = false;
  float dcEstimateIr = 0.0f;
  float detrendedIr = 0.0f;
  float filteredIr = 0.0f;
};

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

  ppgDisplayState.dcEstimateIr +=
      (irSample - ppgDisplayState.dcEstimateIr) * project_config::kHeartRateDcAlpha;
  ppgDisplayState.detrendedIr = irSample - ppgDisplayState.dcEstimateIr;
  ppgDisplayState.filteredIr +=
      (ppgDisplayState.detrendedIr - ppgDisplayState.filteredIr) * project_config::kHeartRateSignalAlpha;
}

void initializeSensor() {
  Wire.begin(project_config::kI2cSdaPin, project_config::kI2cSclPin);
  Wire.setClock(project_config::kI2cClockHz);

  sensorReady = max30102.begin(Wire);
  if (!sensorReady) {
    return;
  }

  heartRateEstimator.reset();
  resetDisplayState();
  lastProcessedSequence = 0;
}

void printVofaFrame(unsigned long nowMs, const Max30102RawReader::Sample& sample) {
  const float beatMarker = heartRateEstimator.beatDetectedRecently()
      ? ppgDisplayState.filteredIr * project_config::kMax30102VofaFilteredDisplayGain
      : 0.0f;
  const float bpmValue = heartRateEstimator.hasValidBpm() ? heartRateEstimator.bpm() : 0.0f;

  Serial.printf(
    "%lu,%lu,%lu,%lu,%lu,%.2f,%.2f,%.2f,%.2f\n",
    nowMs,
      static_cast<unsigned long>(sample.ir),
      static_cast<unsigned long>(sample.red),
      static_cast<unsigned long>(heartRateEstimator.averageIr()),
      static_cast<unsigned long>(heartRateEstimator.averageRed()),
      ppgDisplayState.detrendedIr,
      ppgDisplayState.filteredIr * project_config::kMax30102VofaFilteredDisplayGain,
      beatMarker,
      bpmValue);
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