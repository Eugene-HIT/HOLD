#include "passive_ppg_manager.h"

#include <math.h>

#include <Wire.h>

#include "heart_rate_estimator.h"
#include "max30102_raw_reader.h"
#include "project_config.h"

namespace hold_integration {
namespace {

constexpr float kChestDisplayDcAlpha = 0.18f;
constexpr float kChestDisplaySignalAlpha = 0.22f;
constexpr float kChestFilteredDisplayGain = 12.0f;
constexpr uint16_t kPassivePpgBatchIntervalMs = project_config::kSensorPollIntervalMs;

struct PpgDisplayState {
  bool initialized = false;
  float dcEstimateIr = 0.0f;
  float detrendedIr = 0.0f;
  float filteredIr = 0.0f;
};

Max30102RawReader ppgReader;
HeartRateEstimator heartRateEstimator;
PpgDisplayState displayState;
PassivePpgRealtimeBatch realtimeBatch;
bool ppgReady = false;
bool batchReady = false;
bool wasEnabled = false;
uint32_t lastSampleSequence = 0;

HeartRateEstimator::Profile buildChestProfile() {
  HeartRateEstimator::Profile profile = HeartRateEstimator::defaultFingerProfile();
  profile.presenceIrMeanThreshold = 1200;
  profile.presenceRedMeanThreshold = 0;
  profile.dcAlpha = 0.08f;
  profile.amplitudeMin = 3.0f;
  profile.amplitudeMax = 900.0f;
  profile.signalAlpha = 0.18f;
  profile.beatIntervalMinMs = 360;
  profile.beatIntervalMaxMs = 2400;
  profile.beatStaleTimeoutMs = 4500;
  profile.contactLossResetMs = 3000;
  profile.usePeakTroughDetector = true;
  return profile;
}

void resetDisplayState() {
  displayState = PpgDisplayState{};
}

void resetBatch() {
  realtimeBatch = PassivePpgRealtimeBatch{};
}

int16_t quantizePoint(float value) {
  const int32_t rounded = static_cast<int32_t>(lroundf(value));
  if (rounded < -32768) {
    return -32768;
  }
  if (rounded > 32767) {
    return 32767;
  }
  return static_cast<int16_t>(rounded);
}

void updateDisplayState(uint32_t irValue) {
  const float irSample = static_cast<float>(irValue);
  if (!displayState.initialized) {
    displayState.initialized = true;
    displayState.dcEstimateIr = irSample;
    return;
  }

  displayState.dcEstimateIr += (irSample - displayState.dcEstimateIr) * kChestDisplayDcAlpha;
  displayState.detrendedIr = irSample - displayState.dcEstimateIr;
  displayState.filteredIr +=
      (displayState.detrendedIr - displayState.filteredIr) * kChestDisplaySignalAlpha;
}

void flushBatch() {
  if (realtimeBatch.sampleCount > 0) {
    batchReady = true;
  }
}

void appendBatch(uint32_t sessionId, uint32_t nowMs, float filteredPoint,
                 float beatMarkerPoint, uint16_t bpm, uint8_t qualityScore,
                 bool contactPresent) {
  if (realtimeBatch.sampleCount >= kActiveRealtimeBatchCapacity) {
    flushBatch();
    if (batchReady) {
      return;
    }
  }

  if (realtimeBatch.sampleCount == 0) {
    realtimeBatch.sessionId = sessionId;
    realtimeBatch.sampleIntervalMs = kPassivePpgBatchIntervalMs;
  }

  const uint8_t index = realtimeBatch.sampleCount;
  realtimeBatch.filteredPoints[index] = quantizePoint(filteredPoint);
  realtimeBatch.beatMarkerPoints[index] = quantizePoint(beatMarkerPoint);
  realtimeBatch.sampleCount += 1;
  realtimeBatch.tsMsEnd = nowMs;
  realtimeBatch.heartRateBpm = bpm;
  realtimeBatch.qualityScore = qualityScore;
  realtimeBatch.contactPresent = contactPresent;
  realtimeBatch.active = true;

  if (realtimeBatch.sampleCount >= kActiveRealtimeBatchCapacity) {
    flushBatch();
  }
}

}  // namespace

void passivePpgManagerBegin(uint32_t nowMs) {
  (void)nowMs;
  resetDisplayState();
  resetBatch();
  batchReady = false;
  wasEnabled = false;
  lastSampleSequence = 0;
  heartRateEstimator.reset();
  heartRateEstimator.setProfile(buildChestProfile());
  ppgReady = ppgReader.begin(Wire);
}

void passivePpgManagerTick(uint32_t nowMs, bool enabled, uint32_t sessionId) {
  if (!ppgReady) {
    return;
  }

  if (enabled && !wasEnabled) {
    resetDisplayState();
    resetBatch();
    batchReady = false;
    lastSampleSequence = 0;
    heartRateEstimator.reset();
    heartRateEstimator.setProfile(buildChestProfile());
  }

  wasEnabled = enabled;
  if (!enabled) {
    flushBatch();
    return;
  }

  ppgReader.update();
  Max30102RawReader::Sample sample;
  if (!ppgReader.readLatestSample(sample) || sample.sequence == lastSampleSequence) {
    return;
  }

  lastSampleSequence = sample.sequence;
  updateDisplayState(sample.ir);
  heartRateEstimator.addSample(sample);

  const float filteredPoint = displayState.filteredIr * kChestFilteredDisplayGain;
  const float beatMarkerPoint = heartRateEstimator.beatDetectedRecently() ? 1000.0f : 0.0f;
  appendBatch(sessionId,
              nowMs,
              filteredPoint,
              beatMarkerPoint,
              heartRateEstimator.hasValidBpm() ? static_cast<uint16_t>(heartRateEstimator.bpm()) : 0,
              heartRateEstimator.contactPresent() ? 88 : 35,
              heartRateEstimator.contactPresent());
}

bool passivePpgManagerConsumeRealtimeBatch(PassivePpgRealtimeBatch *batch) {
  if (!batchReady || batch == nullptr) {
    return false;
  }

  *batch = realtimeBatch;
  resetBatch();
  batchReady = false;
  return true;
}

}  // namespace hold_integration