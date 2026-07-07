#include "data_packager.h"

#include "device_state_machine.h"

namespace hold_integration {

namespace {

void appendJsonStringField(String &payload, const char *key, const char *value,
                           bool appendComma = true) {
  payload += "\"" + String(key) + "\":\"" + String(value == nullptr ? "" : value) + "\"";
  if (appendComma) {
    payload += ",";
  }
}

void appendIntArrayField(String &payload, const char *key, const int16_t *values,
                         uint8_t count, bool appendComma = true) {
  payload += "\"" + String(key) + "\":[";
  for (uint8_t index = 0; index < count; ++index) {
    if (index > 0) {
      payload += ",";
    }
    payload += String(values[index]);
  }
  payload += "]";
  if (appendComma) {
    payload += ",";
  }
}

void appendUint16ArraySliceField(String &payload, const char *key, const uint16_t *values,
                                 size_t offset, size_t count, bool appendComma = true) {
  payload += "\"" + String(key) + "\":[";
  for (size_t index = 0; index < count; ++index) {
    if (index > 0) {
      payload += ",";
    }
    payload += String(values[offset + index]);
  }
  payload += "]";
  if (appendComma) {
    payload += ",";
  }
}

void appendUint32ArraySliceField(String &payload, const char *key, const uint32_t *values,
                                 size_t offset, size_t count, bool appendComma = true) {
  payload += "\"" + String(key) + "\":[";
  for (size_t index = 0; index < count; ++index) {
    if (index > 0) {
      payload += ",";
    }
    payload += String(values[offset + index]);
  }
  payload += "]";
  if (appendComma) {
    payload += ",";
  }
}

}  // namespace

String packDeviceStateJson(const DeviceStateSnapshot &snapshot) {
  String payload = "{";
  appendJsonStringField(payload, "msg_type", "device_state");
  payload += "\"session_id\":" + String(snapshot.sessionId) + ",";
  payload += "\"ts_ms\":" + String(snapshot.tsMs) + ",";
  appendJsonStringField(payload, "device_state", toString(snapshot.deviceState));
  appendJsonStringField(payload, "ble_state", toString(snapshot.bleLinkState));
  appendJsonStringField(payload, "led_mode", toString(snapshot.ledMode));
  appendJsonStringField(payload, "phase_type", toString(snapshot.phaseType));
  payload += "\"phase_remaining_ms\":" + String(snapshot.phaseRemainingMs) + ",";
  appendJsonStringField(payload, "status_text", snapshot.statusText);
  appendJsonStringField(payload, "guide_text", snapshot.guideText);
  payload += "\"error_code\":" + String(snapshot.errorCode);
  payload += "}";
  return payload;
}

String packCalibrationStatusJson(const CalibrationStatusSnapshot &snapshot) {
  String payload = "{";
  appendJsonStringField(payload, "msg_type", "calibration_status");
  payload += "\"session_id\":" + String(snapshot.sessionId) + ",";
  payload += "\"ts_ms\":" + String(snapshot.tsMs) + ",";
  payload += "\"calibration_step\":" + String(snapshot.calibrationStep) + ",";
  appendJsonStringField(payload, "phase_type", toString(snapshot.phaseType));
  payload += "\"phase_remaining_ms\":" + String(snapshot.phaseRemainingMs) + ",";
  payload += "\"resp_rate_bpm\":" + String(snapshot.respRateBpm) + ",";
  payload += "\"resp_carrier_value\":" + String(snapshot.respCarrierValue, 5) + ",";
  payload += "\"resp_detrended_value\":" + String(snapshot.respDetrendedValue, 5) + ",";
  payload += "\"resp_signal_value\":" + String(snapshot.respSignalValue, 4) + ",";
  payload += "\"resp_beat_marker_value\":" + String(snapshot.respBeatMarkerValue, 5) + ",";
  payload += "\"resp_slope_value\":" + String(snapshot.respSlopeValue, 5) + ",";
  payload += "\"resp_amplitude\":" + String(snapshot.respAmplitude, 4) + ",";
  payload += "\"motion_level\":" + String(snapshot.motionLevel, 4) + ",";
  appendJsonStringField(payload, "axis_name", snapshot.axisName);
  appendJsonStringField(payload, "reject_reason", snapshot.rejectReason);
  appendJsonStringField(payload, "status_text", snapshot.statusText);
  appendJsonStringField(payload, "guide_text", snapshot.guideText, false);
  payload += "}";
  return payload;
}

String packRespDebugJson(const CalibrationStatusSnapshot &snapshot) {
  String payload = "{";
  appendJsonStringField(payload, "msg_type", "resp_debug");
  payload += "\"session_id\":" + String(snapshot.sessionId) + ",";
  payload += "\"ts_ms\":" + String(snapshot.tsMs) + ",";
  payload += "\"resp_rate_bpm\":" + String(snapshot.respRateBpm) + ",";
  payload += "\"resp_carrier_value\":" + String(snapshot.respCarrierValue, 5) + ",";
  payload += "\"resp_detrended_value\":" + String(snapshot.respDetrendedValue, 5) + ",";
  payload += "\"resp_signal_value\":" + String(snapshot.respSignalValue, 4) + ",";
  payload += "\"resp_beat_marker_value\":" + String(snapshot.respBeatMarkerValue, 5) + ",";
  payload += "\"resp_slope_value\":" + String(snapshot.respSlopeValue, 5) + ",";
  payload += "\"resp_amplitude\":" + String(snapshot.respAmplitude, 4) + ",";
  payload += "\"motion_level\":" + String(snapshot.motionLevel, 4) + ",";
  appendJsonStringField(payload, "axis_name", snapshot.axisName);
  appendJsonStringField(payload, "reject_reason", snapshot.rejectReason);
  appendJsonStringField(payload, "status_text", snapshot.statusText);
  appendJsonStringField(payload, "guide_text", snapshot.guideText, false);
  payload += "}";
  return payload;
}

String packActiveRealtimeJson(const ActivePpgRealtimeSnapshot &snapshot) {
  String payload = "{";
  appendJsonStringField(payload, "msg_type", "active_realtime");
  payload += "\"session_id\":" + String(snapshot.sessionId) + ",";
  payload += "\"measurement_id\":" + String(snapshot.measurementId) + ",";
  payload += "\"ts_ms\":" + String(snapshot.tsMs) + ",";
  payload += "\"i6_filtered_point\":" + String(snapshot.filteredPoint, 5) + ",";
  payload += "\"i7_beat_marker\":" + String(snapshot.beatMarkerPoint, 5) + ",";
  payload += "\"heart_rate_bpm\":" + String(snapshot.heartRateBpm) + ",";
  payload += "\"i12\":" + String(snapshot.lastBeatIntervalMs) + ",";
  payload += "\"quality_score\":" + String(snapshot.qualityScore) + ",";
  payload += "\"beat_count\":" + String(snapshot.beatCount) + ",";
  payload += "\"contact_present\":" + String(snapshot.contactPresent ? "true" : "false") + ",";
  payload += "\"active\":" + String(snapshot.active ? "true" : "false");
  payload += "}";
  return payload;
}

String packActiveRealtimeBatchJson(const ActivePpgRealtimeBatch &batch) {
  String payload = "{";
  appendJsonStringField(payload, "msg_type", "active_realtime_batch");
  payload += "\"session_id\":" + String(batch.sessionId) + ",";
  payload += "\"measurement_id\":" + String(batch.measurementId) + ",";
  payload += "\"ts_ms_end\":" + String(batch.tsMsEnd) + ",";
  payload += "\"dt_ms\":" + String(batch.sampleIntervalMs) + ",";
  payload += "\"sample_count\":" + String(batch.sampleCount) + ",";
  appendIntArrayField(payload, "i6", batch.filteredPoints, batch.sampleCount);
  appendIntArrayField(payload, "i7", batch.beatMarkerPoints, batch.sampleCount);
  payload += "\"bpm\":" + String(batch.heartRateBpm) + ",";
  payload += "\"i12\":" + String(batch.lastBeatIntervalMs) + ",";
  payload += "\"qs\":" + String(batch.qualityScore) + ",";
  payload += "\"bc\":" + String(batch.beatCount) + ",";
  payload += "\"cp\":" + String(batch.contactPresent ? 1 : 0) + ",";
  payload += "\"active\":" + String(batch.active ? 1 : 0);
  payload += "}";
  return payload;
}

String packPassivePpgRealtimeBatchJson(const PassivePpgRealtimeBatch &batch) {
  String payload = "{";
  appendJsonStringField(payload, "msg_type", "passive_ppg_batch");
  payload += "\"session_id\":" + String(batch.sessionId) + ",";
  payload += "\"ts_ms_end\":" + String(batch.tsMsEnd) + ",";
  payload += "\"dt_ms\":" + String(batch.sampleIntervalMs) + ",";
  payload += "\"sample_count\":" + String(batch.sampleCount) + ",";
  appendIntArrayField(payload, "i6", batch.filteredPoints, batch.sampleCount);
  appendIntArrayField(payload, "i7", batch.beatMarkerPoints, batch.sampleCount);
  payload += "\"bpm\":" + String(batch.heartRateBpm) + ",";
  payload += "\"qs\":" + String(batch.qualityScore) + ",";
  payload += "\"cp\":" + String(batch.contactPresent ? 1 : 0) + ",";
  payload += "\"active\":" + String(batch.active ? 1 : 0);
  payload += "}";
  return payload;
}

String packPassiveRespWindowJson(const PassiveRespWindow &window,
                                 uint16_t fragmentIndex,
                                 uint16_t fragmentTotal) {
  String payload = "{";
  appendJsonStringField(payload, "msg_type", "passive_resp_window");
  payload += "\"session_id\":" + String(window.sessionId) + ",";
  payload += "\"window_id\":" + String(window.windowId) + ",";
  payload += "\"window_start_ts_ms\":" + String(window.windowStartTsMs) + ",";
  payload += "\"window_end_ts_ms\":" + String(window.windowEndTsMs) + ",";
  payload += "\"resp_rate_bpm\":" + String(window.respRateBpm) + ",";
  payload += "\"quality_score\":" + String(window.qualityScore) + ",";
  payload += "\"motion_level\":" + String(window.motionLevel, 4) + ",";
  payload += "\"point_count\":" + String(window.pointCount) + ",";
  payload += "\"fragment_index\":" + String(fragmentIndex) + ",";
  payload += "\"fragment_total\":" + String(fragmentTotal);
  payload += "}";
  return payload;
}

String packActiveWindowJson(const ActivePpgWindow &window,
                            uint16_t fragmentIndex,
                            uint16_t fragmentTotal,
                            size_t processedPointOffset,
                            size_t processedPointCount,
                            size_t beatOffset,
                            size_t beatCount) {
  String payload = "{";
  appendJsonStringField(payload, "msg_type", "active_window");
  payload += "\"session_id\":" + String(window.sessionId) + ",";
  payload += "\"measurement_id\":" + String(window.measurementId) + ",";
  payload += "\"sample_start_ts_ms\":" + String(window.sampleStartTsMs) + ",";
  payload += "\"sample_end_ts_ms\":" + String(window.sampleEndTsMs) + ",";
  payload += "\"heart_rate_bpm\":" + String(window.heartRateBpm) + ",";
  payload += "\"quality_score\":" + String(window.qualityScore) + ",";
  payload += "\"processed_point_count\":" + String(window.processedPointCount) + ",";
  payload += "\"beat_count\":" + String(window.beatCount) + ",";
  payload += "\"rr_interval_count\":" + String(window.rrIntervalCount) + ",";
  payload += "\"fragment_index\":" + String(fragmentIndex) + ",";
  payload += "\"fragment_total\":" + String(fragmentTotal) + ",";
  payload += "\"processed_point_offset\":" + String(static_cast<uint32_t>(processedPointOffset)) + ",";
  payload += "\"processed_point_fragment_count\":" + String(static_cast<uint32_t>(processedPointCount)) + ",";
  appendUint16ArraySliceField(payload, "processed_points_fragment",
                              window.processedPoints,
                              processedPointOffset,
                              processedPointCount);
  payload += "\"beat_offset\":" + String(static_cast<uint32_t>(beatOffset)) + ",";
  payload += "\"beat_fragment_count\":" + String(static_cast<uint32_t>(beatCount)) + ",";
  appendUint32ArraySliceField(payload, "beat_ts_ms_fragment",
                              window.beatTsMs,
                              beatOffset,
                              beatCount,
                              true);
  appendUint16ArraySliceField(payload, "rr_intervals_ms_fragment",
                              window.rrIntervalsMs,
                              0,
                              window.rrIntervalCount,
                              false);
  payload += "}";
  return payload;
}

String packErrorStatusJson(const ErrorStatusSnapshot &snapshot) {
  String payload = "{";
  appendJsonStringField(payload, "msg_type", "error_status");
  payload += "\"session_id\":" + String(snapshot.sessionId) + ",";
  payload += "\"ts_ms\":" + String(snapshot.tsMs) + ",";
  payload += "\"error_code\":" + String(snapshot.errorCode) + ",";
  payload += "\"recoverable\":" + String(snapshot.recoverable ? "true" : "false") + ",";
  appendJsonStringField(payload, "error_message", snapshot.errorMessage, false);
  payload += "}";
  return payload;
}

}  // namespace hold_integration