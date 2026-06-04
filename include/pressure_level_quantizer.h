/*
 * 创建时间: 2026-05-25
 * 文件主要职责: 将薄膜压力模块的 ADC 原始值转换为 0-10 的压力等级。
 * 核心函数输入输出:
 * - reset(...): 重置基线和峰值跟踪状态。
 * - quantize(...): 输入当前 ADC 原始值，输出 0-10 的整数等级。
 * 最后更改时间: 2026-05-25
 * 累加式更改日志:
 * - 2026-05-25: 新建压力等级量化器，用于薄膜压力模块最小可观测验证。
 * 注意事项:
 * - 当前量化结果是工程分级值，不代表真实物理压力单位。
 * - 量化器会记住启动后的静置基线，并使用运行期观测到的峰值做自适应缩放。
 */

#pragma once

#include <Arduino.h>

class PressureLevelQuantizer {
 public:
  void reset(uint16_t baseline_raw, uint16_t minimum_range_raw) {
    baseline_raw_ = baseline_raw;
    minimum_range_raw_ = minimum_range_raw;
    peak_delta_raw_ = 0;
  }

  uint8_t quantize(uint16_t raw_value) {
    const uint16_t delta_raw =
        raw_value > baseline_raw_ ? static_cast<uint16_t>(raw_value - baseline_raw_) : 0;

    if (delta_raw > peak_delta_raw_) {
      peak_delta_raw_ = delta_raw;
    }

    const uint16_t full_scale_delta = peak_delta_raw_ > minimum_range_raw_
                                          ? peak_delta_raw_
                                          : minimum_range_raw_;
    if (full_scale_delta == 0) {
      return 0;
    }

    const uint32_t numerator = static_cast<uint32_t>(delta_raw) * 10U;
    const uint8_t level = static_cast<uint8_t>((numerator + (full_scale_delta / 2U)) /
                                               full_scale_delta);
    return level > 10 ? 10 : level;
  }

  uint16_t baselineRaw() const {
    return baseline_raw_;
  }

  uint16_t peakDeltaRaw() const {
    return peak_delta_raw_;
  }

  uint16_t minimumRangeRaw() const {
    return minimum_range_raw_;
  }

 private:
  uint16_t baseline_raw_ = 0;
  uint16_t minimum_range_raw_ = 0;
  uint16_t peak_delta_raw_ = 0;
};