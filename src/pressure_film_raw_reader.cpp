/*
 * 创建时间: 2026-05-25
 * 文件主要职责: 实现薄膜压力传感器模块 AO 模拟量读取、平均和 0-10 量化。
 * 核心函数输入输出:
 * - begin(): 配置 ADC 输入，并采集静置基线。
 * - update(): 对一组 ADC 样本求平均，再量化为 0-10。
 * - readAverageRaw(...): 输入采样次数，输出平均 ADC 原始值。
 * 最后更改时间: 2026-05-25
 * 累加式更改日志:
 * - 2026-05-25: 新建薄膜压力传感器最小读取实现。
 * 注意事项:
 * - 量化结果依赖启动后的静置基线和运行期观测到的最大增量，首轮目标是“好观察”，不是“精确标定”。
 */

#include "pressure_film_raw_reader.h"

#include "project_config.h"

bool PressureFilmRawReader::begin() {
  pinMode(project_config::kPressureAdcPin, INPUT);
  analogReadResolution(project_config::kPressureAdcResolutionBits);

  const uint16_t baseline_raw = readAverageRaw(project_config::kPressureBaselineSampleCount);
  quantizer_.reset(baseline_raw, project_config::kPressureMinimumRangeRaw);

  is_initialized_ = true;
  has_sample_ = false;
  last_error_ = "ok";
  latest_sample_ = {};
  return true;
}

bool PressureFilmRawReader::update() {
  if (!is_initialized_) {
    last_error_ = "not-initialized";
    return false;
  }

  const uint16_t raw_average = readAverageRaw(project_config::kPressureAverageSampleCount);

  latest_sample_.rawAverage = raw_average;
  latest_sample_.level = quantizer_.quantize(raw_average);
  latest_sample_.sequence += 1;
  latest_sample_.capturedAtMs = millis();
  has_sample_ = true;
  last_error_ = "ok";
  return true;
}

bool PressureFilmRawReader::readLatestSample(Sample& sample) const {
  if (!has_sample_) {
    return false;
  }

  sample = latest_sample_;
  return true;
}

bool PressureFilmRawReader::isInitialized() const {
  return is_initialized_;
}

const char* PressureFilmRawReader::lastError() const {
  return last_error_;
}

uint16_t PressureFilmRawReader::baselineRaw() const {
  return quantizer_.baselineRaw();
}

uint16_t PressureFilmRawReader::peakDeltaRaw() const {
  return quantizer_.peakDeltaRaw();
}

uint16_t PressureFilmRawReader::readAverageRaw(size_t sample_count) const {
  uint32_t sum = 0;
  for (size_t index = 0; index < sample_count; ++index) {
    sum += static_cast<uint32_t>(analogRead(project_config::kPressureAdcPin));
  }

  return static_cast<uint16_t>(sum / sample_count);
}