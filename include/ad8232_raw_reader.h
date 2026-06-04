/*
 * 创建时间: 2026-05-25
 * 文件主要职责: 声明 AD8232 单导联生物电模块的最小 ADC 原始读取接口。
 * 核心函数输入输出:
 * - begin(): 初始化 ADC 输入脚与运行时统计状态。
 * - update(): 读取一次 AD8232 OUTPUT 模拟值，并刷新最近样本与窗口统计。
 * - readWindowSummary(...): 输出当前观测窗口内的原始波形统计，供串口最小观测使用。
 * 最后更改时间: 2026-05-25
 * 累加式更改日志:
 * - 2026-05-25: 新建 AD8232 原始读取模块接口，服务于首轮生物电链路验证。
 * 注意事项:
 * - 当前模块只负责 OUTPUT 原始 ADC 读取，不负责导联脱落判断和 ECG 算法分析。
 */

#pragma once

#include <Arduino.h>

class Ad8232RawReader {
 public:
  struct Sample {
    uint16_t rawValue = 0;
    uint32_t sequence = 0;
    unsigned long capturedAtMs = 0;
  };

  struct WindowSummary {
    bool hasData = false;
    uint16_t minRaw = 0;
    uint16_t maxRaw = 0;
    uint16_t lastRaw = 0;
    uint16_t peakToPeak = 0;
    uint16_t meanRaw = 0;
    size_t sampleCount = 0;
    uint32_t lastSequence = 0;
    unsigned long windowStartedAtMs = 0;
    unsigned long lastUpdatedAtMs = 0;
  };

  bool begin();
  bool update();
  bool readLatestSample(Sample& sample) const;
  bool readWindowSummary(WindowSummary& window_summary) const;
  void resetWindowSummary();

  bool isInitialized() const;
  const char* lastError() const;
  uint64_t totalSamplesRead() const;

 private:
  bool is_initialized_ = false;
  bool has_sample_ = false;
  const char* last_error_ = "not-started";
  uint64_t total_samples_read_ = 0;
  uint32_t window_sum_raw_ = 0;
  Sample latest_sample_{};
  WindowSummary window_summary_{};
};