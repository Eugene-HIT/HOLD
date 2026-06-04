/*
 * 创建时间: 2026-05-25
 * 文件主要职责: 声明薄膜压力传感器模块 AO 模拟量读取接口。
 * 核心函数输入输出:
 * - begin(): 初始化 ADC 输入脚并建立静置基线。
 * - update(): 读取一组 ADC 样本，输出最近一次原始平均值与 0-10 等级。
 * - readLatestSample(...): 返回最近一次成功读取结果。
 * 最后更改时间: 2026-05-25
 * 累加式更改日志:
 * - 2026-05-25: 新建薄膜压力传感器最小读取模块接口。
 * 注意事项:
 * - 当前模块只服务于最小观察闭环，不做物理量标定。
 */

#pragma once

#include <Arduino.h>

#include "pressure_level_quantizer.h"

class PressureFilmRawReader {
 public:
  struct Sample {
    uint16_t rawAverage = 0;
    uint8_t level = 0;
    uint32_t sequence = 0;
    unsigned long capturedAtMs = 0;
  };

  bool begin();
  bool update();
  bool readLatestSample(Sample& sample) const;

  bool isInitialized() const;
  const char* lastError() const;
  uint16_t baselineRaw() const;
  uint16_t peakDeltaRaw() const;

 private:
  uint16_t readAverageRaw(size_t sample_count) const;

  bool is_initialized_ = false;
  bool has_sample_ = false;
  const char* last_error_ = "not-started";
  Sample latest_sample_{};
  PressureLevelQuantizer quantizer_{};
};