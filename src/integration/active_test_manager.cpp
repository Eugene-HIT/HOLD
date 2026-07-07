#include "active_test_manager.h"

#include <math.h>

#include <Wire.h>

#include "heart_rate_estimator.h"
#include "project_config.h"

namespace hold_integration {
namespace {

constexpr float kChestDisplayDcAlpha = 0.18f;
constexpr float kChestDisplaySignalAlpha = 0.22f;
constexpr float kChestFilteredDisplayGain = 12.0f;
constexpr uint16_t kActiveRealtimeBatchIntervalMs = project_config::kSensorPollIntervalMs;

struct PpgDisplayState {
  bool initialized = false;
  float dcEstimateIr = 0.0f;
  float detrendedIr = 0.0f;
  float filteredIr = 0.0f;
};

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

Max30102RawReader ppgReader;
HeartRateEstimator heartRateEstimator;
PpgDisplayState displayState;
ActivePpgWindow readyWindow;
ActivePpgRealtimeSnapshot realtimeSnapshot;
ActivePpgRealtimeBatch realtimeBatch;
bool ppgReady = false;
bool windowReady = false;
bool realtimeSnapshotReady = false;
bool realtimeBatchReady = false;
bool completedEventPending = false;
bool wasEnabled = false;
uint32_t startedAtMs = 0;
uint32_t measurementId = 0;
uint32_t lastSampleSequence = 0;
uint32_t lastBeatCount = 0;
uint16_t pointIndex = 0;
uint16_t beatIndex = 0;

void resetDisplayState() {
  displayState = PpgDisplayState{};
}

void resetWindowState() {
  readyWindow = ActivePpgWindow{};
  windowReady = false;
  completedEventPending = false;
  pointIndex = 0;
  beatIndex = 0;
  lastBeatCount = 0;
}

void resetRealtimeState() {
  realtimeSnapshot = ActivePpgRealtimeSnapshot{};
  realtimeBatch = ActivePpgRealtimeBatch{};
  realtimeSnapshotReady = false;
  realtimeBatchReady = false;
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

void flushRealtimeBatch() {
  if (realtimeBatch.sampleCount > 0) {
    realtimeBatchReady = true;
  }
}

void appendRealtimeBatch(uint32_t sessionId,
                         uint32_t nowMs,
                         float filteredPoint,
                         float beatMarkerPoint,
                         uint16_t bpm,
                         uint16_t lastBeatIntervalMs,
                         uint8_t qualityScore,
                         uint16_t beatCount,
                         bool contactPresent) {
  if (realtimeBatch.sampleCount >= kActiveRealtimeBatchCapacity) {
    flushRealtimeBatch();
    if (realtimeBatchReady) {
      return;
    }
  }

  if (realtimeBatch.sampleCount == 0) {
    realtimeBatch.sessionId = sessionId;
    realtimeBatch.measurementId = measurementId;
    realtimeBatch.sampleIntervalMs = kActiveRealtimeBatchIntervalMs;
  }

  const uint8_t index = realtimeBatch.sampleCount;
  realtimeBatch.filteredPoints[index] = quantizePoint(filteredPoint);
  realtimeBatch.beatMarkerPoints[index] = quantizePoint(beatMarkerPoint);
  realtimeBatch.sampleCount += 1;
  realtimeBatch.tsMsEnd = nowMs;
  realtimeBatch.heartRateBpm = bpm;
  realtimeBatch.lastBeatIntervalMs = lastBeatIntervalMs;
  realtimeBatch.qualityScore = qualityScore;
  realtimeBatch.beatCount = beatCount;
  realtimeBatch.contactPresent = contactPresent;
  realtimeBatch.active = true;

  if (realtimeBatch.sampleCount >= kActiveRealtimeBatchCapacity) {
    flushRealtimeBatch();
  }
}

void beginMeasurement(uint32_t nowMs, uint32_t sessionId) {
  measurementId += 1;
  startedAtMs = nowMs;
  lastSampleSequence = 0;
  heartRateEstimator.reset();
  heartRateEstimator.setProfile(buildChestProfile());
  resetDisplayState();
  resetWindowState();
  resetRealtimeState();

  realtimeSnapshot.active = true;
  realtimeSnapshot.measurementId = measurementId;
  realtimeSnapshot.sessionId = sessionId;
  realtimeSnapshot.tsMs = nowMs;
}

void storeProcessedPoint(float filteredPoint) {
  if (pointIndex >= kActiveProcessedPointCapacity) {
    return;
  }

  const int32_t normalized = static_cast<int32_t>(filteredPoint + 32768.0f);
  const uint16_t clipped = normalized < 0
    ? 0
    : (normalized > 65535 ? 65535 : static_cast<uint16_t>(normalized));
  readyWindow.processedPoints[pointIndex] = clipped;
  pointIndex += 1;
}

void storeBeatTimestamp(uint32_t capturedAtMs) {
  const uint32_t currentBeatCount = heartRateEstimator.beatCount();
  if (currentBeatCount == lastBeatCount) {
    return;
  }

  lastBeatCount = currentBeatCount;
  const unsigned long intervalMs = heartRateEstimator.lastBeatIntervalMs();
  if (intervalMs == 0) {
    return;
  }

  if (beatIndex < kActiveBeatCapacity) {
    readyWindow.beatTsMs[beatIndex] = capturedAtMs;
    readyWindow.rrIntervalsMs[beatIndex] =
        intervalMs > 65535UL ? 65535U : static_cast<uint16_t>(intervalMs);
    beatIndex += 1;
    readyWindow.rrIntervalCount = beatIndex;
  }
}

}  // namespace

void activeTestManagerBegin(uint32_t nowMs) {
  (void)nowMs;
  heartRateEstimator.reset();
  heartRateEstimator.setProfile(buildChestProfile());
  resetDisplayState();
  resetWindowState();
  resetRealtimeState();
  measurementId = 0;
  startedAtMs = 0;
  lastSampleSequence = 0;
  wasEnabled = false;
  ppgReady = ppgReader.begin(Wire);
  Serial.printf("[active-ppg] init=%s err=%s\n", ppgReady ? "ok" : "miss", ppgReader.lastError());
}

void activeTestManagerTick(uint32_t nowMs, bool enabled, uint32_t sessionId) {
  if (!ppgReady) {
    return;
  }

  if (enabled && !wasEnabled) {
    beginMeasurement(nowMs, sessionId);
  }

  wasEnabled = enabled;
  if (!enabled) {
    flushRealtimeBatch();
    realtimeSnapshot.active = false;
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
  const uint16_t bpm = heartRateEstimator.hasValidBpm()
    ? static_cast<uint16_t>(heartRateEstimator.bpm())
    : 0;
  const uint16_t lastBeatIntervalMs = heartRateEstimator.lastBeatIntervalMs() > 65535UL
    ? 65535U
    : static_cast<uint16_t>(heartRateEstimator.lastBeatIntervalMs());
  const uint8_t qualityScore = heartRateEstimator.contactPresent() ? 88 : 35;
  const bool contactPresent = heartRateEstimator.contactPresent();

  realtimeSnapshot.active = true;
  realtimeSnapshot.sessionId = sessionId;
  realtimeSnapshot.measurementId = measurementId;
  realtimeSnapshot.tsMs = nowMs;
  realtimeSnapshot.filteredPoint = filteredPoint;
  realtimeSnapshot.beatMarkerPoint = beatMarkerPoint;
  realtimeSnapshot.heartRateBpm = bpm;
  realtimeSnapshot.lastBeatIntervalMs = lastBeatIntervalMs;
  realtimeSnapshot.qualityScore = qualityScore;
  realtimeSnapshot.contactPresent = contactPresent;

  storeProcessedPoint(filteredPoint);
  storeBeatTimestamp(sample.capturedAtMs);

  realtimeSnapshot.beatCount = beatIndex;
  realtimeSnapshotReady = true;
  appendRealtimeBatch(sessionId,
                      nowMs,
                      filteredPoint,
                      beatMarkerPoint,
                      bpm,
                      lastBeatIntervalMs,
                      qualityScore,
                      beatIndex,
                      contactPresent);

  if (nowMs - startedAtMs >= 60000 && !windowReady) {
    readyWindow.sessionId = sessionId;
    readyWindow.measurementId = measurementId;
    readyWindow.sampleStartTsMs = startedAtMs;
    readyWindow.sampleEndTsMs = nowMs;
    readyWindow.heartRateBpm = bpm;
    readyWindow.qualityScore = qualityScore;
    readyWindow.processedPointCount = pointIndex;
    readyWindow.beatCount = beatIndex;
    readyWindow.rrIntervalCount = beatIndex;
    windowReady = true;
    completedEventPending = true;
  }
}

bool activeTestManagerConsumeWindow(ActivePpgWindow *window) {
  if (!windowReady || window == nullptr) {
    return false;
  }

  *window = readyWindow;
  windowReady = false;
  return true;
}

bool activeTestManagerConsumeCompletedEvent() {
  const bool hadEvent = completedEventPending;
  completedEventPending = false;
  return hadEvent;
}

ActivePpgRealtimeSnapshot activeTestManagerGetRealtimeSnapshot() {
  return realtimeSnapshot;
}

bool activeTestManagerConsumeRealtimeSnapshot(ActivePpgRealtimeSnapshot *snapshot) {
  if (!realtimeSnapshotReady || snapshot == nullptr) {
    return false;
  }

  *snapshot = realtimeSnapshot;
  realtimeSnapshotReady = false;
  return true;
}

bool activeTestManagerConsumeRealtimeBatch(ActivePpgRealtimeBatch *batch) {
  if (!realtimeBatchReady || batch == nullptr) {
    return false;
  }

  *batch = realtimeBatch;
  realtimeBatch = ActivePpgRealtimeBatch{};
  realtimeBatchReady = false;
  return true;
}

}  // namespace hold_integration