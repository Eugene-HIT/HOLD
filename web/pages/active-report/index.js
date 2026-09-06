const holdBleRuntime = require('../../utils/hold-ble-runtime');

const ACTIVE_TEST_STATE = 'FINGER_PPG_ACTIVE_TEST';

function sampleSeries(series, targetCount) {
  if (!Array.isArray(series) || !series.length) {
    return [];
  }

  if (series.length <= targetCount) {
    return series.slice();
  }

  const sampled = [];
  const lastIndex = series.length - 1;
  for (let index = 0; index < targetCount; index += 1) {
    const sourceIndex = Math.round((lastIndex * index) / Math.max(targetCount - 1, 1));
    sampled.push(Number(series[sourceIndex] || 0));
  }
  return sampled;
}

function buildBeatTimelineMsFromMarkers(beatMarkerPoints, durationMs) {
  const points = Array.isArray(beatMarkerPoints) ? beatMarkerPoints : [];
  if (!points.length) {
    return [];
  }

  const timeline = [];
  const safeDurationMs = Math.max(0, Number(durationMs || 0));
  let previousMarked = false;
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

function buildBeatMarkerSeriesFromTimelineMs(wavePoints, beatTimelineMs, durationMs) {
  const safeWavePoints = Array.isArray(wavePoints) ? wavePoints : [];
  const safeTimeline = Array.isArray(beatTimelineMs) ? beatTimelineMs : [];
  const markers = new Array(safeWavePoints.length).fill(0);
  if (!markers.length) {
    return markers;
  }

  const safeDurationMs = Math.max(0, Number(durationMs || 0));
  safeTimeline.forEach((offsetMs) => {
    let index = 0;
    if (safeDurationMs > 0) {
      index = Math.round((Number(offsetMs || 0) / safeDurationMs) * (markers.length - 1));
    }
    if (index < 0) {
      index = 0;
    }
    if (index >= markers.length) {
      index = markers.length - 1;
    }
    markers[index] = safeWavePoints[index] || 1;
  });
  return markers;
}

function deriveBeatTimelineMs(report) {
  if (Array.isArray(report && report.beatTimelineMs) && report.beatTimelineMs.length) {
    return report.beatTimelineMs.slice();
  }
  if (Array.isArray(report && report.beat_timeline_ms) && report.beat_timeline_ms.length) {
    return report.beat_timeline_ms.slice();
  }
  if (Array.isArray(report && report.rrIntervalsMs) && report.rrIntervalsMs.length) {
    return buildBeatTimelineMsFromIntervals(report.rrIntervalsMs);
  }
  if (Array.isArray(report && report.rr_intervals_ms) && report.rr_intervals_ms.length) {
    return buildBeatTimelineMsFromIntervals(report.rr_intervals_ms);
  }

  const fullBeatMarkerPoints = Array.isArray(report && report.fullPpgBeatMarkerPoints)
    ? report.fullPpgBeatMarkerPoints
    : [];
  const displayBeatMarkerPoints = Array.isArray(report && report.ppgBeatMarkerPoints)
    ? report.ppgBeatMarkerPoints
    : [];
  const beatMarkerPoints = fullBeatMarkerPoints.length ? fullBeatMarkerPoints : displayBeatMarkerPoints;
  const durationMs = Number(report && (
    report.realtimeDurationMs
    || (Number(report.sampleEndTsMs || 0) - Number(report.sampleStartTsMs || 0))
  ) || 0);
  return buildBeatTimelineMsFromMarkers(beatMarkerPoints, durationMs);
}

function deriveRrIntervalsMs(report, beatTimelineMs) {
  if (Array.isArray(report && report.rrIntervalsMs) && report.rrIntervalsMs.length) {
    return report.rrIntervalsMs.slice();
  }
  if (Array.isArray(report && report.rr_intervals_ms) && report.rr_intervals_ms.length) {
    return report.rr_intervals_ms.slice();
  }
  return buildRrIntervalsMs(beatTimelineMs);
}

function computeActiveAnalysisStats(report) {
  const beatTimelineMs = deriveBeatTimelineMs(report);
  const rrIntervalsMs = deriveRrIntervalsMs(report, beatTimelineMs)
    .map((value) => Math.max(0, Number(value || 0)))
    .filter((value) => value > 0);
  const effectiveBeatCount = rrIntervalsMs.length > 0
    ? rrIntervalsMs.length + 1
    : Math.max(0, Number(report && report.fullBeatCount || 0));
  const avgRrMs = rrIntervalsMs.length > 0
    ? rrIntervalsMs.reduce((sum, value) => sum + value, 0) / rrIntervalsMs.length
    : 0;
  const variance = rrIntervalsMs.length > 0
    ? rrIntervalsMs.reduce((sum, value) => sum + ((value - avgRrMs) * (value - avgRrMs)), 0) / rrIntervalsMs.length
    : 0;
  const sdnnMs = variance > 0 ? Math.round(Math.sqrt(variance)) : 0;
  const cv = avgRrMs > 0 ? Math.sqrt(variance) / avgRrMs : 0;
  const metricHeartRate = Number(report && report.realtimeHeartRateBpm
    ? report.realtimeHeartRateBpm
    : (report && Array.isArray(report.metrics) && report.metrics[0] ? report.metrics[0].value : 0));
  const avgHeartRateBpm = avgRrMs > 0 ? Math.round(60000 / avgRrMs) : Math.max(0, metricHeartRate);

  let rhythmLabel = '基本平稳';
  if (cv >= 0.18 || sdnnMs >= 180) {
    rhythmLabel = '波动偏大';
  } else if (cv >= 0.12 || sdnnMs >= 110) {
    rhythmLabel = '有些起伏';
  } else if (cv <= 0.08 && sdnnMs <= 70) {
    rhythmLabel = '比较平稳';
  }

  let speedLabel = '不快';
  if (avgHeartRateBpm >= 95) {
    speedLabel = '偏快';
  } else if (avgHeartRateBpm >= 85) {
    speedLabel = '略快';
  }

  let anxietyLabel = '更偏向没有明显焦虑激活';
  if (avgHeartRateBpm >= 95 || (avgHeartRateBpm >= 88 && cv >= 0.12) || cv >= 0.2) {
    anxietyLabel = '更偏向明显紧张或焦虑激活';
  } else if (avgHeartRateBpm >= 82 || cv >= 0.12) {
    anxietyLabel = '更偏向轻度紧张';
  }

  return {
    beatTimelineMs,
    rrIntervalsMs,
    effectiveBeatCount,
    avgHeartRateBpm,
    sdnnMs,
    cv,
    rhythmLabel,
    speedLabel,
    anxietyLabel
  };
}

function buildCompactActiveReportText(report) {
  const stats = computeActiveAnalysisStats(report);
  return [
    `结论：本次有效片段${stats.anxietyLabel}。`,
    `节律：当前有效片段心率${stats.rhythmLabel}。`,
    `心率：平均约 ${stats.avgHeartRateBpm || '--'} bpm，整体${stats.speedLabel}。`,
    `焦虑倾向：${stats.anxietyLabel}。`
  ].join('\n');
}

function shouldCompactActiveReportText(text) {
  const normalized = `${text || ''}`.trim();
  if (!normalized) {
    return true;
  }
  if (normalized.length > 180) {
    return true;
  }
  return /无法|不可靠|数据质量|置信度|干扰|中断|不足|复测|伪影|空白|低置信/.test(normalized);
}

function buildActiveReportPrompt(report) {
  const stats = computeActiveAnalysisStats(report);

  return [
    '你是一次性指部 PPG 主动检测的身心状态解读助手。',
    '你的任务只有一个：只分析当前有效RR片段里的节律和平稳度，判断这次结果更偏平稳还是更偏紧张。',
    '要求：',
    '1. 不使用医学诊断口吻。',
    '2. 只输出4句短句，每句单独一行，总长度控制在120字以内。',
    '3. 第1句必须以“结论：”开头，直接写更偏平稳、轻度紧张或明显紧张。',
    '4. 第2句必须以“节律：”开头，只说当前有效片段是平稳、略有起伏还是波动偏大。',
    '5. 第3句必须以“心率：”开头，只说平均心率大概多少、整体不快/略快/偏快。',
    '6. 第4句必须以“焦虑倾向：”开头，只给偏向性结论。',
    '7. 不要出现“无法判断、数据质量、置信度、干扰因素、复测建议、信号中断、采集不足”这些说法。',
    '8. 不要解释采集过程，只基于有效RR片段直接给结论。',
    `检测记录: ${JSON.stringify({
      id: report && report.id ? report.id : '',
      startedAt: report && report.startedAt ? report.startedAt : '',
      durationLabel: report && report.durationLabel ? report.durationLabel : '',
      resultTag: report && report.resultTag ? report.resultTag : '',
      metrics: report && report.metrics ? report.metrics : [],
      fullBeatCount: report && report.fullBeatCount ? report.fullBeatCount : 0,
      realtimeDurationMs: report && report.realtimeDurationMs ? report.realtimeDurationMs : 0,
      archiveMode: report && report.archiveMode ? report.archiveMode : '',
      effectiveBeatCount: stats.effectiveBeatCount,
      effectiveAvgHeartRateBpm: stats.avgHeartRateBpm,
      effectiveRhythm: stats.rhythmLabel
    })}`,
    `有效片段概况: 有效beat约 ${stats.effectiveBeatCount} 个, RR间期 ${stats.rrIntervalsMs.length} 个`,
    `1分钟总beat数: ${report && report.fullBeatCount ? report.fullBeatCount : 0}`,
    `RR间期毫秒序列: ${JSON.stringify(stats.rrIntervalsMs)}`,
    `beat时间点(相对开始毫秒，仅作辅助展示): ${JSON.stringify(stats.beatTimelineMs)}`
  ].join('\n');
}

function resolveFallbackReportId(latestActiveWindow) {
  if (!latestActiveWindow) {
    return 'preview';
  }

  if (latestActiveWindow.session_id !== null && latestActiveWindow.session_id !== undefined && latestActiveWindow.session_id !== '' &&
      latestActiveWindow.measurement_id !== null && latestActiveWindow.measurement_id !== undefined && latestActiveWindow.measurement_id !== '') {
    return `session-${latestActiveWindow.session_id}-measurement-${latestActiveWindow.measurement_id}`;
  }

  if (latestActiveWindow.measurement_id !== null && latestActiveWindow.measurement_id !== undefined && latestActiveWindow.measurement_id !== '') {
    return `${latestActiveWindow.measurement_id}`;
  }

  return `window-${latestActiveWindow.sample_start_ts_ms || 0}-${latestActiveWindow.sample_end_ts_ms || 0}`;
}

function buildFallbackReport(latestActiveWindow, state) {
  if (!latestActiveWindow && !state) {
    return null;
  }

  const currentHeartBpm = Number(state && state.currentActiveHeartBpm ? state.currentActiveHeartBpm : 0);
  const currentBeatCount = Number(state && state.currentActiveBeatCount ? state.currentActiveBeatCount : 0);
  const windowHeartBpm = latestActiveWindow
    ? Number(latestActiveWindow.realtime_heart_rate_bpm || latestActiveWindow.heart_rate_bpm || 0)
    : 0;
  const windowBeatCount = latestActiveWindow
    ? Number(latestActiveWindow.realtime_beat_count || latestActiveWindow.beat_count || 0)
    : 0;
  const processedPointCount = latestActiveWindow ? Number(latestActiveWindow.processed_point_count || 0) : 0;
  const realtimePointCount = latestActiveWindow ? Number(latestActiveWindow.realtime_point_count || 0) : 0;
  const realtimeDurationMs = latestActiveWindow ? Number(latestActiveWindow.realtime_duration_ms || 0) : 0;
  const realtimeComplete = !!(latestActiveWindow && latestActiveWindow.realtime_complete);
  const fullPpgWavePoints = state && Array.isArray(state.heartWavePoints) ? state.heartWavePoints.slice() : [];
  const directRrIntervalsMs = Array.isArray(latestActiveWindow && latestActiveWindow.rr_intervals_ms)
    && latestActiveWindow.rr_intervals_ms.length
    ? latestActiveWindow.rr_intervals_ms.slice()
    : [];
  const beatTimelineMs = Array.isArray(latestActiveWindow && latestActiveWindow.beat_timeline_ms)
    && latestActiveWindow.beat_timeline_ms.length
    ? latestActiveWindow.beat_timeline_ms.slice()
    : (directRrIntervalsMs.length
      ? buildBeatTimelineMsFromIntervals(directRrIntervalsMs)
      : buildBeatTimelineMsFromMarkers(
        state && Array.isArray(state.heartBeatMarkerPoints) ? state.heartBeatMarkerPoints : [],
        realtimeDurationMs > 0
          ? realtimeDurationMs
          : (latestActiveWindow ? Number(latestActiveWindow.sample_end_ts_ms || 0) - Number(latestActiveWindow.sample_start_ts_ms || 0) : 0)
      ));
  const rrIntervalsMs = directRrIntervalsMs.length
    ? directRrIntervalsMs
    : buildRrIntervalsMs(beatTimelineMs);
  const fullPpgBeatMarkerPoints = state && Array.isArray(state.heartBeatMarkerPoints)
    ? state.heartBeatMarkerPoints.slice()
    : buildBeatMarkerSeriesFromTimelineMs(
      fullPpgWavePoints,
      beatTimelineMs,
      realtimeDurationMs > 0
        ? realtimeDurationMs
        : (latestActiveWindow ? Number(latestActiveWindow.sample_end_ts_ms || 0) - Number(latestActiveWindow.sample_start_ts_ms || 0) : 0)
    );
  const ppgWavePoints = sampleSeries(fullPpgWavePoints, 180);
  const ppgBeatMarkerPoints = sampleSeries(fullPpgBeatMarkerPoints, 180);
  const fragmentText = latestActiveWindow
    ? `${Number(latestActiveWindow.received_fragment_count || 0)}/${Number(latestActiveWindow.fragment_total || 0)}`
    : '--';

  return {
    id: resolveFallbackReportId(latestActiveWindow),
    title: '指部 PPG 曲线预览',
    resultTag: '最近缓存',
    startedAt: '尚未归档完整 60 秒报告',
    durationLabel: '',
    metrics: [
      {
        label: '最近缓存心率',
        value: `${currentHeartBpm > 0 ? currentHeartBpm : (windowHeartBpm > 0 ? windowHeartBpm : '--')}`,
        unit: ' bpm'
      },
      {
        label: '最近缓存 beat 数',
        value: `${currentBeatCount > 0 ? currentBeatCount : (windowBeatCount > 0 ? windowBeatCount : '--')}`,
        unit: ''
      }
    ],
    summary: latestActiveWindow
      ? (realtimeComplete
        ? `已拿到最近一次主动检测的完整实时累计，当前实时点数 ${realtimePointCount}，窗口分片 ${fragmentText}。`
        : `已收到最近一次主动检测窗口，实时累计 ${realtimePointCount} 点，窗口处理点数 ${processedPointCount}，分片接收 ${fragmentText}。`)
      : '当前还没有归档完成的指部主动检测报告，下面先显示最近心率曲线窗口。',
    briefAnalysis: latestActiveWindow
      ? (realtimeComplete
        ? '当前页面已经拿到一条完整的 60 秒实时累计记录。即使窗口分片还没收完，也会优先使用这条实时累计来显示和生成报告。'
        : '当前页面先显示最近缓存或实时心率窗口。若实时累计达到 60 秒，会优先按实时累计结果生成报告。')
      : '当前页面没有找到完整主动检测记录，因此只能显示实时心率窗口预览。',
    briefAdvice: realtimeComplete
      ? `当前实时累计约 ${Math.round(realtimeDurationMs / 1000)} 秒，可直接尝试生成正式报告。`
      : '如果你刚做完一次 60 秒检测但这里仍未出现正式报告，优先检查该次检测是否完整结束以及蓝牙传输是否中断。',
    processedPointCount,
    fullProcessedPointCount: realtimePointCount || processedPointCount,
    fullBeatCount: currentBeatCount || windowBeatCount || rrIntervalsMs.length || beatTimelineMs.length,
    sampleStartTsMs: latestActiveWindow ? Number(latestActiveWindow.sample_start_ts_ms || 0) : 0,
    sampleEndTsMs: latestActiveWindow ? Number(latestActiveWindow.sample_end_ts_ms || 0) : 0,
    fullPpgWavePoints,
    fullPpgBeatMarkerPoints,
    ppgWavePoints,
    ppgBeatMarkerPoints,
    beatTimelineMs,
    rrIntervalsMs,
    archiveReady: realtimeComplete,
    generatedReportText: '',
    generatedReportSource: '',
    generatedReportError: '',
    generatedReportUpdatedAt: '',
    reportSections: [],
    isPreview: true
  };
}

function buildIdleReport() {
  return {
    id: 'idle-preview',
    title: '指部 PPG 曲线预览',
    resultTag: '等待检测',
    startedAt: '开始一次新的 60 秒检测后，这里会开始绘图',
    durationLabel: '',
    metrics: [
      {
        label: '最近缓存心率',
        value: '--',
        unit: ' bpm'
      },
      {
        label: '最近缓存 beat 数',
        value: '--',
        unit: ''
      }
    ],
    summary: '当前还没有本次可查看的指部检测数据。页面会先固定显示绘图窗口，等你开始新的 60 秒主动检测后，再在这里实时画出波形与跳点。',
    briefAnalysis: '在新的 60 秒主动检测真正开始之前，这里不会提前生成曲线或报告。',
    briefAdvice: '开始检测后保持手指贴合与相对静止，页面会直接使用这次检测的 beat 时间点与 1 分钟总 beat 数供模型分析。',
    processedPointCount: 0,
    fullProcessedPointCount: 0,
    fullBeatCount: 0,
    sampleStartTsMs: 0,
    sampleEndTsMs: 0,
    fullPpgWavePoints: [],
    fullPpgBeatMarkerPoints: [],
    ppgWavePoints: [],
    ppgBeatMarkerPoints: [],
    beatTimelineMs: [],
    rrIntervalsMs: [],
    archiveReady: false,
    generatedReportText: '',
    generatedReportSource: '',
    generatedReportError: '',
    generatedReportUpdatedAt: '',
    reportSections: [],
    isPreview: true
  };
}

Page({
  data: {
    report: null,
    viewReport: null,
    hasStoredReport: false,
    canGenerateReport: false,
    chartWidth: 320,
    chartHeight: 180,
    showWaveChart: true,
    chartStatusText: '开始 60 秒检测后，这里会开始绘图',
    reportStatus: 'idle',
    reportId: ''
  },

  renderIntervalMs: 120,

  onLoad(options) {
    const reportId = options.id || '';
    const systemInfo = wx.getSystemInfoSync();
    this.hasSeenActiveSession = false;
    this.localGeneratedReportPatchById = {};
    this.setData({
      reportId,
      chartWidth: Math.max(280, Math.floor(systemInfo.windowWidth - 56)),
      chartHeight: 180,
      reportFeedback: ''
    });
    this.unsubscribeRuntime = holdBleRuntime.subscribe((state) => {
      if (state.currentDeviceState === ACTIVE_TEST_STATE) {
        this.hasSeenActiveSession = true;
      }

      this.pendingRuntimeState = state;
      this.scheduleStateFlush();
    });
  },

  scheduleStateFlush() {
    if (this.renderTimer) {
      return;
    }

    this.renderTimer = setTimeout(() => {
      this.renderTimer = null;
      if (!this.pendingRuntimeState) {
        return;
      }

      const state = this.pendingRuntimeState;
      const reportId = this.data.reportId || '';
      const allowPreviewFallback = !!reportId || this.hasSeenActiveSession;
      const currentActiveReport = typeof holdBleRuntime.buildCurrentActiveMeasurementFromLatestWindow === 'function'
        ? holdBleRuntime.buildCurrentActiveMeasurementFromLatestWindow()
        : null;
      let report = (state.activeMeasurements || []).find((item) => item.id === reportId) || null;
      let viewReport = currentActiveReport
        || report
        || (allowPreviewFallback ? buildFallbackReport(state.latestActiveWindow, state) : null)
        || buildIdleReport();
      const localPatch = viewReport && this.localGeneratedReportPatchById
        ? this.localGeneratedReportPatchById[viewReport.id]
        : null;
      if (report && localPatch) {
        report = {
          ...report,
          ...localPatch
        };
      }
      if (viewReport && localPatch) {
        viewReport = {
          ...viewReport,
          ...localPatch
        };
      }
      this.currentReport = viewReport;
      const canGenerateReport = !!(viewReport && viewReport.archiveReady);
      const reportSource = report && report.generatedReportSource ? report.generatedReportSource : (viewReport && viewReport.generatedReportSource ? viewReport.generatedReportSource : '');
      const reportError = report && report.generatedReportError ? report.generatedReportError : (viewReport && viewReport.generatedReportError ? viewReport.generatedReportError : '');
      const beatTimelineCount = Array.isArray(viewReport && viewReport.beatTimelineMs) ? viewReport.beatTimelineMs.length : 0;
      const rrIntervalsCount = Array.isArray(viewReport && viewReport.rrIntervalsMs) ? viewReport.rrIntervalsMs.length : 0;
      const displayedBeatCount = Number(viewReport && viewReport.fullBeatCount ? viewReport.fullBeatCount : beatTimelineCount);
      const effectiveBeatCount = rrIntervalsCount > 0 ? rrIntervalsCount + 1 : displayedBeatCount;
      const fullWavePointCount = Array.isArray(viewReport && viewReport.fullPpgWavePoints)
        ? viewReport.fullPpgWavePoints.length
        : (Array.isArray(viewReport && viewReport.ppgWavePoints) ? viewReport.ppgWavePoints.length : 0);
      const fullBeatMarkerCount = Array.isArray(viewReport && viewReport.fullPpgBeatMarkerPoints)
        ? viewReport.fullPpgBeatMarkerPoints.length
        : (Array.isArray(viewReport && viewReport.ppgBeatMarkerPoints) ? viewReport.ppgBeatMarkerPoints.length : 0);
      const isActiveTesting = state.currentDeviceState === ACTIVE_TEST_STATE;
      const hasRenderableWave = fullWavePointCount > 1 || fullBeatMarkerCount > 1;
      const chartStatusText = isActiveTesting
        ? '检测进行中，正在实时绘制当前 60 秒波形'
        : (hasRenderableWave
          ? '当前显示最近一次可用的主动检测曲线与跳点'
          : '开始 60 秒检测后，这里会开始绘图');
      this.setData({
        report: report && viewReport && report.id === viewReport.id ? report : null,
        viewReport,
        hasStoredReport: !!(report && viewReport && report.id === viewReport.id),
        canGenerateReport,
        showWaveChart: true,
        chartStatusText,
        reportStatus: viewReport && viewReport.generatedReportSource === 'running' ? 'running' : 'idle',
        reportFeedback: report && report.generatedReportSource === 'running'
          ? '正在把这次检测数据发送给模型...'
          : this.data.reportFeedback
      });
      this.scheduleChartDraw();
    }, this.renderIntervalMs);
  },

  onReady() {
    this.chartDrawPending = false;
    this.drawCharts();
  },

  onUnload() {
    if (this.renderTimer) {
      clearTimeout(this.renderTimer);
      this.renderTimer = null;
    }
    if (this.chartDrawPending) {
      this.chartDrawPending = false;
    }
    if (this.unsubscribeRuntime) {
      this.unsubscribeRuntime();
      this.unsubscribeRuntime = null;
    }
  },

  scheduleChartDraw() {
    if (this.chartDrawPending) {
      return;
    }

    this.chartDrawPending = true;
    setTimeout(() => {
      this.chartDrawPending = false;
      this.drawCharts();
    }, this.renderIntervalMs);
  },

  sampleSeriesForDisplay(series, maxPoints, preservePeaks) {
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
  },

  buildSlidingWindowSeries(series, visiblePointCount, drawPointCount, preservePeaks) {
    const source = Array.isArray(series) ? series : [];
    if (!source.length) {
      return [];
    }

    const tailWindow = source.slice(-visiblePointCount);
    return this.sampleSeriesForDisplay(tailWindow, drawPointCount, preservePeaks);
  },

  drawCharts() {
    const report = this.currentReport;
    this.drawWaveChart('chestPpgCanvas',
      this.buildSlidingWindowSeries(report ? report.fullPpgWavePoints : [], 240, 240, false),
      this.buildSlidingWindowSeries(report ? report.fullPpgBeatMarkerPoints : [], 240, 240, true), {
      lineColor: '#1A1A1A',
      markerColor: '#FF2A8B'
    });
  },

  drawWaveChart(canvasId, points, markerPoints, palette) {
    const ctx = wx.createCanvasContext(canvasId, this);
    const width = this.data.chartWidth;
    const height = this.data.chartHeight;
    const padding = 16;
    const innerWidth = width - padding * 2;
    const innerHeight = height - padding * 2;
    const linePoints = Array.isArray(points) ? points : [];
    const markers = Array.isArray(markerPoints) ? markerPoints : [];
    const pointCount = Math.max(linePoints.length, markers.length);

    ctx.clearRect(0, 0, width, height);
    ctx.setFillStyle('#F8F3E7');
    ctx.fillRect(0, 0, width, height);
    ctx.setStrokeStyle('rgba(32, 55, 42, 0.08)');
    ctx.setLineWidth(1);
    for (let index = 0; index <= 4; index += 1) {
      const y = padding + (innerHeight / 4) * index;
      ctx.beginPath();
      ctx.moveTo(padding, y);
      ctx.lineTo(width - padding, y);
      ctx.stroke();
    }

    if (pointCount < 2) {
      ctx.draw();
      return;
    }

    let minValue = 0;
    let maxValue = 0;
    linePoints.concat(markers).forEach((point, index) => {
      if (index === 0 || point < minValue) {
        minValue = point;
      }
      if (index === 0 || point > maxValue) {
        maxValue = point;
      }
    });

    if (maxValue === minValue) {
      maxValue += 1;
      minValue -= 1;
    }

    const drawSeries = (series, color, widthPx) => {
      if (!series || series.length < 2) {
        return;
      }

      ctx.beginPath();
      series.forEach((point, index) => {
        const x = padding + (innerWidth * index) / (series.length - 1);
        const ratio = (point - minValue) / (maxValue - minValue);
        const y = padding + innerHeight - ratio * innerHeight;
        if (index === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      });
      ctx.setStrokeStyle(color);
      ctx.setLineWidth(widthPx);
      ctx.stroke();
    };

    drawSeries(linePoints, palette.lineColor, 2);
    drawSeries(markers, palette.markerColor, 1.5);
    ctx.draw();
  },

  async generateReport() {
    let report = this.data.viewReport || this.data.report;
    if (!report || !report.id || this.data.reportStatus === 'running') {
      if (this.data.reportStatus !== 'running') {
        wx.showToast({
          title: '当前还没有可用的主动检测数据',
          icon: 'none',
          duration: 2200
        });
      }
      return;
    }

    if (!this.data.report && report.archiveReady) {
      const ensuredReport = holdBleRuntime.ensureActiveMeasurementFromLatestWindow(report.id);
      if (ensuredReport) {
        report = ensuredReport;
      } else {
        this.setData({
          reportFeedback: `补正式记录失败: id=${report.id || '-'} latest=${holdBleRuntime.getState().latestActiveWindow ? 1 : 0}`,
        });
      }
    }

    if (!report.archiveReady) {
      const feedback = report.receivedFragmentCount || report.fragmentTotal
        ? `这次检测还没形成完整 60 秒记录。当前实时累计 ${report.fullProcessedPointCount || 0} 点，分片 ${report.receivedFragmentCount || 0}/${report.fragmentTotal || 0}。`
        : '这次检测还没形成完整 60 秒记录，请先重新完成一次完整检测。';
      this.setData({ reportFeedback: feedback });
      wx.showToast({
        title: '当前记录还不完整',
        icon: 'none',
        duration: 2200
      });
      return;
    }

    const stats = computeActiveAnalysisStats(report);
    const normalizedBeatTimelineMs = stats.beatTimelineMs;
    const normalizedRrIntervalsMs = stats.rrIntervalsMs;
    const effectiveBeatCount = stats.effectiveBeatCount;
    report = {
      ...report,
      beatTimelineMs: normalizedBeatTimelineMs,
      rrIntervalsMs: normalizedRrIntervalsMs,
      effectiveBeatCount
    };

    this.setData({
      reportStatus: 'running',
      reportFeedback: `正在生成报告，当前使用 ${report.fullProcessedPointCount || 0} 个实时累计点、${report.fullBeatCount || 0} 个总beat、${normalizedRrIntervalsMs.length} 个有效RR。`
    });
    const prompt = buildActiveReportPrompt(report);

    try {
      const result = await wx.cloud.callFunction({
        name: 'health_insight',
        data: {
          prompt,
          report_kind: 'active_report'
        }
      });
      const cloudResult = result && result.result ? result.result : {};
      let generatedReportText = cloudResult.reply_text || '';
      let generatedReportSource = cloudResult.source || 'unknown';
      const generatedReportError = cloudResult.error_message || '';
      if (shouldCompactActiveReportText(generatedReportText)) {
        generatedReportText = buildCompactActiveReportText(report);
        generatedReportSource = cloudResult.reply_text
          ? `${generatedReportSource}-compact`
          : 'local-compact';
      }
      if (!generatedReportText) {
        generatedReportText = buildCompactActiveReportText(report);
      }
      const generatedReportUpdatedAt = new Date().toLocaleString();
      const generatedPatch = {
        generatedReportText,
        generatedReportSource,
        generatedReportError,
        generatedReportUpdatedAt,
        beatTimelineMs: normalizedBeatTimelineMs,
        rrIntervalsMs: normalizedRrIntervalsMs
      };
      this.localGeneratedReportPatchById[report.id] = generatedPatch;

      let persistedReport = this.data.report || holdBleRuntime.ensureActiveMeasurementFromLatestWindow(report.id) || null;
      if (persistedReport && typeof holdBleRuntime.updateActiveMeasurementReport === 'function') {
        persistedReport = holdBleRuntime.updateActiveMeasurementReport(persistedReport.id, generatedPatch) || persistedReport;
      }

      const patchedReport = {
        ...report,
        ...generatedPatch,
        ...(persistedReport || {})
      };

      this.currentReport = patchedReport;
      this.setData({
        report: persistedReport || this.data.report,
        viewReport: patchedReport,
        hasStoredReport: !!persistedReport,
        reportStatus: 'done',
        reportFeedback: generatedReportError
          ? `报告已返回 fallback，原因 ${generatedReportError}`
          : `报告已更新，来源 ${generatedReportSource}。`,
      });
      wx.showToast({
        title: generatedReportError ? '已返回回退报告' : '报告已生成',
        icon: generatedReportError ? 'none' : 'success',
        duration: 2000
      });
    } catch (error) {
      const errorMessage = error && error.message ? error.message : 'unknown';
      this.setData({
        reportStatus: 'idle',
        reportFeedback: `报告生成失败：${errorMessage}`,
      });
      wx.showToast({
        title: '生成失败',
        icon: 'none',
        duration: 2200
      });
    }
  }
});