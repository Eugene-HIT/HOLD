/*
 * 创建时间: 2026-05-25
 * 文件主要职责: 声明 ICS43434 I2S 数字麦克风原始数据读取模块的对外接口。
 * 核心函数输入输出:
 * - begin(): 初始化 ESP32-S3 I2S 接收链路，返回是否成功进入可读状态。
 * - update(): 读取一批音频样本并刷新批次统计与窗口统计。
 * - readWindowSummary(...): 读取当前窗口统计结果，用于串口最小可观测输出。
 * 最后更改时间: 2026-05-25
 * 累加式更改日志:
 * - 2026-05-25: 新建 ICS43434 原始读取模块接口，服务于首轮麦克风链路验证。
 * 注意事项:
 * - 本模块当前只负责 I2S 接收与统计值输出，不负责录音保存、频谱分析或识别算法。
 */

#pragma once

#include <Arduino.h>

class Ics43434RawReader {
 public:
  struct BatchStats {
    int32_t minSample = 0;
    int32_t maxSample = 0;
    uint32_t peakToPeak = 0;
    uint32_t meanAbs = 0;
    size_t sampleCount = 0;
    uint32_t sequence = 0;
    unsigned long capturedAtMs = 0;
  };

  struct WindowSummary {
    bool hasData = false;
    int32_t minSample = 0;
    int32_t maxSample = 0;
    uint32_t peakToPeak = 0;
    uint32_t meanAbs = 0;
    size_t sampleCount = 0;
    size_t batchCount = 0;
    uint32_t lastSequence = 0;
    unsigned long windowStartedAtMs = 0;
    unsigned long lastUpdatedAtMs = 0;
  };

  bool begin();
  void end();
  bool update();
  bool readLatestBatch(BatchStats& batch_stats) const;
  bool readWindowSummary(WindowSummary& window_summary) const;
  void resetWindowSummary();

  bool isInitialized() const;
  const char* lastError() const;
  uint64_t totalSamplesRead() const;
  uint32_t emptyReadCount() const;
  uint32_t readErrorCount() const;
  size_t lastBytesRead() const;
  unsigned long lastReadAtMs() const;

 private:
  void resetRuntimeState();
  void accumulateWindowStats(const BatchStats& batch_stats, uint64_t batch_abs_sum);

  static constexpr size_t kBufferSampleCount = 160;

  bool is_initialized_ = false;
  bool has_batch_ = false;
  const char* last_error_ = "not-started";
  uint64_t total_samples_read_ = 0;
  uint32_t empty_read_count_ = 0;
  uint32_t read_error_count_ = 0;
  size_t last_bytes_read_ = 0;
  unsigned long last_read_at_ms_ = 0;
  uint64_t window_abs_sum_ = 0;
  BatchStats latest_batch_{};
  WindowSummary window_summary_{};
  int32_t sample_buffer_[kBufferSampleCount] = {};
};