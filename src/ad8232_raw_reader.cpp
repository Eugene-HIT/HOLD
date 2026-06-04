/*
 * 创建时间: 2026-05-25
 * 文件主要职责: 实现 AD8232 OUTPUT 模拟量最小读取、最近样本缓存与窗口统计。
 * 核心函数输入输出:
 * - begin(): 配置 ADC 输入和分辨率，并清空运行时状态。
 * - update(): 读取一次 ADC 原始值，更新最近样本、窗口最值和均值统计。
 * - resetWindowSummary(): 在一次串口输出后清空窗口统计，开始下一轮观测。
 * 最后更改时间: 2026-05-25
 * 累加式更改日志:
 * - 2026-05-25: 新建 AD8232 原始读取实现，用于首轮 OUTPUT 波形链路验证。
 * 注意事项:
 * - 当前只观察原始值、窗口均值与峰峰值，不做去基线、陷波或 QRS 检测。
 */

#include "ad8232_raw_reader.h"

#include "project_config.h"

bool Ad8232RawReader::begin() {
  pinMode(project_config::kAd8232AdcPin, INPUT);
  analogReadResolution(project_config::kAd8232AdcResolutionBits);

  is_initialized_ = true;
  has_sample_ = false;
  last_error_ = "ok";
  total_samples_read_ = 0;
  window_sum_raw_ = 0;
  latest_sample_ = {};
  window_summary_ = {};
  return true;
}

bool Ad8232RawReader::update() {
  if (!is_initialized_) {
    last_error_ = "not-initialized";
    return false;
  }

  const uint16_t raw_value = static_cast<uint16_t>(analogRead(project_config::kAd8232AdcPin));
  const unsigned long now_ms = millis();

  latest_sample_.rawValue = raw_value;
  latest_sample_.sequence += 1;
  latest_sample_.capturedAtMs = now_ms;

  if (!window_summary_.hasData) {
    window_summary_.hasData = true;
    window_summary_.minRaw = raw_value;
    window_summary_.maxRaw = raw_value;
    window_summary_.lastRaw = raw_value;
    window_summary_.peakToPeak = 0;
    window_summary_.meanRaw = raw_value;
    window_summary_.sampleCount = 1;
    window_summary_.lastSequence = latest_sample_.sequence;
    window_summary_.windowStartedAtMs = now_ms;
    window_summary_.lastUpdatedAtMs = now_ms;
    window_sum_raw_ = raw_value;
  } else {
    if (raw_value < window_summary_.minRaw) {
      window_summary_.minRaw = raw_value;
    }
    if (raw_value > window_summary_.maxRaw) {
      window_summary_.maxRaw = raw_value;
    }

    window_summary_.lastRaw = raw_value;
    window_summary_.sampleCount += 1;
    window_summary_.lastSequence = latest_sample_.sequence;
    window_summary_.lastUpdatedAtMs = now_ms;
    window_sum_raw_ += raw_value;
    window_summary_.meanRaw = static_cast<uint16_t>(window_sum_raw_ / window_summary_.sampleCount);
    window_summary_.peakToPeak = static_cast<uint16_t>(window_summary_.maxRaw - window_summary_.minRaw);
  }

  total_samples_read_ += 1;
  has_sample_ = true;
  last_error_ = "ok";
  return true;
}

bool Ad8232RawReader::readLatestSample(Sample& sample) const {
  if (!has_sample_) {
    return false;
  }

  sample = latest_sample_;
  return true;
}

bool Ad8232RawReader::readWindowSummary(WindowSummary& window_summary) const {
  if (!window_summary_.hasData) {
    return false;
  }

  window_summary = window_summary_;
  return true;
}

void Ad8232RawReader::resetWindowSummary() {
  window_summary_ = {};
  window_sum_raw_ = 0;
}

bool Ad8232RawReader::isInitialized() const {
  return is_initialized_;
}

const char* Ad8232RawReader::lastError() const {
  return last_error_;
}

uint64_t Ad8232RawReader::totalSamplesRead() const {
  return total_samples_read_;
}