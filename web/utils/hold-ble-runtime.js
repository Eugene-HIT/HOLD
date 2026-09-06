const bleDebugProtocol = require('./ble-debug-protocol');

const MAX_WAVE_POINTS = 240;
const MAX_DEBUG_LOGS = 40;
const MAX_ACTIVE_MEASUREMENTS = 30;
const MAX_DAILY_ANALYSES = 21;
const MAX_RESP_REPORT_POINTS = 240;
const MAX_PPG_REPORT_POINTS = 6000;
const STORAGE_KEY = 'hold_ble_runtime_state_v2';
const MAX_ACTIVE_PERSIST_DAYS = 7;
const MAX_DAILY_PERSIST_DAYS = 14;
const AUTO_RECONNECT_DELAY_MS = 1200;

const runtime = {
  initialized: false,
  listeners: [],
  connecting: false,
  manualDisconnectRequested: false,
  autoReconnectTimer: null,
  reconnectAttemptsRemaining: 0,
  pendingActiveWindows: {},
  pendingActiveRealtimeMeasurements: {},
  state: buildInitialState()
};

function buildInitialState() {
  return {
    adapterStatus: '未初始化',
    connectionStatus: '未连接',
    isConnected: false,
    scanning: false,
    deviceName: '',
    deviceId: '',
    serviceId: '',
    notifyCharacteristicId: '',
    writeCharacteristicId: '',
    lastEventTime: '',
    lastPacketType: '',
    lastEventRaw: '',
    currentDeviceState: '',
    currentGuideText: '',
    currentPhaseText: '',
    currentRespBpm: '',
    currentHeartBpm: '',
    currentActiveHeartBpm: '',
    currentMotionLevel: '',
    currentSignalQuality: 0,
    currentBeatCount: 0,
    currentActiveBeatCount: 0,
    currentAxisName: '',
    currentCalibrationStep: 0,
    phaseRemainingMs: 0,
    respWaveSummary: '',
    heartWaveSummary: '',
    respWavePoints: [],
    respBeatMarkerPoints: [],
    heartWavePoints: [],
    heartBeatMarkerPoints: [],
    chestPpgWavePoints: [],
    chestPpgBeatMarkerPoints: [],
    debugLogs: [],
    activeMeasurements: [],
    dailyAnalyses: [],
    latestPassiveWindow: null,
    latestActiveWindow: null,
    overallSummary: buildEmptyOverallSummary(),
    insightStatus: 'idle'
  };
}

function stringToArrayBuffer(text) {
  const source = `${text || ''}`;
  const buffer = new ArrayBuffer(source.length);
  const bytes = new Uint8Array(buffer);
  for (let index = 0; index < source.length; index += 1) {
    bytes[index] = source.charCodeAt(index);
  }
  return buffer;
}

function buildEmptyOverallSummary() {
  return {
    title: '整体分析',
    summary: '暂无可分析的真实数据。',
    advice: '连接设备并积累一段时间数据后，这里会生成简要分析和建议。',
    updatedAt: '',
    sections: [
      { key: 'resp', title: '呼吸报告', body: '暂无呼吸窗口数据。' },
      { key: 'heart', title: '当天心率报告', body: '暂无心率趋势数据。' },
      { key: 'active', title: '指部 PPG 报告', body: '暂无主动检测记录。' },
      { key: 'overall', title: '总结板块', body: '暂无整体结论。' }
    ]
  };
}

function cloneState() {
  return JSON.parse(JSON.stringify(runtime.state));
}

function emitState() {
  const snapshot = cloneState();
  runtime.listeners.forEach((listener) => {
    try {
      listener(snapshot);
    } catch (error) {
      console.error('BLE runtime listener error', error);
    }
  });
}

function persistState() {
  const persisted = {
    activeMeasurements: runtime.state.activeMeasurements,
    dailyAnalyses: runtime.state.dailyAnalyses,
    latestPassiveWindow: runtime.state.latestPassiveWindow,
    latestActiveWindow: runtime.state.latestActiveWindow,
    overallSummary: runtime.state.overallSummary,
    respWavePoints: runtime.state.respWavePoints,
    respBeatMarkerPoints: runtime.state.respBeatMarkerPoints,
    chestPpgWavePoints: runtime.state.chestPpgWavePoints,
    chestPpgBeatMarkerPoints: runtime.state.chestPpgBeatMarkerPoints
  };

  try {
    wx.setStorageSync(STORAGE_KEY, persisted);
  } catch (error) {
    console.error('persist state failed', error);
  }
}

function hydrateStateFromStorage() {
  try {
    const persisted = wx.getStorageSync(STORAGE_KEY);
    if (!persisted || typeof persisted !== 'object') {
      return;
    }

    runtime.state.activeMeasurements = Array.isArray(persisted.activeMeasurements)
      ? persisted.activeMeasurements.slice(0, MAX_ACTIVE_MEASUREMENTS)
      : [];
    runtime.state.dailyAnalyses = Array.isArray(persisted.dailyAnalyses)
      ? persisted.dailyAnalyses.slice(0, MAX_DAILY_ANALYSES)
      : [];
    runtime.state.latestPassiveWindow = persisted.latestPassiveWindow || null;
    runtime.state.latestActiveWindow = persisted.latestActiveWindow || null;
    runtime.state.overallSummary = persisted.overallSummary || buildEmptyOverallSummary();
    runtime.state.respWavePoints = Array.isArray(persisted.respWavePoints) ? persisted.respWavePoints : [];
    runtime.state.respBeatMarkerPoints = Array.isArray(persisted.respBeatMarkerPoints) ? persisted.respBeatMarkerPoints : [];
    runtime.state.chestPpgWavePoints = Array.isArray(persisted.chestPpgWavePoints) ? persisted.chestPpgWavePoints : [];
    runtime.state.chestPpgBeatMarkerPoints = Array.isArray(persisted.chestPpgBeatMarkerPoints) ? persisted.chestPpgBeatMarkerPoints : [];
  } catch (error) {
    console.error('hydrate state failed', error);
  }
}

function appendWavePoint(key, value) {
  const points = runtime.state[key].slice();
  points.push(Number(value || 0));
  if (points.length > MAX_WAVE_POINTS) {
    points.shift();
  }
  runtime.state[key] = points;
}

function appendWavePoints(key, values) {
  const points = runtime.state[key].slice();
  (values || []).forEach((value) => {
    points.push(Number(value || 0));
  });
  while (points.length > MAX_WAVE_POINTS) {
    points.shift();
  }
  runtime.state[key] = points;
}

function appendWavePointsWithCap(key, values, cap) {
  const points = runtime.state[key].slice();
  (values || []).forEach((value) => {
    points.push(Number(value || 0));
  });
  while (points.length > cap) {
    points.shift();
  }
  runtime.state[key] = points;
}

function trimArrayToCap(key, cap) {
  const points = runtime.state[key].slice();
  while (points.length > cap) {
    points.shift();
  }
  runtime.state[key] = points;
}

function sampleSeriesForPrompt(series, maxPoints, preservePeaks) {
  const source = Array.isArray(series) ? series : [];
  if (source.length <= maxPoints) {
    return source.slice();
  }

  const result = [];
  for (let index = 0; index < maxPoints; index += 1) {
    const start = Math.floor((index * source.length) / maxPoints);
    const end = Math.floor(((index + 1) * source.length) / maxPoints);
    const bucket = source.slice(start, Math.max(start + 1, end));
    if (!bucket.length) {
      continue;
    }

    if (preservePeaks) {
      let picked = bucket[0];
      bucket.forEach((value) => {
        if (Math.abs(value) > Math.abs(picked)) {
          picked = value;
        }
      });
      result.push(picked);
    } else {
      const sum = bucket.reduce((acc, value) => acc + Number(value || 0), 0);
      result.push(sum / bucket.length);
    }
  }
  return result;
}

function hasValue(value) {
  return value !== null && value !== undefined && value !== '';
}

function resolveActiveMeasurementId(source, fallbackSuffix = '') {
  if (source && hasValue(source.session_id) && hasValue(source.measurement_id)) {
    return `session-${source.session_id}-measurement-${source.measurement_id}`;
  }

  if (source && hasValue(source.measurement_id)) {
    return `${source.measurement_id}`;
  }

  if (source && (hasValue(source.sample_start_ts_ms) || hasValue(source.sample_end_ts_ms))) {
    return `window-${source.sample_start_ts_ms || 0}-${source.sample_end_ts_ms || 0}${fallbackSuffix ? `-${fallbackSuffix}` : ''}`;
  }

  return fallbackSuffix ? `active-${fallbackSuffix}` : '';
}

function decodeProcessedPointSeries(points) {
  return (Array.isArray(points) ? points : []).map((value) => Number(value || 0) - 32768);
}

function buildBeatMarkerSeriesFromTimestamps(wavePoints, beatTsMs, sampleStartTsMs, sampleEndTsMs) {
  const series = new Array(Array.isArray(wavePoints) ? wavePoints.length : 0).fill(0);
  if (!series.length) {
    return series;
  }

  const start = Number(sampleStartTsMs || 0);
  const end = Number(sampleEndTsMs || 0);
  const duration = end > start ? (end - start) : 0;
  (Array.isArray(beatTsMs) ? beatTsMs : []).forEach((timestamp) => {
    let index = 0;
    if (duration > 0) {
      index = Math.round(((Number(timestamp || 0) - start) / duration) * (series.length - 1));
    }
    if (index < 0) {
      index = 0;
    }
    if (index >= series.length) {
      index = series.length - 1;
    }
    series[index] = wavePoints[index] || 1;
  });
  return series;
}

function buildBeatMarkerSeriesFromTimelineMs(wavePoints, beatTimelineMs, durationMs) {
  const series = new Array(Array.isArray(wavePoints) ? wavePoints.length : 0).fill(0);
  if (!series.length) {
    return series;
  }

  const safeDurationMs = Math.max(0, Number(durationMs || 0));
  (Array.isArray(beatTimelineMs) ? beatTimelineMs : []).forEach((offsetMs) => {
    let index = 0;
    if (safeDurationMs > 0) {
      index = Math.round((Number(offsetMs || 0) / safeDurationMs) * (series.length - 1));
    }
    if (index < 0) {
      index = 0;
    }
    if (index >= series.length) {
      index = series.length - 1;
    }
    series[index] = wavePoints[index] || 1;
  });
  return series;
}

function buildDisplaySeriesPair(wavePoints, beatMarkerPoints, targetCount) {
  const safeWavePoints = Array.isArray(wavePoints) ? wavePoints : [];
  const safeBeatMarkerPoints = Array.isArray(beatMarkerPoints) ? beatMarkerPoints : [];
  const maxLength = Math.max(safeWavePoints.length, safeBeatMarkerPoints.length);
  if (maxLength <= targetCount) {
    return {
      wavePoints: safeWavePoints.slice(),
      beatMarkerPoints: safeBeatMarkerPoints.slice()
    };
  }

  const startIndex = maxLength - targetCount;
  return {
    wavePoints: safeWavePoints.slice(Math.min(startIndex, safeWavePoints.length)),
    beatMarkerPoints: safeBeatMarkerPoints.slice(Math.min(startIndex, safeBeatMarkerPoints.length))
  };
}

function buildBeatTimelineMsFromMarkers(beatMarkerPoints, durationMs) {
  const points = Array.isArray(beatMarkerPoints) ? beatMarkerPoints : [];
  if (!points.length) {
    return [];
  }

  const timeline = [];
  let previousMarked = false;
  const safeDurationMs = Math.max(0, Number(durationMs || 0));
  points.forEach((value, index) => {
    const marked = Number(value || 0) !== 0;
    if (!marked) {
      previousMarked = false;
      return;
    }

    if (previousMarked) {
      return;
    }

    previousMarked = true;
    const offsetMs = points.length > 1
      ? Math.round((index / (points.length - 1)) * safeDurationMs)
      : 0;
    timeline.push(offsetMs);
  });

  return timeline;
}

function buildBeatTimelineMs(beatTsMs, sampleStartTsMs, beatMarkerPoints, durationMs) {
  const directBeatTs = Array.isArray(beatTsMs)
    ? beatTsMs.filter((value) => value !== null && value !== undefined).map((value) => Number(value || 0))
    : [];
  if (directBeatTs.length) {
    const startTsMs = Number(sampleStartTsMs || 0);
    return directBeatTs.map((value) => Math.max(0, value - startTsMs));
  }

  return buildBeatTimelineMsFromMarkers(beatMarkerPoints, durationMs);
}

function buildBeatTimelineMsFromIntervals(rrIntervalsMs) {
  const source = Array.isArray(rrIntervalsMs) ? rrIntervalsMs : [];
  if (!source.length) {
    return [];
  }

  let accumulated = 0;
  return source.map((intervalMs) => {
    accumulated += Math.max(0, Number(intervalMs || 0));
    return accumulated;
  });
}

function buildRrIntervalsMs(beatTimelineMs) {
  const source = Array.isArray(beatTimelineMs) ? beatTimelineMs : [];
  if (source.length < 2) {
    return [];
  }

  const rrIntervals = [];
  for (let index = 1; index < source.length; index += 1) {
    rrIntervals.push(Math.max(0, Number(source[index] || 0) - Number(source[index - 1] || 0)));
  }
  return rrIntervals;
}

function stripFullActiveWave(item) {
  if (!item || typeof item !== 'object') {
    return item;
  }

  return {
    ...item,
    fullPpgWavePoints: [],
    fullPpgBeatMarkerPoints: []
  };
}

function buildActiveMeasurementPrompt(measurement) {
  const beatTimelineMs = Array.isArray(measurement.beatTimelineMs)
    ? measurement.beatTimelineMs
    : [];
  const rrIntervalsMs = Array.isArray(measurement.rrIntervalsMs)
    ? measurement.rrIntervalsMs
    : buildRrIntervalsMs(beatTimelineMs);
  const effectiveBeatCount = rrIntervalsMs.length > 0 ? rrIntervalsMs.length + 1 : Number(measurement.fullBeatCount || 0);

  return [
    '你是指部 PPG 单次检测报告助手。',
    '请只根据当前有效RR片段分析这次检测更偏平稳还是更偏紧张。',
    '要求：',
    '1. 不使用医学诊断口吻。',
    '2. 只输出4句短句，每句单独一行，总长度控制在120字以内。',
    '3. 必须依次输出：结论、节律、心率、焦虑倾向。',
    '4. 不要出现无法判断、数据质量、置信度、干扰因素、复测建议这些说法。',
    `检测记录: ${JSON.stringify({
      id: measurement.id,
      startedAt: measurement.startedAt,
      durationLabel: measurement.durationLabel,
      resultTag: measurement.resultTag,
      metrics: measurement.metrics,
      fullBeatCount: measurement.fullBeatCount || 0,
      effectiveBeatCount,
      realtimeDurationMs: measurement.realtimeDurationMs || 0,
      archiveMode: measurement.archiveMode || ''
    })}`,
    `1分钟总beat数: ${measurement.fullBeatCount || 0}`,
    `有效片段beat数: ${effectiveBeatCount}`,
    `beat时间点(相对开始毫秒): ${JSON.stringify(beatTimelineMs)}`,
    `RR间期毫秒序列: ${JSON.stringify(rrIntervalsMs)}`
  ].join('\n');
}

function buildLocalActiveMeasurementFallbackText(measurement, failureReason) {
  const metricHeartRate = measurement && Array.isArray(measurement.metrics) && measurement.metrics[0]
    ? measurement.metrics[0].value
    : '--';
  const metricBeatCount = measurement && Array.isArray(measurement.metrics) && measurement.metrics[1]
    ? measurement.metrics[1].value
    : '--';
  const pointCount = measurement && Number(measurement.fullProcessedPointCount || measurement.processedPointCount || 0);
  const archiveMode = measurement && measurement.archiveMode ? measurement.archiveMode : 'unknown';

  return [
    '结论：本次更偏向轻度到中等紧张解读。',
    `节律：当前记录显示心率约 ${metricHeartRate} bpm，beat 数 ${metricBeatCount}。`,
    '心率：若有效片段起伏不大，可按基本平稳理解；若节律跳动明显，则按偏紧张理解。',
    `焦虑倾向：当前展示为本地短结论兜底，来源 ${archiveMode}，云端失败原因 ${failureReason || 'unknown'}。`
  ].join('\n');
}

function clearAutoReconnectTimer() {
  if (runtime.autoReconnectTimer) {
    clearTimeout(runtime.autoReconnectTimer);
    runtime.autoReconnectTimer = null;
  }
}

function pushDebugLog(message) {
  if (!message) {
    return;
  }

  const logs = runtime.state.debugLogs.slice();
  logs.unshift(`${new Date().toLocaleTimeString()}  ${message}`);
  runtime.state.debugLogs = logs.slice(0, MAX_DEBUG_LOGS);
}

function formatDateTime(timestampMs) {
  if (!timestampMs) {
    return '';
  }

  const date = new Date(Number(timestampMs));
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, '0');
  const day = `${date.getDate()}`.padStart(2, '0');
  const hours = `${date.getHours()}`.padStart(2, '0');
  const minutes = `${date.getMinutes()}`.padStart(2, '0');
  return `${year}-${month}-${day} ${hours}:${minutes}`;
}

function formatDateOnly(timestampMs) {
  return formatDateTime(timestampMs).slice(0, 10);
}

function formatDuration(durationMs) {
  if (!durationMs) {
    return '';
  }

  const seconds = Math.max(0, Math.round(durationMs / 1000));
  return `${seconds} 秒`;
}

function computeResultTag(avgHeartRate, beatCount) {
  if (Number(avgHeartRate || 0) > 0 && Number(beatCount || 0) > 0) {
    return '检测完成';
  }
  return '建议复测';
}

function getOrCreatePendingActiveRealtimeMeasurement(measurementId) {
  const key = hasValue(measurementId) ? `${measurementId}` : '0';
  if (!runtime.pendingActiveRealtimeMeasurements[key]) {
    runtime.pendingActiveRealtimeMeasurements[key] = {
      measurementId: key,
      wavePoints: [],
      beatMarkerPoints: [],
      beatCount: 0,
      heartRateBpm: 0,
      lastBeatIntervalMs: 0,
      sampleIntervalMs: 0,
      tsMsEnd: 0,
      startedAtTsMs: 0
    };
  }

  return runtime.pendingActiveRealtimeMeasurements[key];
}

function consumePendingActiveRealtimeMeasurement(measurementId) {
  const key = hasValue(measurementId) ? `${measurementId}` : '0';
  const snapshot = runtime.pendingActiveRealtimeMeasurements[key] || null;
  delete runtime.pendingActiveRealtimeMeasurements[key];
  return snapshot;
}

function buildActiveMeasurementRecord(payload, existingItem, options = {}) {
  const id = resolveActiveMeasurementId(payload, `${Date.now()}`);
  const avgHeartRate = Number(payload.heart_rate_bpm || 0);
  const beatCount = Number(payload.beat_count || 0);
  const isPartial = Boolean(options.isPartial);
  const receivedFragmentCount = Number(options.receivedFragmentCount || 0);
  const fragmentTotal = Number(options.fragmentTotal || 0);
  const providedFullWavePoints = Array.isArray(options.fullWavePoints) ? options.fullWavePoints : null;
  const providedFullBeatMarkerPoints = Array.isArray(options.fullBeatMarkerPoints) ? options.fullBeatMarkerPoints : null;
  const realtimeHeartRateBpm = Number(options.realtimeHeartRateBpm || 0);
  const realtimeBeatCount = Number(options.realtimeBeatCount || 0);
  const realtimeSampleIntervalMs = Number(options.realtimeSampleIntervalMs || 0);
  const realtimeDurationMs = Number(options.realtimeDurationMs || 0);
  const realtimePointTarget = Number(options.realtimePointTarget || 0);
  const processedPoints = Array.isArray(payload.processed_points)
    ? payload.processed_points.filter((value) => value !== null && value !== undefined)
    : [];
  const beatTsMs = Array.isArray(payload.beat_ts_ms)
    ? payload.beat_ts_ms.filter((value) => value !== null && value !== undefined)
    : [];
  const directRrIntervalsMs = Array.isArray(payload.rr_intervals_ms)
    ? payload.rr_intervals_ms.filter((value) => value !== null && value !== undefined).map((value) => Number(value || 0))
    : [];
  const hasProvidedWave = Array.isArray(providedFullWavePoints) && providedFullWavePoints.length > 0;
  const hasCompleteWave = processedPoints.length > 0;
  const fullWavePoints = hasProvidedWave
    ? providedFullWavePoints.slice()
    : (hasCompleteWave
    ? decodeProcessedPointSeries(processedPoints)
    : (runtime.state.heartWavePoints || []));
  const expectedPointCount = Number(payload.processed_point_count || 0);
  const expectedDurationMs = Math.max(0, Number(payload.sample_end_ts_ms || 0) - Number(payload.sample_start_ts_ms || 0));
  const effectiveHeartRate = realtimeHeartRateBpm > 0 ? realtimeHeartRateBpm : avgHeartRate;
  const effectiveBeatCount = realtimeBeatCount > 0 ? realtimeBeatCount : beatCount;
  const effectiveRealtimeDurationMs = realtimeDurationMs > 0
    ? realtimeDurationMs
    : (realtimeSampleIntervalMs > 0 ? realtimeSampleIntervalMs * fullWavePoints.length : 0);
  const expectedRealtimePoints = realtimePointTarget > 0
    ? realtimePointTarget
    : (realtimeSampleIntervalMs > 0 ? Math.round(60000 / realtimeSampleIntervalMs) : 0);
  const realtimeComplete = Boolean(options.realtimeComplete)
    || (fullWavePoints.length > 0 && (
      (expectedRealtimePoints > 0 && fullWavePoints.length >= Math.max(1200, Math.floor(expectedRealtimePoints * 0.9)))
      || (expectedPointCount > 0 && fullWavePoints.length >= Math.max(1200, Math.floor(expectedPointCount * 0.9)))
      || effectiveRealtimeDurationMs >= 55000
      || (expectedDurationMs >= 55000 && fullWavePoints.length >= 1200)
    ));
  const archiveReady = realtimeComplete || (!isPartial && fragmentTotal > 0 && receivedFragmentCount >= fragmentTotal);
  const effectivePartial = isPartial && !realtimeComplete;
  const beatTimelineMs = beatTsMs.length > 0
    ? buildBeatTimelineMs(
      beatTsMs,
      payload.sample_start_ts_ms,
      Array.isArray(providedFullBeatMarkerPoints) ? providedFullBeatMarkerPoints : [],
      effectiveRealtimeDurationMs > 0 ? effectiveRealtimeDurationMs : expectedDurationMs)
    : buildBeatTimelineMsFromIntervals(directRrIntervalsMs);
  const rrIntervalsMs = directRrIntervalsMs.length > 0 ? directRrIntervalsMs : buildRrIntervalsMs(beatTimelineMs);
  const preferredBeatMarkerPoints = Array.isArray(providedFullBeatMarkerPoints) && providedFullBeatMarkerPoints.length > 0
    ? providedFullBeatMarkerPoints.slice()
    : (beatTimelineMs.length > 0
      ? buildBeatMarkerSeriesFromTimelineMs(
        fullWavePoints,
        beatTimelineMs,
        effectiveRealtimeDurationMs > 0 ? effectiveRealtimeDurationMs : expectedDurationMs)
      : (hasCompleteWave
        ? buildBeatMarkerSeriesFromTimestamps(
          fullWavePoints,
          beatTsMs,
          payload.sample_start_ts_ms,
          payload.sample_end_ts_ms)
        : (runtime.state.heartBeatMarkerPoints || [])));
  const displaySeries = buildDisplaySeriesPair(fullWavePoints, preferredBeatMarkerPoints, 240);
  const previous = existingItem || {};

  return {
    id,
    title: '指部主动检测报告',
    startedAt: formatDateTime(payload.sample_start_ts_ms),
    durationLabel: formatDuration(Number(payload.sample_end_ts_ms || 0) - Number(payload.sample_start_ts_ms || 0)),
    resultTag: effectivePartial ? '接收中' : computeResultTag(effectiveHeartRate, effectiveBeatCount),
    metrics: [
      { label: '平均心率', value: `${effectiveHeartRate}`, unit: ' bpm' },
      { label: 'beat 数', value: `${effectiveBeatCount}`, unit: '' }
    ],
    processedPointCount: Number(payload.processed_point_count || 0),
    sampleStartTsMs: Number(payload.sample_start_ts_ms || 0),
    sampleEndTsMs: Number(payload.sample_end_ts_ms || 0),
    fullProcessedPointCount: fullWavePoints.length,
    fullBeatCount: effectiveBeatCount || rrIntervalsMs.length || beatTimelineMs.length || preferredBeatMarkerPoints.filter((value) => Number(value || 0) !== 0).length,
    fullPpgWavePoints: fullWavePoints,
    fullPpgBeatMarkerPoints: preferredBeatMarkerPoints,
    ppgWavePoints: displaySeries.wavePoints,
    ppgBeatMarkerPoints: displaySeries.beatMarkerPoints,
    beatTimelineMs,
    rrIntervalsMs,
    realtimePointCount: fullWavePoints.length,
    realtimeDurationMs: effectiveRealtimeDurationMs,
    realtimeHeartRateBpm: realtimeHeartRateBpm || effectiveHeartRate,
    realtimeBeatCount: realtimeBeatCount || effectiveBeatCount,
    archiveReady,
    archiveMode: realtimeComplete
      ? 'realtime-primary'
      : (effectivePartial ? 'fragment-pending' : 'fragment-complete'),
    generatedReportText: previous.generatedReportText || '',
    generatedReportSource: previous.generatedReportSource || '',
    generatedReportError: previous.generatedReportError || '',
    generatedReportUpdatedAt: previous.generatedReportUpdatedAt || '',
    summary: effectivePartial
      ? `测量 ${payload.measurement_id || 0} 仍在接收窗口元数据，当前分片 ${receivedFragmentCount}/${fragmentTotal}，但已累计实时波形 ${fullWavePoints.length}/${expectedRealtimePoints || expectedPointCount || '--'} 点，当前页面先以实时累计结果为准。`
      : (realtimeComplete && fragmentTotal > 0 && receivedFragmentCount < fragmentTotal
        ? `测量 ${payload.measurement_id || 0} 已累计完整 60 秒实时波形 ${fullWavePoints.length} 点，窗口分片目前为 ${receivedFragmentCount}/${fragmentTotal}，本条记录已按实时累计结果归档。`
        : `测量 ${payload.measurement_id || 0}，处理点数 ${payload.processed_point_count || 0}，实时累计 ${fullWavePoints.length} 点，识别 beat ${effectiveBeatCount}。`),
    briefAnalysis: effectivePartial
      ? '这次 60 秒主动检测的分片归档还没收全，但实时批数据已经在累计。只要实时累计达到整分钟，报告会优先使用实时累计结果，不再被分片卡死。'
      : (effectiveHeartRate > 0
        ? '本次主动检测已形成可读的心率与波形记录，页面展示和模型报告都会优先使用同一份实时累计结果。'
        : '本次主动检测没有形成稳定的心率结果，建议重新测一次并保持贴合稳定。'),
    briefAdvice: effectivePartial
      ? '如果后续分片继续到达，这条记录会自动补齐窗口元数据，但报告生成不再依赖所有分片都传完。'
      : (effectiveHeartRate > 0 ? `当前记录心率约 ${effectiveHeartRate} bpm，请结合后续多次记录一起看趋势。` : '本次未形成稳定心率，请优先检查接触与姿态。'),
    reportSections: previous.reportSections || [
      { heading: '指部 PPG 报告', body: `平均心率 ${effectiveHeartRate || '--'} bpm，识别 beat ${effectiveBeatCount || 0}，实时累计 ${fullWavePoints.length} 点。` },
      { heading: '简要分析', body: effectivePartial ? '当前窗口分片未收全，但已经开始使用实时累计波形作为主要依据。' : (effectiveHeartRate > 0 ? '这次记录已经提取到可参考的节律信息，并且显示与报告统一使用同一份缓存。' : '这次记录没有形成足够稳定的节律结果。') },
      { heading: '建议', body: effectiveHeartRate > 0 ? '建议继续保留同样贴合方式做复测，并与被动监测趋势一起看。' : '建议调整手指遮光与压力后再次检测。' }
    ],
    isPartial: effectivePartial,
    receivedFragmentCount,
    fragmentTotal,
    raw: payload
  };
}

function trimOldRecords() {
  const now = Date.now();
  const activeCutoff = now - MAX_ACTIVE_PERSIST_DAYS * 24 * 60 * 60 * 1000;
  const dailyCutoff = now - MAX_DAILY_PERSIST_DAYS * 24 * 60 * 60 * 1000;

  runtime.state.activeMeasurements = (runtime.state.activeMeasurements || []).filter((item) => {
    const ts = Number(item.sampleEndTsMs || item.raw?.sample_end_ts_ms || 0);
    return !ts || ts >= activeCutoff;
  }).slice(0, MAX_ACTIVE_MEASUREMENTS);

  runtime.state.dailyAnalyses = (runtime.state.dailyAnalyses || []).filter((item) => {
    const ts = Number(item.windowEndTsMs || item.latestWindowEndTsMs || 0);
    return !ts || ts >= dailyCutoff;
  }).slice(0, MAX_DAILY_ANALYSES);
}

function buildFallbackInsight() {
  const latestDaily = runtime.state.dailyAnalyses[0] || null;
  const latestActive = runtime.state.activeMeasurements[0] || null;
  const overall = buildEmptyOverallSummary();

  if (latestDaily) {
    overall.sections[0].body = `最近呼吸摘要：平均呼吸 ${latestDaily.respirationAvg || '--'} 次/分，已累计窗口 ${latestDaily.windowCount || 0} 个。`;
    overall.sections[1].body = `最近日级心率摘要：平均心率 ${latestDaily.heartRateAvg || '--'} bpm，最近窗口 ${latestDaily.latestWindowId || 0}。`;
  }

  if (latestActive) {
    overall.sections[2].body = `${latestActive.startedAt || ''} 的主动检测结果为 ${latestActive.resultTag || '待复核'}，平均心率 ${latestActive.metrics?.[0]?.value || '--'} bpm。`;
  }

  overall.sections[3].body = [overall.sections[0].body, overall.sections[1].body, overall.sections[2].body]
    .filter(Boolean)
    .join(' ');
  overall.summary = overall.sections[3].body || overall.summary;
  overall.advice = '当前数据量仍有限，建议继续积累更多真实记录后再做趋势判断。';
  overall.updatedAt = formatDateTime(Date.now());
  return overall;
}

function normalizeInsightJson(json, fallback) {
  const modelSections = Array.isArray(json.sections) ? json.sections : [];
  const mergedSections = fallback.sections.map((fallbackSection) => {
    const found = modelSections.filter((item) => item && item.key === fallbackSection.key)[0];
    if (found && found.body) {
      return {
        key: fallbackSection.key,
        title: found.title || fallbackSection.title,
        body: found.body
      };
    }
    return fallbackSection;
  });

  return {
    title: json.title || fallback.title,
    summary: json.summary || fallback.summary,
    advice: json.advice || fallback.advice,
    updatedAt: formatDateTime(Date.now()),
    sections: mergedSections
  };
}

function extractInsightJsonText(replyText) {
  let text = `${replyText}`.trim();

  const fenceMatch = text.match(/```(?:json)?\s*([\s\S]*?)```/i);
  if (fenceMatch && fenceMatch[1]) {
    text = fenceMatch[1].trim();
  }

  if (text.startsWith('{') && text.endsWith('}')) {
    return text;
  }

  const start = text.indexOf('{');
  const end = text.lastIndexOf('}');
  if (start >= 0 && end > start) {
    return text.slice(start, end + 1);
  }

  return text;
}

function parseInsightReply(replyText) {
  const fallback = buildFallbackInsight();
  if (!replyText) {
    return fallback;
  }

  try {
    const json = JSON.parse(extractInsightJsonText(replyText));
    return normalizeInsightJson(json, fallback);
  } catch (error) {
    fallback.summary = `${replyText}`.trim();
    fallback.updatedAt = formatDateTime(Date.now());
    return fallback;
  }
}

function buildFallbackDailyAnalysis() {
  const latestWindow = runtime.state.latestPassiveWindow;
  const hasRespWave = (runtime.state.respWavePoints || []).length > 0;
  const hasChestWave = (runtime.state.chestPpgWavePoints || []).length > 0;
  if (!latestWindow && !hasRespWave && !hasChestWave) {
    return null;
  }

  const timestampMs = latestWindow && latestWindow.window_end_ts_ms
    ? Number(latestWindow.window_end_ts_ms)
    : Date.now();
  return {
    dayKey: formatDateOnly(timestampMs),
    day: formatDateOnly(timestampMs),
    title: '最近 1 分钟缓存',
    respirationAvg: Number(runtime.state.currentRespBpm || (latestWindow && latestWindow.resp_rate_bpm) || 0),
    heartRateAvg: Number(runtime.state.currentHeartBpm || 0),
    stabilityScore: Number((latestWindow && latestWindow.quality_score) || runtime.state.currentSignalQuality || 0),
    alertCount: 0,
    insight: latestWindow
      ? `最近窗口 ${latestWindow.window_id || 0}，motion ${Number(latestWindow.motion_level || 0).toFixed(4)}`
      : '当前尚未归档成日级窗口，先展示最近 1 分钟实时缓存。',
    summary: latestWindow
      ? '当前页面正在使用最近一次被动窗口对应的缓存波形。'
      : '当前页面正在使用尚未归档的最近 1 分钟实时缓存。',
    suggestion: '如需更稳定结论，建议继续保持贴合并等待完整被动窗口生成。',
    windowCount: latestWindow ? 1 : 0,
    latestWindowId: latestWindow ? latestWindow.window_id || 0 : 0,
    latestWindowEndTsMs: timestampMs,
    respWavePoints: runtime.state.respWavePoints.slice(-MAX_RESP_REPORT_POINTS),
    respBeatMarkerPoints: runtime.state.respBeatMarkerPoints.slice(-MAX_RESP_REPORT_POINTS),
    chestPpgWavePoints: runtime.state.chestPpgWavePoints.slice(-MAX_PPG_REPORT_POINTS),
    chestPpgBeatMarkerPoints: runtime.state.chestPpgBeatMarkerPoints.slice(-MAX_PPG_REPORT_POINTS),
    timeline: []
  };
}

function buildInsightPrompt() {
  const latestDaily = runtime.state.dailyAnalyses.map((item) => ({
    day: item.day,
    respirationAvg: item.respirationAvg,
    heartRateAvg: item.heartRateAvg,
    stabilityScore: item.stabilityScore,
    windowCount: item.windowCount,
    latestWindowId: item.latestWindowId,
    summary: item.summary,
    insight: item.insight,
    suggestion: item.suggestion,
    timeline: item.timeline || []
  }));
  const latestActive = runtime.state.activeMeasurements.map((item) => ({
    id: item.id,
    title: item.title,
    resultTag: item.resultTag,
    startedAt: item.startedAt,
    summary: item.summary,
    metrics: item.metrics,
    briefAnalysis: item.briefAnalysis,
    briefAdvice: item.briefAdvice,
    generatedReportText: item.generatedReportText || ''
  }));
  const latestDailyWave = runtime.state.dailyAnalyses[0] || buildFallbackDailyAnalysis() || null;
  const latestActiveWave = runtime.state.activeMeasurements[0] || null;

  return [
    '你是健康监测整体状态摘要助手。',
    '请基于下面的小程序真实缓存数据，判断用户当前整体状态与近期趋势，而不是逐点复述数据本身。',
    '要求：',
    '1. 不夸大结论，不使用医学诊断口吻。',
    '2. 重点回答“用户目前整体状态怎样、近期趋势怎样、接下来最值得关注什么”。',
    '3. 明确说明哪些判断来自呼吸/胸口PPG/指部PPG，哪些地方因为数据量或质量有限只能低置信度参考。',
    '4. 输出 JSON 字符串。',
    '5. JSON 结构为 {"title":"整体分析","summary":"...","advice":"...","sections":[{"key":"resp","title":"呼吸报告","body":"..."},{"key":"heart","title":"当天心率报告","body":"..."},{"key":"active","title":"指部 PPG 报告","body":"..."},{"key":"overall","title":"总结板块","body":"..."}] }。',
    `被动日级数据: ${JSON.stringify(latestDaily)}`,
    `主动检测数据: ${JSON.stringify(latestActive)}`,
    `最近呼吸波形采样: ${JSON.stringify(latestDailyWave ? sampleSeriesForPrompt(latestDailyWave.respWavePoints || [], 160, false) : [])}`,
    `最近呼吸跳点采样: ${JSON.stringify(latestDailyWave ? sampleSeriesForPrompt(latestDailyWave.respBeatMarkerPoints || [], 160, true) : [])}`,
    `最近胸口PPG波形采样: ${JSON.stringify(latestDailyWave ? sampleSeriesForPrompt(latestDailyWave.chestPpgWavePoints || [], 220, false) : [])}`,
    `最近胸口PPG跳点采样: ${JSON.stringify(latestDailyWave ? sampleSeriesForPrompt(latestDailyWave.chestPpgBeatMarkerPoints || [], 220, true) : [])}`,
    `最近指部PPG波形采样: ${JSON.stringify(latestActiveWave ? (latestActiveWave.ppgWavePoints || []) : [])}`,
    `最近指部PPG跳点采样: ${JSON.stringify(latestActiveWave ? (latestActiveWave.ppgBeatMarkerPoints || []) : [])}`
  ].join('\n');
}

async function refreshOverallInsight(force = false) {
  if (runtime.state.insightStatus === 'running' && !force) {
    return;
  }

  const hasDaily = (runtime.state.dailyAnalyses || []).length > 0;
  const hasActive = (runtime.state.activeMeasurements || []).length > 0;
  if (!hasDaily && !hasActive) {
    runtime.state.overallSummary = buildEmptyOverallSummary();
    runtime.state.insightStatus = 'idle';
    persistState();
    emitState();
    return;
  }

  runtime.state.insightStatus = 'running';
  emitState();

  try {
    const result = await wx.cloud.callFunction({
      name: 'health_insight',
      data: {
        prompt: buildInsightPrompt()
      }
    });
    const replyText = result && result.result && result.result.reply_text
      ? result.result.reply_text
      : '';
    runtime.state.overallSummary = parseInsightReply(replyText);
    runtime.state.insightStatus = 'done';
  } catch (error) {
    console.error('refresh overall insight failed', error);
    runtime.state.overallSummary = buildFallbackInsight();
    runtime.state.insightStatus = 'fallback';
  }

  persistState();
  emitState();
}

function upsertDailyAnalysis(payload) {
  const analyses = runtime.state.dailyAnalyses.slice();
  const dayKey = formatDateOnly(payload.window_end_ts_ms);
  const existingIndex = analyses.findIndex((item) => item.dayKey === dayKey);
  const existing = existingIndex >= 0 ? analyses[existingIndex] : null;
  const windowCount = existing ? existing.windowCount + 1 : 1;
  const avgResp = existing
    ? Math.round(((existing.respirationAvg || 0) * existing.windowCount + Number(payload.resp_rate_bpm || 0)) / windowCount)
    : Number(payload.resp_rate_bpm || 0);
  const avgHeart = existing
    ? Math.round(((existing.heartRateAvg || 0) * existing.windowCount + Number(runtime.state.currentHeartBpm || 0)) / windowCount)
    : Number(runtime.state.currentHeartBpm || 0);
  const avgQuality = existing
    ? Math.round(((existing.stabilityScore || 0) * existing.windowCount + Number(payload.quality_score || 0)) / windowCount)
    : Number(payload.quality_score || 0);

  const nextDay = {
    dayKey,
    day: dayKey,
    title: dayKey,
    respirationAvg: avgResp,
    heartRateAvg: avgHeart,
    stabilityScore: avgQuality,
    alertCount: 0,
    insight: `最近窗口 ${payload.window_id || 0}，motion ${Number(payload.motion_level || 0).toFixed(4)}`,
    summary: `今日已累计 ${windowCount} 个真实被动窗口。`,
    suggestion: avgQuality < 60 ? '稳定度偏低，建议先保证佩戴贴合与静止。' : '当前波形稳定度尚可，可继续积累观察。',
    windowCount,
    latestWindowId: payload.window_id || 0,
    latestWindowEndTsMs: Number(payload.window_end_ts_ms || 0),
    respWavePoints: runtime.state.respWavePoints.slice(-MAX_RESP_REPORT_POINTS),
    respBeatMarkerPoints: runtime.state.respBeatMarkerPoints.slice(-MAX_RESP_REPORT_POINTS),
    chestPpgWavePoints: runtime.state.chestPpgWavePoints.slice(-MAX_PPG_REPORT_POINTS),
    chestPpgBeatMarkerPoints: runtime.state.chestPpgBeatMarkerPoints.slice(-MAX_PPG_REPORT_POINTS),
    generatedReport: existing && existing.generatedReport ? existing.generatedReport : '',
    generatedReportUpdatedAt: existing && existing.generatedReportUpdatedAt ? existing.generatedReportUpdatedAt : '',
    timeline: existing && Array.isArray(existing.timeline) ? existing.timeline.slice() : []
  };

  nextDay.timeline.unshift({
    time: formatDateTime(payload.window_end_ts_ms).slice(11, 16),
    label: `窗口 ${payload.window_id || 0}`,
    value: `呼吸 ${payload.resp_rate_bpm || 0} 次/分`,
    level: Number(payload.quality_score || 0) >= 85 ? 'strong' : (Number(payload.quality_score || 0) >= 60 ? 'warm' : 'soft')
  });
  nextDay.timeline = nextDay.timeline.slice(0, 12);

  if (existingIndex >= 0) {
    analyses.splice(existingIndex, 1, nextDay);
  } else {
    analyses.unshift(nextDay);
  }

  runtime.state.dailyAnalyses = analyses.slice(0, MAX_DAILY_ANALYSES);
  trimOldRecords();
  persistState();
  refreshOverallInsight();
}

function appendActiveMeasurement(payload, options = {}) {
  const measurements = runtime.state.activeMeasurements.slice();
  const id = resolveActiveMeasurementId(payload, `${Date.now()}`);
  const existingItem = measurements.find((item) => item.id === id) || null;
  const nextItem = buildActiveMeasurementRecord(payload, existingItem, options);

  const filtered = measurements.filter((item) => item.id !== id).map(stripFullActiveWave);
  filtered.unshift(nextItem);
  runtime.state.activeMeasurements = filtered.slice(0, MAX_ACTIVE_MEASUREMENTS);
  trimOldRecords();
  persistState();
  emitState();
  refreshOverallInsight();
}

function applyDeviceState(payload) {
  runtime.state.currentDeviceState = payload.device_state || '';
  if (payload.device_state !== 'RESP_CALIBRATING') {
    runtime.state.currentGuideText = payload.guide_text || payload.status_text || '';
  }
  if (payload.device_state === 'BREATH_GUIDE_SESSION') {
    runtime.state.currentPhaseText = payload.phase_type || runtime.state.currentPhaseText || '';
    runtime.state.phaseRemainingMs = Number(payload.phase_remaining_ms || 0);
    runtime.state.currentAxisName = '';
    runtime.state.currentCalibrationStep = 0;
  } else if (payload.device_state !== 'RESP_CALIBRATING') {
    runtime.state.currentPhaseText = '';
    runtime.state.phaseRemainingMs = 0;
    runtime.state.currentAxisName = '';
  }
  runtime.state.connectionStatus = payload.ble_state ? `设备 ${payload.ble_state}` : runtime.state.connectionStatus;
  pushDebugLog(`状态 ${payload.device_state || 'UNKNOWN'} / ${payload.ble_state || 'UNKNOWN'}`);
}

function applyRespDebug(payload, packetKind) {
  appendWavePoint('respWavePoints', Number(payload.resp_signal_value || 0));
  appendWavePoint('respBeatMarkerPoints', Number(payload.resp_beat_marker_value || 0));
  trimArrayToCap('respWavePoints', MAX_RESP_REPORT_POINTS);
  trimArrayToCap('respBeatMarkerPoints', MAX_RESP_REPORT_POINTS);
  runtime.state.currentRespBpm = Number(payload.resp_rate_bpm || 0);
  runtime.state.currentMotionLevel = Number(payload.motion_level || 0).toFixed(4);
  if (runtime.state.currentDeviceState === 'RESP_CALIBRATING') {
    runtime.state.currentPhaseText = payload.phase_type || payload.axis_name || '';
  }
  runtime.state.currentGuideText = payload.guide_text || runtime.state.currentGuideText;
  runtime.state.currentAxisName = runtime.state.currentDeviceState === 'RESP_CALIBRATING'
    ? (payload.axis_name || '')
    : '';
  runtime.state.currentCalibrationStep = Number(payload.calibration_step || runtime.state.currentCalibrationStep || 0);
  runtime.state.phaseRemainingMs = Number(payload.phase_remaining_ms || runtime.state.phaseRemainingMs || 0);
  runtime.state.respWaveSummary = `${packetKind} / axis ${payload.axis_name || '-'} / amp ${Number(payload.resp_amplitude || 0).toFixed(4)}`;
}

function applyActiveRealtime(payload) {
  appendWavePoint('heartWavePoints', Number(payload.i6_filtered_point || 0));
  appendWavePoint('heartBeatMarkerPoints', Number(payload.i7_beat_marker || 0));
  runtime.state.currentHeartBpm = Number(payload.heart_rate_bpm || 0);
  runtime.state.currentActiveHeartBpm = Number(payload.heart_rate_bpm || 0);
  runtime.state.currentSignalQuality = Number(payload.quality_score || 0);
  runtime.state.currentBeatCount = Number(payload.beat_count || 0);
  runtime.state.currentActiveBeatCount = Number(payload.beat_count || 0);
  runtime.state.heartWaveSummary = `I6 filtered / I7 beatMarker / ${payload.contact_present ? 'contact ok' : 'contact weak'} / measurement ${payload.measurement_id || 0}`;
}

function applyActiveRealtimeBatch(payload) {
  appendWavePoints('heartWavePoints', payload.i6 || []);
  appendWavePoints('heartBeatMarkerPoints', payload.i7 || []);
  const pendingMeasurement = getOrCreatePendingActiveRealtimeMeasurement(payload.measurement_id || 0);
  if (!pendingMeasurement.startedAtTsMs) {
    pendingMeasurement.startedAtTsMs = Number(payload.ts_ms_end || 0) -
      (Number(payload.sample_count || 0) * Number(payload.dt_ms || 0));
  }
  pendingMeasurement.wavePoints = pendingMeasurement.wavePoints.concat((payload.i6 || []).map((value) => Number(value || 0))).slice(-MAX_PPG_REPORT_POINTS);
  pendingMeasurement.beatMarkerPoints = pendingMeasurement.beatMarkerPoints.concat((payload.i7 || []).map((value) => Number(value || 0))).slice(-MAX_PPG_REPORT_POINTS);
  pendingMeasurement.beatCount = Number(payload.bc || pendingMeasurement.beatCount || 0);
  pendingMeasurement.heartRateBpm = Number(payload.bpm || pendingMeasurement.heartRateBpm || 0);
  pendingMeasurement.lastBeatIntervalMs = Number(payload.i12 || pendingMeasurement.lastBeatIntervalMs || 0);
  pendingMeasurement.sampleIntervalMs = Number(payload.dt_ms || pendingMeasurement.sampleIntervalMs || 0);
  pendingMeasurement.tsMsEnd = Number(payload.ts_ms_end || pendingMeasurement.tsMsEnd || 0);
  runtime.state.currentHeartBpm = Number(payload.bpm || 0);
  runtime.state.currentActiveHeartBpm = Number(payload.bpm || 0);
  runtime.state.currentSignalQuality = Number(payload.qs || 0);
  runtime.state.currentBeatCount = Number(payload.bc || 0);
  runtime.state.currentActiveBeatCount = Number(payload.bc || 0);
  if (runtime.state.latestActiveWindow) {
    const latestWindowId = `${runtime.state.latestActiveWindow.measurement_id || ''}`;
    const batchMeasurementId = `${payload.measurement_id || ''}`;
    if (!latestWindowId || !batchMeasurementId || latestWindowId === batchMeasurementId) {
      runtime.state.latestActiveWindow = {
        ...runtime.state.latestActiveWindow,
        realtime_heart_rate_bpm: runtime.state.currentActiveHeartBpm,
        realtime_beat_count: runtime.state.currentActiveBeatCount,
        realtime_point_count: pendingMeasurement.wavePoints.length,
        realtime_duration_ms: Number(pendingMeasurement.sampleIntervalMs || 0) * Number(pendingMeasurement.wavePoints.length || 0)
      };
    }
  }
  runtime.state.heartWaveSummary = `batch ${Number(payload.sample_count || 0)} pts / dt ${Number(payload.dt_ms || 0)} ms / ${Number(payload.cp || 0) ? 'contact ok' : 'contact weak'} / measurement ${payload.measurement_id || 0}`;
}

function applyPassiveWindow(payload) {
  runtime.state.latestPassiveWindow = payload;
  runtime.state.currentRespBpm = Number(payload.resp_rate_bpm || runtime.state.currentRespBpm || 0);
  runtime.state.respWaveSummary = `被动窗口 ${payload.window_id || 0} / ${payload.point_count || 0} points / 呼吸 ${payload.resp_rate_bpm || 0} bpm`;
  upsertDailyAnalysis(payload);
  pushDebugLog(`被动窗口 ${payload.window_id || 0} 完成，呼吸 ${payload.resp_rate_bpm || 0} bpm`);
}

function applyPassivePpgBatch(payload) {
  appendWavePointsWithCap('chestPpgWavePoints', payload.i6 || [], MAX_PPG_REPORT_POINTS);
  appendWavePointsWithCap('chestPpgBeatMarkerPoints', payload.i7 || [], MAX_PPG_REPORT_POINTS);
  runtime.state.currentHeartBpm = Number(payload.bpm || runtime.state.currentHeartBpm || 0);
  runtime.state.currentSignalQuality = Number(payload.qs || runtime.state.currentSignalQuality || 0);
}

function applyActiveWindow(payload) {
  const measurementId = `${payload.measurement_id || 0}`;
  const fragmentTotal = Math.max(1, Number(payload.fragment_total || 1));
  const existing = runtime.pendingActiveWindows[measurementId] || {
    measurementId,
    fragmentTotal,
    sampleStartTsMs: Number(payload.sample_start_ts_ms || 0),
    sampleEndTsMs: Number(payload.sample_end_ts_ms || 0),
    heartRateBpm: Number(payload.heart_rate_bpm || 0),
    qualityScore: Number(payload.quality_score || 0),
    processedPointCount: Number(payload.processed_point_count || 0),
    beatCount: Number(payload.beat_count || 0),
    rrIntervalCount: Number(payload.rr_interval_count || 0),
    processedPoints: new Array(Number(payload.processed_point_count || 0)).fill(null),
    beatTsMs: new Array(Number(payload.beat_count || 0)).fill(null),
    rrIntervalsMs: new Array(Number(payload.rr_interval_count || 0)).fill(null),
    receivedFragments: {}
  };

  const processedPointOffset = Number(payload.processed_point_offset || 0);
  const processedPointsFragment = Array.isArray(payload.processed_points_fragment)
    ? payload.processed_points_fragment
    : [];
  processedPointsFragment.forEach((value, index) => {
    const targetIndex = processedPointOffset + index;
    if (targetIndex < existing.processedPoints.length) {
      existing.processedPoints[targetIndex] = Number(value || 0);
    }
  });

  const beatOffset = Number(payload.beat_offset || 0);
  const beatTsMsFragment = Array.isArray(payload.beat_ts_ms_fragment)
    ? payload.beat_ts_ms_fragment
    : [];
  beatTsMsFragment.forEach((value, index) => {
    const targetIndex = beatOffset + index;
    if (targetIndex < existing.beatTsMs.length) {
      existing.beatTsMs[targetIndex] = Number(value || 0);
    }
  });

  const rrIntervalsMsFragment = Array.isArray(payload.rr_intervals_ms_fragment)
    ? payload.rr_intervals_ms_fragment
    : [];
  rrIntervalsMsFragment.forEach((value, index) => {
    if (index < existing.rrIntervalsMs.length) {
      existing.rrIntervalsMs[index] = Number(value || 0);
    }
  });

  existing.receivedFragments[Number(payload.fragment_index || 0)] = true;
  runtime.pendingActiveWindows[measurementId] = existing;

  const pendingRealtimeMeasurement = getOrCreatePendingActiveRealtimeMeasurement(measurementId);
  const receivedFragmentCount = Object.keys(existing.receivedFragments).length;
  const realtimeDurationMs = Number(pendingRealtimeMeasurement.sampleIntervalMs || 0) * Number(pendingRealtimeMeasurement.wavePoints.length || 0);
  const realtimePointTarget = Number(pendingRealtimeMeasurement.sampleIntervalMs || 0) > 0
    ? Math.round(60000 / Number(pendingRealtimeMeasurement.sampleIntervalMs || 0))
    : 0;
  const latestRrIntervalsMs = existing.rrIntervalsMs.filter((value) => value !== null && value !== undefined);
  const latestBeatTimelineMs = latestRrIntervalsMs.length > 0
    ? buildBeatTimelineMsFromIntervals(latestRrIntervalsMs)
    : buildBeatTimelineMs(
      existing.beatTsMs,
      payload.sample_start_ts_ms,
      pendingRealtimeMeasurement.beatMarkerPoints,
      realtimeDurationMs > 0 ? realtimeDurationMs : (Number(payload.sample_end_ts_ms || 0) - Number(payload.sample_start_ts_ms || 0))
    );
  const realtimeComplete = pendingRealtimeMeasurement.wavePoints.length > 0 && (
    (realtimePointTarget > 0 && pendingRealtimeMeasurement.wavePoints.length >= Math.max(1200, Math.floor(realtimePointTarget * 0.9)))
    || pendingRealtimeMeasurement.wavePoints.length >= Math.max(1200, Math.floor(Number(payload.processed_point_count || 0) * 0.9))
    || realtimeDurationMs >= 55000
  );

  runtime.state.latestActiveWindow = {
    ...payload,
    received_fragment_count: receivedFragmentCount,
    fragment_total: fragmentTotal,
    realtime_point_count: pendingRealtimeMeasurement.wavePoints.length,
    realtime_duration_ms: realtimeDurationMs,
    realtime_complete: realtimeComplete,
    realtime_heart_rate_bpm: Number(pendingRealtimeMeasurement.heartRateBpm || payload.heart_rate_bpm || 0),
    realtime_beat_count: Number(pendingRealtimeMeasurement.beatCount || payload.beat_count || 0),
    beat_timeline_ms: latestBeatTimelineMs,
    rr_intervals_ms: latestRrIntervalsMs
  };
  runtime.state.currentHeartBpm = Number(pendingRealtimeMeasurement.heartRateBpm || runtime.state.currentHeartBpm || payload.heart_rate_bpm || 0);
  runtime.state.currentActiveHeartBpm = Number(pendingRealtimeMeasurement.heartRateBpm || runtime.state.currentActiveHeartBpm || payload.heart_rate_bpm || 0);
  runtime.state.currentSignalQuality = Number(payload.quality_score || runtime.state.currentSignalQuality || 0);
  runtime.state.currentBeatCount = Number(pendingRealtimeMeasurement.beatCount || runtime.state.currentBeatCount || payload.beat_count || 0);
  runtime.state.currentActiveBeatCount = Number(pendingRealtimeMeasurement.beatCount || runtime.state.currentActiveBeatCount || payload.beat_count || 0);
  runtime.state.heartWaveSummary = `主动窗口 ${payload.measurement_id || 0} / ${payload.processed_point_count || 0} points / realtime ${pendingRealtimeMeasurement.wavePoints.length} / frag ${receivedFragmentCount}/${fragmentTotal} / 心率 ${runtime.state.currentActiveHeartBpm || 0} bpm`;

  appendActiveMeasurement({
    ...payload,
    processed_points: existing.processedPoints,
    beat_ts_ms: existing.beatTsMs,
    rr_intervals_ms: latestRrIntervalsMs
  }, {
    isPartial: !realtimeComplete,
    receivedFragmentCount,
    fragmentTotal,
    fullWavePoints: pendingRealtimeMeasurement.wavePoints,
    fullBeatMarkerPoints: pendingRealtimeMeasurement.beatMarkerPoints,
    realtimeComplete,
    realtimeDurationMs,
    realtimePointTarget,
    realtimeHeartRateBpm: pendingRealtimeMeasurement.heartRateBpm,
    realtimeBeatCount: pendingRealtimeMeasurement.beatCount,
    realtimeSampleIntervalMs: pendingRealtimeMeasurement.sampleIntervalMs
  });

  const complete = receivedFragmentCount >= fragmentTotal &&
    existing.processedPoints.every((value) => value !== null) &&
    existing.rrIntervalsMs.every((value) => value !== null);
  if (complete) {
    const completedRealtimeMeasurement = consumePendingActiveRealtimeMeasurement(measurementId) || pendingRealtimeMeasurement;
    appendActiveMeasurement({
      ...payload,
      processed_points: existing.processedPoints,
      beat_ts_ms: existing.beatTsMs,
      rr_intervals_ms: latestRrIntervalsMs
    }, {
      isPartial: false,
      receivedFragmentCount,
      fragmentTotal,
      fullWavePoints: completedRealtimeMeasurement.wavePoints,
      fullBeatMarkerPoints: completedRealtimeMeasurement.beatMarkerPoints,
      realtimeComplete: true,
      realtimeDurationMs: Number(completedRealtimeMeasurement.sampleIntervalMs || 0) * Number(completedRealtimeMeasurement.wavePoints.length || 0),
      realtimePointTarget: Number(completedRealtimeMeasurement.sampleIntervalMs || 0) > 0
        ? Math.round(60000 / Number(completedRealtimeMeasurement.sampleIntervalMs || 0))
        : 0,
      realtimeHeartRateBpm: completedRealtimeMeasurement.heartRateBpm,
      realtimeBeatCount: completedRealtimeMeasurement.beatCount,
      realtimeSampleIntervalMs: completedRealtimeMeasurement.sampleIntervalMs
    });
    delete runtime.pendingActiveWindows[measurementId];
    pushDebugLog(`主动检测完成，hr ${completedRealtimeMeasurement.heartRateBpm || payload.heart_rate_bpm || 0} bpm / beat ${completedRealtimeMeasurement.beatCount || payload.beat_count || 0} / full points ${existing.processedPoints.length}`);
  } else if (realtimeComplete) {
    pushDebugLog(`主动检测 ${payload.measurement_id || 0} 已拿到完整实时累计，当前分片 ${receivedFragmentCount}/${fragmentTotal}`);
  }
}

function applyDebugPacket(packet) {
  const payload = packet.payload || {};
  runtime.state.lastEventTime = packet.receivedAtLabel || '';
  runtime.state.lastPacketType = packet.kind || '';
  runtime.state.lastEventRaw = packet.rawText || '';

  if (packet.kind === 'invalid') {
    runtime.state.connectionStatus = '收到无法解析的通知';
    pushDebugLog(`解析失败: ${packet.rawText}`);
    emitState();
    return;
  }

  switch (packet.kind) {
    case 'device_state':
      applyDeviceState(payload);
      break;
    case 'calibration_status':
    case 'resp_debug':
      applyRespDebug(payload, packet.kind);
      break;
    case 'active_realtime':
      applyActiveRealtime(payload);
      break;
    case 'active_realtime_batch':
      applyActiveRealtimeBatch(payload);
      break;
    case 'passive_resp_window':
      applyPassiveWindow(payload);
      break;
    case 'passive_ppg_batch':
      applyPassivePpgBatch(payload);
      break;
    case 'active_window':
      applyActiveWindow(payload);
      break;
    case 'debug_log':
      pushDebugLog(payload.message || '收到调试日志');
      break;
    case 'error_status':
      pushDebugLog(`错误 ${payload.error_code || 0}: ${payload.error_message || 'unknown'}`);
      break;
    default:
      pushDebugLog(`收到未归类消息: ${packet.kind}`);
      break;
  }

  emitState();
}

function resetLiveData() {
  runtime.pendingActiveWindows = {};
  runtime.pendingActiveRealtimeMeasurements = {};
  runtime.state.lastEventTime = '';
  runtime.state.lastPacketType = '';
  runtime.state.lastEventRaw = '';
  runtime.state.currentDeviceState = '';
  runtime.state.currentGuideText = '';
  runtime.state.currentPhaseText = '';
  runtime.state.currentRespBpm = '';
  runtime.state.currentHeartBpm = '';
  runtime.state.currentActiveHeartBpm = '';
  runtime.state.currentMotionLevel = '';
  runtime.state.currentSignalQuality = 0;
  runtime.state.currentBeatCount = 0;
  runtime.state.currentActiveBeatCount = 0;
  runtime.state.currentAxisName = '';
  runtime.state.currentCalibrationStep = 0;
  runtime.state.phaseRemainingMs = 0;
  runtime.state.respWaveSummary = '';
  runtime.state.heartWaveSummary = '';
  runtime.state.respWavePoints = [];
  runtime.state.respBeatMarkerPoints = [];
  runtime.state.heartWavePoints = [];
  runtime.state.heartBeatMarkerPoints = [];
  runtime.state.chestPpgWavePoints = [];
  runtime.state.chestPpgBeatMarkerPoints = [];
}

function connectToKnownDevice(deviceId, deviceName) {
  if (!deviceId || runtime.connecting) {
    return;
  }

  clearAutoReconnectTimer();
  runtime.connecting = true;
  runtime.state.deviceId = deviceId;
  runtime.state.deviceName = deviceName || runtime.state.deviceName || 'HOLD-INTEGRATED';
  runtime.state.connectionStatus = '正在连接';
  emitState();

  wx.createBLEConnection({
    deviceId,
    timeout: 10000,
    success: () => {
      runtime.state.connectionStatus = '已连接，获取服务中';
      emitState();
      wx.getBLEDeviceServices({
        deviceId,
        success: (serviceResult) => {
          const service = (serviceResult.services || []).find((item) =>
            (item.uuid || '').toLowerCase() === bleDebugProtocol.SERVICE_UUID
          );
          if (!service) {
            runtime.connecting = false;
            runtime.state.connectionStatus = '未找到目标服务';
            emitState();
            return;
          }

          runtime.state.serviceId = service.uuid;
          runtime.state.connectionStatus = '服务已找到，获取特征中';
          emitState();
          wx.getBLEDeviceCharacteristics({
            deviceId,
            serviceId: service.uuid,
            success: (characteristicResult) => {
                  const characteristic = bleDebugProtocol.findNotifyCharacteristic(characteristicResult.characteristics || []);
                  const writeCharacteristic = bleDebugProtocol.findWriteCharacteristic(characteristicResult.characteristics || []);
                  if (!characteristic) {
                runtime.connecting = false;
                runtime.state.connectionStatus = '未找到可订阅调试特征';
                emitState();
                return;
              }

              runtime.state.notifyCharacteristicId = characteristic.uuid;
                  runtime.state.writeCharacteristicId = writeCharacteristic ? writeCharacteristic.uuid : '';
              wx.notifyBLECharacteristicValueChange({
                deviceId,
                serviceId: service.uuid,
                characteristicId: characteristic.uuid,
                state: true,
                success: () => {
                  runtime.connecting = false;
                  runtime.state.isConnected = true;
                  runtime.reconnectAttemptsRemaining = 0;
                  runtime.state.connectionStatus = '已订阅调试通知';
                  runtime.state.adapterStatus = '蓝牙链路已打通，等待状态与波形数据';
                  pushDebugLog('已订阅设备调试通知');
                  emitState();
                },
                fail: (error) => {
                  runtime.connecting = false;
                  runtime.state.connectionStatus = `订阅失败: ${error.errCode || error.errMsg}`;
                  emitState();
                }
              });
            },
            fail: (error) => {
              runtime.connecting = false;
              runtime.state.connectionStatus = `获取特征失败: ${error.errCode || error.errMsg}`;
              emitState();
            }
          });
        },
        fail: (error) => {
          runtime.connecting = false;
          runtime.state.connectionStatus = `获取服务失败: ${error.errCode || error.errMsg}`;
          emitState();
        }
      });
    },
    fail: (error) => {
      runtime.connecting = false;
      runtime.state.connectionStatus = `连接失败: ${error.errCode || error.errMsg}`;
      emitState();
      scheduleAutoReconnect();
    }
  });
}

function scheduleAutoReconnect() {
  if (runtime.manualDisconnectRequested || runtime.state.isConnected || runtime.connecting || !runtime.state.deviceId) {
    return;
  }

  if (runtime.reconnectAttemptsRemaining <= 0) {
    return;
  }

  clearAutoReconnectTimer();
  runtime.autoReconnectTimer = setTimeout(() => {
    runtime.autoReconnectTimer = null;
    runtime.reconnectAttemptsRemaining -= 1;
    runtime.state.adapterStatus = `蓝牙意外断开，准备重连（剩余 ${runtime.reconnectAttemptsRemaining} 次）`;
    emitState();
    connectToKnownDevice(runtime.state.deviceId, runtime.state.deviceName);
  }, AUTO_RECONNECT_DELAY_MS);
}

function handleDiscoveredDevices(result) {
  const devices = result.devices || [];
  const target = bleDebugProtocol.findTargetDevice(devices);
  if (!target || runtime.connecting || runtime.state.isConnected) {
    return;
  }

  runtime.state.deviceName = target.name || target.localName || 'HOLD-INTEGRATED';
  runtime.state.deviceId = target.deviceId;
  runtime.state.adapterStatus = '已发现目标设备';
  emitState();
  wx.stopBluetoothDevicesDiscovery({ complete: () => {} });
  runtime.state.scanning = false;
  runtime.manualDisconnectRequested = false;
  runtime.reconnectAttemptsRemaining = 3;
  connectToKnownDevice(target.deviceId, runtime.state.deviceName);
}

function handleConnectionStateChange(result) {
  if (result.connected) {
    return;
  }

  runtime.connecting = false;
  runtime.state.isConnected = false;
  runtime.state.serviceId = '';
  runtime.state.notifyCharacteristicId = '';
  resetLiveData();

  if (runtime.manualDisconnectRequested || !runtime.state.deviceId) {
    runtime.state.connectionStatus = '已断开';
    runtime.state.adapterStatus = '蓝牙已断开';
    pushDebugLog('BLE 连接已断开');
    emitState();
    return;
  }

  runtime.state.connectionStatus = '连接中断，准备自动重连';
  runtime.state.adapterStatus = '蓝牙链路发生中断';
  pushDebugLog('BLE 意外断开，准备自动重连');
  if (runtime.reconnectAttemptsRemaining <= 0) {
    runtime.reconnectAttemptsRemaining = 3;
  }
  emitState();
  scheduleAutoReconnect();
}

function init() {
  if (runtime.initialized) {
    return;
  }

  runtime.initialized = true;
  hydrateStateFromStorage();
  wx.onBLECharacteristicValueChange((result) => {
    applyDebugPacket(bleDebugProtocol.parseBleNotifyBuffer(result.value));
  });

  wx.onBluetoothDeviceFound(handleDiscoveredDevices);
  wx.onBLEConnectionStateChange(handleConnectionStateChange);
  emitState();
}

function subscribe(listener) {
  runtime.listeners.push(listener);
  listener(cloneState());
  return () => {
    runtime.listeners = runtime.listeners.filter((item) => item !== listener);
  };
}

function getState() {
  return cloneState();
}

function startScanAndConnect() {
  if (runtime.state.isConnected || runtime.connecting) {
    emitState();
    return;
  }

  clearAutoReconnectTimer();
  runtime.manualDisconnectRequested = false;
  runtime.reconnectAttemptsRemaining = 3;
  resetLiveData();
  runtime.state.adapterStatus = '初始化蓝牙中';
  runtime.state.connectionStatus = '未连接';
  runtime.state.scanning = true;
  emitState();

  wx.openBluetoothAdapter({
    success: () => {
      runtime.state.adapterStatus = '蓝牙已开启，开始扫描';
      emitState();
      wx.startBluetoothDevicesDiscovery({
        allowDuplicatesKey: false,
        success: () => {
          runtime.state.adapterStatus = '扫描中，等待目标设备...';
          runtime.state.scanning = true;
          emitState();
        },
        fail: (error) => {
          runtime.state.adapterStatus = `扫描失败: ${error.errCode || error.errMsg}`;
          runtime.state.scanning = false;
          emitState();
        }
      });
    },
    fail: (error) => {
      runtime.state.adapterStatus = `蓝牙初始化失败: ${error.errCode || error.errMsg}`;
      runtime.state.scanning = false;
      emitState();
    }
  });
}

function disconnect() {
  if (!runtime.state.deviceId) {
    return;
  }

  clearAutoReconnectTimer();
  runtime.manualDisconnectRequested = true;
  wx.closeBLEConnection({
    deviceId: runtime.state.deviceId,
    complete: () => {
      runtime.connecting = false;
      runtime.state.isConnected = false;
      runtime.reconnectAttemptsRemaining = 0;
      runtime.state.connectionStatus = '已断开';
      runtime.state.adapterStatus = '蓝牙已断开';
      runtime.state.deviceName = '';
      runtime.state.deviceId = '';
      runtime.state.serviceId = '';
      runtime.state.notifyCharacteristicId = '';
      runtime.state.writeCharacteristicId = '';
      resetLiveData();
      runtime.manualDisconnectRequested = false;
      emitState();
    }
  });
}

function startBreathGuide() {
  return new Promise((resolve, reject) => {
    if (!runtime.state.isConnected || !runtime.state.deviceId || !runtime.state.serviceId || !runtime.state.writeCharacteristicId) {
      reject(new Error('bluetooth-not-ready'));
      return;
    }

    const commandText = JSON.stringify({
      cmd: 'start_breath_guide',
      cycles: 6,
      inhale_ms: 4000,
      exhale_ms: 5000,
      duration_ms: 54000
    });

    wx.writeBLECharacteristicValue({
      deviceId: runtime.state.deviceId,
      serviceId: runtime.state.serviceId,
      characteristicId: runtime.state.writeCharacteristicId,
      value: stringToArrayBuffer(commandText),
      success: () => {
        runtime.state.currentGuideText = '呼吸引导启动中';
        pushDebugLog('已发送呼吸引导启动命令');
        emitState();
        resolve({ ok: true });
      },
      fail: (error) => {
        reject(new Error(error && (error.errMsg || error.errCode) ? `${error.errMsg || error.errCode}` : 'write-failed'));
      }
    });
  });
}

function startActiveTest(options = {}) {
  return new Promise((resolve, reject) => {
    if (!runtime.state.isConnected || !runtime.state.deviceId || !runtime.state.serviceId || !runtime.state.writeCharacteristicId) {
      reject(new Error('bluetooth-not-ready'));
      return;
    }

    const commandText = JSON.stringify({
      cmd: 'start_active_test',
      duration_ms: Number(options.durationMs || 60000)
    });

    wx.writeBLECharacteristicValue({
      deviceId: runtime.state.deviceId,
      serviceId: runtime.state.serviceId,
      characteristicId: runtime.state.writeCharacteristicId,
      value: stringToArrayBuffer(commandText),
      success: () => {
        pushDebugLog(`已发送主动检测启动命令 duration=${options.durationMs || 60000}ms`);
        emitState();
        resolve({ ok: true });
      },
      fail: (error) => {
        pushDebugLog(`主动检测启动命令发送失败: ${error && (error.errMsg || error.errCode) ? error.errMsg || error.errCode : 'write-failed'}`);
        reject(new Error(error && (error.errMsg || error.errCode) ? `${error.errMsg || error.errCode}` : 'write-failed'));
      }
    });
  });
}

function clearCachedData() {
  resetLiveData();
  runtime.state.debugLogs = [];
  runtime.state.activeMeasurements = [];
  runtime.state.dailyAnalyses = [];
  runtime.state.latestPassiveWindow = null;
  runtime.state.latestActiveWindow = null;
  runtime.state.overallSummary = buildEmptyOverallSummary();
  persistState();
  emitState();
}

function getOverallSummary() {
  return cloneState().overallSummary;
}

function ensureActiveMeasurementFromLatestWindow(id) {
  const latestWindow = runtime.state.latestActiveWindow;
  const latestWindowId = latestWindow ? resolveActiveMeasurementId(latestWindow, 'latest') : '';
  const measurementId = `${id || latestWindowId || (latestWindow && latestWindow.measurement_id) || ''}`;
  if (!measurementId || !latestWindow) {
    return null;
  }

  const existingMeasurement = (runtime.state.activeMeasurements || []).find((item) => item.id === measurementId)
    || (runtime.state.activeMeasurements || []).find((item) => item.id === latestWindowId);
  if (existingMeasurement && measurementId !== latestWindowId) {
    return existingMeasurement;
  }

  const candidateIds = [`${latestWindow.measurement_id || ''}`, latestWindowId].filter(Boolean);
  if (candidateIds.length && candidateIds.indexOf(measurementId) < 0) {
    return null;
  }

  const latestWindowKey = hasValue(latestWindow.measurement_id) ? `${latestWindow.measurement_id}` : measurementId;
  const pendingWindow = runtime.pendingActiveWindows[latestWindowKey] || runtime.pendingActiveWindows[measurementId] || null;
  const pendingRealtime = runtime.pendingActiveRealtimeMeasurements[latestWindowKey] || runtime.pendingActiveRealtimeMeasurements[measurementId] || null;
  const partialProcessedPoints = pendingWindow && Array.isArray(pendingWindow.processedPoints)
    ? pendingWindow.processedPoints.filter((value) => value !== null && value !== undefined)
    : [];
  const partialBeatTsMs = pendingWindow && Array.isArray(pendingWindow.beatTsMs)
    ? pendingWindow.beatTsMs.filter((value) => value !== null && value !== undefined)
    : [];
  const partialRrIntervalsMs = pendingWindow && Array.isArray(pendingWindow.rrIntervalsMs)
    ? pendingWindow.rrIntervalsMs.filter((value) => value !== null && value !== undefined)
    : (Array.isArray(latestWindow.rr_intervals_ms) ? latestWindow.rr_intervals_ms : []);

  appendActiveMeasurement({
    ...latestWindow,
    processed_points: partialProcessedPoints,
    beat_ts_ms: partialBeatTsMs,
    rr_intervals_ms: partialRrIntervalsMs
  }, {
    isPartial: !Number(latestWindow.realtime_complete ? 1 : 0),
    receivedFragmentCount: Number(latestWindow.received_fragment_count || 0),
    fragmentTotal: Number(latestWindow.fragment_total || 0),
    fullWavePoints: pendingRealtime && Array.isArray(pendingRealtime.wavePoints) ? pendingRealtime.wavePoints : runtime.state.heartWavePoints,
    fullBeatMarkerPoints: pendingRealtime && Array.isArray(pendingRealtime.beatMarkerPoints) ? pendingRealtime.beatMarkerPoints : runtime.state.heartBeatMarkerPoints,
    realtimeComplete: Boolean(latestWindow.realtime_complete),
    realtimeDurationMs: Number(latestWindow.realtime_duration_ms || 0),
    realtimePointTarget: pendingRealtime && Number(pendingRealtime.sampleIntervalMs || 0) > 0
      ? Math.round(60000 / Number(pendingRealtime.sampleIntervalMs || 0))
      : 0,
    realtimeHeartRateBpm: Number(runtime.state.currentActiveHeartBpm || latestWindow.realtime_heart_rate_bpm || 0),
    realtimeBeatCount: Number(runtime.state.currentActiveBeatCount || latestWindow.realtime_beat_count || 0),
    realtimeSampleIntervalMs: pendingRealtime ? Number(pendingRealtime.sampleIntervalMs || 0) : 0
  });

  return (runtime.state.activeMeasurements || []).find((item) => item.id === measurementId)
    || (runtime.state.activeMeasurements || []).find((item) => item.id === latestWindowId)
    || null;
}

function buildCurrentActiveMeasurementFromLatestWindow() {
  const latestWindow = runtime.state.latestActiveWindow;
  if (!latestWindow) {
    return null;
  }

  const latestWindowId = resolveActiveMeasurementId(latestWindow, 'latest');
  const latestWindowKey = hasValue(latestWindow.measurement_id) ? `${latestWindow.measurement_id}` : latestWindowId;
  const pendingWindow = runtime.pendingActiveWindows[latestWindowKey] || runtime.pendingActiveWindows[latestWindowId] || null;
  const pendingRealtime = runtime.pendingActiveRealtimeMeasurements[latestWindowKey] || runtime.pendingActiveRealtimeMeasurements[latestWindowId] || null;
  const partialProcessedPoints = pendingWindow && Array.isArray(pendingWindow.processedPoints)
    ? pendingWindow.processedPoints.filter((value) => value !== null && value !== undefined)
    : [];
  const partialBeatTsMs = pendingWindow && Array.isArray(pendingWindow.beatTsMs)
    ? pendingWindow.beatTsMs.filter((value) => value !== null && value !== undefined)
    : [];
  const partialRrIntervalsMs = pendingWindow && Array.isArray(pendingWindow.rrIntervalsMs)
    ? pendingWindow.rrIntervalsMs.filter((value) => value !== null && value !== undefined)
    : (Array.isArray(latestWindow.rr_intervals_ms) ? latestWindow.rr_intervals_ms : []);

  return buildActiveMeasurementRecord({
    ...latestWindow,
    processed_points: partialProcessedPoints,
    beat_ts_ms: partialBeatTsMs,
    rr_intervals_ms: partialRrIntervalsMs
  }, null, {
    isPartial: !Boolean(latestWindow.realtime_complete),
    receivedFragmentCount: Number(latestWindow.received_fragment_count || 0),
    fragmentTotal: Number(latestWindow.fragment_total || 0),
    fullWavePoints: pendingRealtime && Array.isArray(pendingRealtime.wavePoints) ? pendingRealtime.wavePoints : runtime.state.heartWavePoints,
    fullBeatMarkerPoints: pendingRealtime && Array.isArray(pendingRealtime.beatMarkerPoints) ? pendingRealtime.beatMarkerPoints : runtime.state.heartBeatMarkerPoints,
    realtimeComplete: Boolean(latestWindow.realtime_complete),
    realtimeDurationMs: Number(latestWindow.realtime_duration_ms || 0),
    realtimePointTarget: pendingRealtime && Number(pendingRealtime.sampleIntervalMs || 0) > 0
      ? Math.round(60000 / Number(pendingRealtime.sampleIntervalMs || 0))
      : 0,
    realtimeHeartRateBpm: Number(runtime.state.currentActiveHeartBpm || latestWindow.realtime_heart_rate_bpm || latestWindow.heart_rate_bpm || 0),
    realtimeBeatCount: Number(runtime.state.currentActiveBeatCount || latestWindow.realtime_beat_count || latestWindow.beat_count || 0),
    realtimeSampleIntervalMs: pendingRealtime ? Number(pendingRealtime.sampleIntervalMs || 0) : 0
  });
}

function updateActiveMeasurementReport(id, patch) {
  const measurements = runtime.state.activeMeasurements.slice();
  const index = measurements.findIndex((item) => item.id === id);
  if (index < 0) {
    return null;
  }

  measurements[index] = {
    ...measurements[index],
    ...patch
  };
  runtime.state.activeMeasurements = measurements;
  persistState();
  emitState();
  return measurements[index];
}

async function requestActiveMeasurementInsight(id, options = {}) {
  const measurement = (runtime.state.activeMeasurements || []).find((item) => item.id === id)
    || ensureActiveMeasurementFromLatestWindow(id)
    || runtime.state.activeMeasurements[0];
  if (!measurement) {
    return { ok: false, reason: 'missing-measurement' };
  }
  if (!measurement.archiveReady) {
    return {
      ok: false,
      reason: 'measurement-not-ready',
      measurement
    };
  }

  const force = Boolean(options.force);
  if (!force && measurement.generatedReportSource === 'running') {
    return { ok: false, reason: 'already-running', measurement };
  }
  if (!force && measurement.generatedReportUpdatedAt && measurement.generatedReportText) {
    return { ok: true, reason: 'already-generated', measurement };
  }

  updateActiveMeasurementReport(measurement.id, {
    generatedReportSource: 'running',
    generatedReportError: ''
  });
  const prompt = buildActiveMeasurementPrompt(measurement);

  if (!wx.cloud || typeof wx.cloud.callFunction !== 'function') {
    const failureReason = 'wx.cloud unavailable';
    const updated = updateActiveMeasurementReport(measurement.id, {
      generatedReportText: buildLocalActiveMeasurementFallbackText(measurement, failureReason),
      generatedReportSource: 'local-fallback-no-cloud',
      generatedReportError: failureReason,
      generatedReportUpdatedAt: new Date().toLocaleString()
    });
    pushDebugLog(`主动报告改用本地兜底: ${failureReason}`);
    return {
      ok: true,
      degraded: true,
      measurement: updated,
      reason: 'no-cloud'
    };
  }

  try {
    const result = await wx.cloud.callFunction({
      name: 'health_insight',
      data: {
        prompt,
        report_kind: 'active_report'
      }
    });
    const cloudResult = result && result.result ? result.result : {};
    const updated = updateActiveMeasurementReport(measurement.id, {
      generatedReportText: cloudResult.reply_text || '云端暂未返回报告，请稍后重试。',
      generatedReportSource: cloudResult.source || 'unknown',
      generatedReportError: cloudResult.error_message || '',
      generatedReportUpdatedAt: new Date().toLocaleString()
    });
    if (cloudResult.error_message) {
      pushDebugLog(`主动报告云端回退: ${cloudResult.source || 'unknown'} / ${cloudResult.error_message}`);
    }
    return {
      ok: true,
      degraded: Boolean(cloudResult.source && `${cloudResult.source}`.indexOf('fallback') === 0),
      measurement: updated,
      result: cloudResult
    };
  } catch (error) {
    const failureReason = error && error.message ? error.message : 'unknown';
    const updated = updateActiveMeasurementReport(measurement.id, {
      generatedReportText: buildLocalActiveMeasurementFallbackText(measurement, failureReason),
      generatedReportSource: 'local-fallback-client-error',
      generatedReportError: failureReason,
      generatedReportUpdatedAt: new Date().toLocaleString()
    });
    pushDebugLog(`主动报告调用失败: ${failureReason}`);
    return {
      ok: true,
      degraded: true,
      measurement: updated,
      reason: 'call-failed',
      error
    };
  }
}

function requestOverallInsightRefresh() {
  return refreshOverallInsight(true);
}

module.exports = {
  init,
  subscribe,
  getState,
  buildFallbackDailyAnalysis,
  getOverallSummary,
  ensureActiveMeasurementFromLatestWindow,
  buildCurrentActiveMeasurementFromLatestWindow,
  updateActiveMeasurementReport,
  requestActiveMeasurementInsight,
  requestOverallInsightRefresh,
  startBreathGuide,
  startActiveTest,
  startScanAndConnect,
  disconnect,
  clearCachedData
};