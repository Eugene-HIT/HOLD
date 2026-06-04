#include "heart_rate_estimator.h"

#include "project_config.h"

namespace {

float updateMovingAverage(float value,
                         float* window,
                         size_t window_size,
                         float& sum,
                         size_t& count,
                         size_t& index) {
  if (count < window_size) {
    window[index] = value;
    sum += value;
    ++count;
  } else {
    sum -= window[index];
    window[index] = value;
    sum += value;
  }

  index = (index + 1) % window_size;
  return sum / static_cast<float>(count);
}

}  // namespace

void HeartRateEstimator::reset() {
  *this = HeartRateEstimator{};
}

void HeartRateEstimator::resetTrackingState(bool clearBeatCount) {
  positive_edge_ = false;
  negative_edge_ = false;
  filtered_ir_ = 0.0f;
  previous_filtered_ir_ = 0.0f;
  signal_max_ = 0.0f;
  signal_min_ = 0.0f;
  last_amplitude_ = 0.0f;
  bpm_ = last_valid_bpm_;
  last_beat_at_ms_ = 0;
  last_beat_interval_ms_ = 0;
  beat_intervals_count_ = 0;
  beat_intervals_index_ = 0;
  signal_window_sum_ = 0.0f;
  signal_count_ = 0;
  signal_index_ = 0;
  if (clearBeatCount) {
    beat_count_ = 0;
    last_valid_bpm_ = 0.0f;
    bpm_ = 0.0f;
  }
  for (size_t index = 0; index < kSignalWindowSize; ++index) {
    signal_window_[index] = 0.0f;
  }
}

void HeartRateEstimator::addSample(const Max30102RawReader::Sample& sample) {
  last_ir_ = sample.ir;
  last_red_ = sample.red;
  beat_detected_recently_ = false;

  if (presence_count_ < kPresenceWindowSize) {
    ir_presence_window_[presence_index_] = sample.ir;
    red_presence_window_[presence_index_] = sample.red;
    ir_presence_sum_ += sample.ir;
    red_presence_sum_ += sample.red;
    ++presence_count_;
  } else {
    ir_presence_sum_ -= ir_presence_window_[presence_index_];
    red_presence_sum_ -= red_presence_window_[presence_index_];
    ir_presence_window_[presence_index_] = sample.ir;
    red_presence_window_[presence_index_] = sample.red;
    ir_presence_sum_ += sample.ir;
    red_presence_sum_ += sample.red;
  }
  presence_index_ = (presence_index_ + 1) % kPresenceWindowSize;

  average_ir_ = static_cast<uint32_t>(ir_presence_sum_ / static_cast<uint64_t>(presence_count_));
  average_red_ = static_cast<uint32_t>(red_presence_sum_ / static_cast<uint64_t>(presence_count_));
  const bool contact_detected =
      presence_count_ >= (kPresenceWindowSize / 2) &&
      average_ir_ >= project_config::kFingerPresentIrMeanThreshold &&
      average_red_ >= project_config::kFingerPresentRedMeanThreshold;
  if (contact_detected) {
    last_contact_at_ms_ = sample.capturedAtMs;
    finger_present_ = true;
  } else {
    finger_present_ =
        last_contact_at_ms_ > 0 &&
        (sample.capturedAtMs - last_contact_at_ms_) <= project_config::kHeartRateFingerLossResetMs;
  }

  if (!initialized_) {
    dc_estimate_ = static_cast<float>(sample.ir);
    initialized_ = true;
    return;
  }

  const float ir_value = static_cast<float>(sample.ir);

  if (!finger_present_) {
    dc_estimate_ = ir_value;
    resetTrackingState(true);
    return;
  }

  dc_estimate_ += (ir_value - dc_estimate_) * project_config::kHeartRateDcAlpha;

  previous_filtered_ir_ = filtered_ir_;
  const float detrended = ir_value - dc_estimate_;
  const float smoothed = updateMovingAverage(
      detrended,
      signal_window_,
      kSignalWindowSize,
      signal_window_sum_,
      signal_count_,
      signal_index_);
  filtered_ir_ += (smoothed - filtered_ir_) * project_config::kHeartRateSignalAlpha;

  if (last_beat_at_ms_ > 0 &&
      (sample.capturedAtMs - last_beat_at_ms_) > project_config::kHeartRateBeatStaleTimeoutMs) {
    resetTrackingState(false);
  }

  if (previous_filtered_ir_ < 0.0f && filtered_ir_ >= 0.0f) {
    last_amplitude_ = signal_max_ - signal_min_;
    positive_edge_ = true;
    negative_edge_ = false;
    signal_max_ = filtered_ir_;

    const unsigned long now_ms = sample.capturedAtMs;
    const unsigned long interval_ms = now_ms - last_beat_at_ms_;
    const bool interval_valid =
        last_beat_at_ms_ > 0 &&
        interval_ms >= project_config::kHeartRateBeatIntervalMinMs &&
        interval_ms <= project_config::kHeartRateBeatIntervalMaxMs;
    if (last_amplitude_ >= project_config::kHeartRateAmplitudeMin && interval_valid) {
      last_beat_at_ms_ = now_ms;
      last_beat_interval_ms_ = interval_ms;
      pushBeatInterval(interval_ms);
      bpm_ = averagedBpm();
      last_valid_bpm_ = bpm_;
      ++beat_count_;
      beat_detected_recently_ = true;
    } else if (last_beat_at_ms_ == 0 && last_amplitude_ >= project_config::kHeartRateAmplitudeMin) {
      last_beat_at_ms_ = now_ms;
      ++beat_count_;
      beat_detected_recently_ = true;
    }
  }

  if (previous_filtered_ir_ > 0.0f && filtered_ir_ <= 0.0f) {
    positive_edge_ = false;
    negative_edge_ = true;
    signal_min_ = filtered_ir_;
  }

  if (positive_edge_ && filtered_ir_ > signal_max_) {
    signal_max_ = filtered_ir_;
  }

  if (negative_edge_ && filtered_ir_ < signal_min_) {
    signal_min_ = filtered_ir_;
  }
}

bool HeartRateEstimator::hasValidBpm() const {
  return last_valid_bpm_ > 0.0f;
}

float HeartRateEstimator::bpm() const {
  return last_valid_bpm_ > 0.0f ? last_valid_bpm_ : bpm_;
}

bool HeartRateEstimator::fingerPresent() const {
  return finger_present_;
}

bool HeartRateEstimator::beatDetectedRecently() const {
  return beat_detected_recently_;
}

uint32_t HeartRateEstimator::lastIr() const {
  return last_ir_;
}

uint32_t HeartRateEstimator::lastRed() const {
  return last_red_;
}

uint32_t HeartRateEstimator::averageIr() const {
  return average_ir_;
}

uint32_t HeartRateEstimator::averageRed() const {
  return average_red_;
}

float HeartRateEstimator::filteredIr() const {
  return filtered_ir_;
}

float HeartRateEstimator::signalAmplitude() const {
  return last_amplitude_;
}

uint32_t HeartRateEstimator::beatCount() const {
  return beat_count_;
}

unsigned long HeartRateEstimator::lastBeatIntervalMs() const {
  return last_beat_interval_ms_;
}

void HeartRateEstimator::pushBeatInterval(unsigned long interval_ms) {
  beat_intervals_ms_[beat_intervals_index_] = interval_ms;
  beat_intervals_index_ = (beat_intervals_index_ + 1) % kBpmWindowSize;
  if (beat_intervals_count_ < kBpmWindowSize) {
    ++beat_intervals_count_;
  }
}

float HeartRateEstimator::averagedBpm() const {
  if (beat_intervals_count_ == 0) {
    return 0.0f;
  }

  unsigned long interval_sum_ms = 0;
  for (size_t index = 0; index < beat_intervals_count_; ++index) {
    interval_sum_ms += beat_intervals_ms_[index];
  }

  const float average_interval_ms =
      static_cast<float>(interval_sum_ms) / static_cast<float>(beat_intervals_count_);
  if (average_interval_ms <= 0.0f) {
    return 0.0f;
  }

  return 60000.0f / average_interval_ms;
}