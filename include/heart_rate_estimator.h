/*
 * 创建时间: 2026-05-23
 * 文件主要职责: 对 MAX30102 的 IR 原始信号做最小心率估计。
 * 核心函数输入输出:
 * - addSample(...): 输入最新 Red/IR 样本，更新内部滤波和心跳检测状态。
 * - hasValidBpm(): 返回当前是否已有可输出的 BPM。
 * - bpm(): 返回最近一次稳定 BPM。
 * 最后更改时间: 2026-05-23
 * 累加式更改日志:
 * - 2026-05-23: 新建简单心率估计模块，先服务于首轮 BPM 验证。
 * 注意事项:
 * - 当前实现只面向静止场景下的最小可运行验证，不承诺医学级准确性。
 */

#pragma once

#include <Arduino.h>

#include "max30102_raw_reader.h"

class HeartRateEstimator {
 public:
  struct Profile {
    uint32_t presenceIrMeanThreshold = 0;
    uint32_t presenceRedMeanThreshold = 0;
    float dcAlpha = 0.0f;
    float signalAlpha = 0.0f;
    float amplitudeMin = 0.0f;
    float amplitudeMax = 0.0f;
    unsigned long beatIntervalMinMs = 0;
    unsigned long beatIntervalMaxMs = 0;
    unsigned long beatStaleTimeoutMs = 0;
    unsigned long contactLossResetMs = 0;
    bool usePeakTroughDetector = false;
  };

  static Profile defaultFingerProfile();

  void reset();
  void setProfile(const Profile& profile);
  void addSample(const Max30102RawReader::Sample& sample);

  bool hasValidBpm() const;
  float bpm() const;
  bool fingerPresent() const;
  bool beatDetectedRecently() const;
  bool contactPresent() const;
  uint32_t lastIr() const;
  uint32_t lastRed() const;
  uint32_t averageIr() const;
  uint32_t averageRed() const;
  float filteredIr() const;
  float signalAmplitude() const;
  uint32_t beatCount() const;
  unsigned long lastBeatIntervalMs() const;

 private:
  static constexpr size_t kBpmWindowSize = 4;
  static constexpr size_t kPresenceWindowSize = 25;
  static constexpr size_t kSignalWindowSize = 4;

  void acceptBeatCandidate(unsigned long beat_at_ms, float amplitude);
  void updatePeakTroughDetector(unsigned long sample_at_ms);
  void pushBeatInterval(unsigned long interval_ms);
  float averagedBpm() const;
  void resetTrackingState(bool clearBeatCount);

  bool initialized_ = false;
  bool finger_present_ = false;
  bool positive_edge_ = false;
  bool negative_edge_ = false;
  bool beat_detected_recently_ = false;
  uint32_t last_ir_ = 0;
  uint32_t last_red_ = 0;
  uint32_t average_ir_ = 0;
  uint32_t average_red_ = 0;
  float dc_estimate_ = 0.0f;
  float filtered_ir_ = 0.0f;
  float previous_filtered_ir_ = 0.0f;
  float signal_max_ = 0.0f;
  float signal_min_ = 0.0f;
  float last_amplitude_ = 0.0f;
  float bpm_ = 0.0f;
  float last_valid_bpm_ = 0.0f;
  uint32_t beat_count_ = 0;
  unsigned long last_beat_at_ms_ = 0;
  unsigned long last_beat_interval_ms_ = 0;
  unsigned long last_contact_at_ms_ = 0;
  unsigned long previous_sample_at_ms_ = 0;
  unsigned long last_trough_at_ms_ = 0;
  unsigned long beat_intervals_ms_[kBpmWindowSize] = {};
  size_t beat_intervals_count_ = 0;
  size_t beat_intervals_index_ = 0;
  uint32_t ir_presence_window_[kPresenceWindowSize] = {};
  uint32_t red_presence_window_[kPresenceWindowSize] = {};
  uint64_t ir_presence_sum_ = 0;
  uint64_t red_presence_sum_ = 0;
  size_t presence_count_ = 0;
  size_t presence_index_ = 0;
  float signal_window_[kSignalWindowSize] = {};
  float signal_window_sum_ = 0.0f;
  size_t signal_count_ = 0;
  size_t signal_index_ = 0;
  float previous_slope_ = 0.0f;
  float last_trough_value_ = 0.0f;
  bool has_trough_ = false;
  Profile profile_{};
};