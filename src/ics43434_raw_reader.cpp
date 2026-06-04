/*
 * 创建时间: 2026-05-25
 * 文件主要职责: 实现 ICS43434 的 I2S 初始化、批量样本读取与窗口统计。
 * 核心函数输入输出:
 * - begin(): 安装 I2S 驱动并绑定 BCLK/WS/DIN 引脚。
 * - update(): 读取一批 32 位 I2S 样本，转换为可观测统计量。
 * - resetWindowSummary(): 在串口输出后清空当前观测窗口，开始下一轮统计。
 * 最后更改时间: 2026-05-25
 * 累加式更改日志:
 * - 2026-05-25: 新建 ICS43434 原始读取实现，支持首轮最小可观测验证。
 * 注意事项:
 * - ICS43434 常见输出为 24 位有效数据左对齐到 32 位容器，本实现按右移 8 位归一化后做统计。
 * - 当前只做样本能量级观察，不对音频幅值做绝对标定。
 */

#include "ics43434_raw_reader.h"

#include <driver/i2s.h>

#include "project_config.h"

namespace {

constexpr i2s_port_t kMicrophoneI2sPort = I2S_NUM_0;

}  // namespace

bool Ics43434RawReader::begin() {
  end();
  resetRuntimeState();

  const i2s_config_t config = {
      .mode = static_cast<i2s_mode_t>(I2S_MODE_MASTER | I2S_MODE_RX),
      .sample_rate = project_config::kMicrophoneSampleRateHz,
      .bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT,
      .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
      .communication_format = I2S_COMM_FORMAT_STAND_I2S,
      .intr_alloc_flags = 0,
      .dma_buf_count = static_cast<int>(project_config::kMicrophoneDmaBufferCount),
      .dma_buf_len = static_cast<int>(project_config::kMicrophoneDmaBufferLength),
      .use_apll = false,
      .tx_desc_auto_clear = false,
      .fixed_mclk = 0,
  };

  const i2s_pin_config_t pin_config = {
      .bck_io_num = project_config::kMicrophoneBclkPin,
      .ws_io_num = project_config::kMicrophoneWsPin,
      .data_out_num = I2S_PIN_NO_CHANGE,
      .data_in_num = project_config::kMicrophoneDataPin,
  };

  if (i2s_driver_install(kMicrophoneI2sPort, &config, 0, nullptr) != ESP_OK) {
    last_error_ = "driver-install-failed";
    return false;
  }

  if (i2s_set_pin(kMicrophoneI2sPort, &pin_config) != ESP_OK) {
    last_error_ = "pin-config-failed";
    i2s_driver_uninstall(kMicrophoneI2sPort);
    return false;
  }

  if (i2s_zero_dma_buffer(kMicrophoneI2sPort) != ESP_OK) {
    last_error_ = "dma-reset-failed";
    i2s_driver_uninstall(kMicrophoneI2sPort);
    return false;
  }

  is_initialized_ = true;
  last_error_ = "ok";
  return true;
}

void Ics43434RawReader::end() {
  if (!is_initialized_) {
    return;
  }

  i2s_driver_uninstall(kMicrophoneI2sPort);
  is_initialized_ = false;
}

bool Ics43434RawReader::update() {
  if (!is_initialized_) {
    return false;
  }

  size_t bytes_read = 0;
  const esp_err_t read_result = i2s_read(
      kMicrophoneI2sPort,
      sample_buffer_,
      project_config::kMicrophoneBatchSampleCount * sizeof(sample_buffer_[0]),
      &bytes_read,
      0);

  last_bytes_read_ = bytes_read;
  if (read_result != ESP_OK) {
    ++read_error_count_;
    last_error_ = "read-failed";
    return false;
  }

  const size_t sample_count = bytes_read / sizeof(sample_buffer_[0]);
  if (sample_count == 0) {
    ++empty_read_count_;
    last_error_ = "no-data";
    return false;
  }

  BatchStats batch_stats;
  batch_stats.sequence = latest_batch_.sequence + 1;
  batch_stats.sampleCount = sample_count;
  batch_stats.capturedAtMs = millis();

  int32_t normalized_sample = sample_buffer_[0] >> 8;
  batch_stats.minSample = normalized_sample;
  batch_stats.maxSample = normalized_sample;
  uint64_t batch_abs_sum = static_cast<uint64_t>(abs(normalized_sample));

  for (size_t index = 1; index < sample_count; ++index) {
    normalized_sample = sample_buffer_[index] >> 8;
    if (normalized_sample < batch_stats.minSample) {
      batch_stats.minSample = normalized_sample;
    }
    if (normalized_sample > batch_stats.maxSample) {
      batch_stats.maxSample = normalized_sample;
    }
    batch_abs_sum += static_cast<uint64_t>(abs(normalized_sample));
  }

  batch_stats.peakToPeak = static_cast<uint32_t>(
      static_cast<int64_t>(batch_stats.maxSample) -
      static_cast<int64_t>(batch_stats.minSample));
  batch_stats.meanAbs = static_cast<uint32_t>(batch_abs_sum / sample_count);

  latest_batch_ = batch_stats;
  has_batch_ = true;
  total_samples_read_ += sample_count;
  last_read_at_ms_ = batch_stats.capturedAtMs;
  accumulateWindowStats(batch_stats, batch_abs_sum);
  last_error_ = "ok";
  return true;
}

bool Ics43434RawReader::readLatestBatch(BatchStats& batch_stats) const {
  if (!has_batch_) {
    return false;
  }

  batch_stats = latest_batch_;
  return true;
}

bool Ics43434RawReader::readWindowSummary(WindowSummary& window_summary) const {
  if (!window_summary_.hasData) {
    return false;
  }

  window_summary = window_summary_;
  return true;
}

void Ics43434RawReader::resetWindowSummary() {
  window_summary_ = {};
  window_abs_sum_ = 0;
}

bool Ics43434RawReader::isInitialized() const {
  return is_initialized_;
}

const char* Ics43434RawReader::lastError() const {
  return last_error_;
}

uint64_t Ics43434RawReader::totalSamplesRead() const {
  return total_samples_read_;
}

uint32_t Ics43434RawReader::emptyReadCount() const {
  return empty_read_count_;
}

uint32_t Ics43434RawReader::readErrorCount() const {
  return read_error_count_;
}

size_t Ics43434RawReader::lastBytesRead() const {
  return last_bytes_read_;
}

unsigned long Ics43434RawReader::lastReadAtMs() const {
  return last_read_at_ms_;
}

void Ics43434RawReader::resetRuntimeState() {
  is_initialized_ = false;
  has_batch_ = false;
  last_error_ = "starting";
  total_samples_read_ = 0;
  empty_read_count_ = 0;
  read_error_count_ = 0;
  last_bytes_read_ = 0;
  last_read_at_ms_ = 0;
  latest_batch_ = {};
  resetWindowSummary();
}

void Ics43434RawReader::accumulateWindowStats(
    const BatchStats& batch_stats,
    uint64_t batch_abs_sum) {
  if (!window_summary_.hasData) {
    window_summary_.hasData = true;
    window_summary_.minSample = batch_stats.minSample;
    window_summary_.maxSample = batch_stats.maxSample;
    window_summary_.windowStartedAtMs = batch_stats.capturedAtMs;
  } else {
    if (batch_stats.minSample < window_summary_.minSample) {
      window_summary_.minSample = batch_stats.minSample;
    }
    if (batch_stats.maxSample > window_summary_.maxSample) {
      window_summary_.maxSample = batch_stats.maxSample;
    }
  }

  window_summary_.sampleCount += batch_stats.sampleCount;
  window_summary_.batchCount += 1;
  window_summary_.lastSequence = batch_stats.sequence;
  window_summary_.lastUpdatedAtMs = batch_stats.capturedAtMs;
  window_abs_sum_ += batch_abs_sum;
  window_summary_.peakToPeak = static_cast<uint32_t>(
      static_cast<int64_t>(window_summary_.maxSample) -
      static_cast<int64_t>(window_summary_.minSample));
  window_summary_.meanAbs = static_cast<uint32_t>(
      window_abs_sum_ / window_summary_.sampleCount);
}