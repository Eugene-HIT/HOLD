const holdBleRuntime = require('../../utils/hold-ble-runtime');

const ACTIVE_TEST_STATE = 'FINGER_PPG_ACTIVE_TEST';

function resolveLatestActiveReportId(latestMeasurement, latestActiveWindow) {
  if (latestMeasurement && latestMeasurement.id) {
    return `${latestMeasurement.id}`;
  }

  if (!latestActiveWindow) {
    return '';
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

Page({
  data: {
    adapterStatus: '未初始化',
    connectionStatus: '未连接',
    isConnected: false,
    deviceName: '',
    currentDeviceState: '',
    currentGuideText: '',
    currentPhaseText: '',
    currentCalibrationStep: 0,
    phaseRemainingMs: 0,
    currentRespBpm: '',
    currentHeartBpm: '',
    currentMotionLevel: '',
    currentBeatCount: 0,
    currentAxisName: '',
    latestPassiveWindowText: '',
    latestActiveWindowText: '',
    debugLogCount: 0,
    activeMeasurements: [],
    dailyAnalyses: [],
    overallSummary: null,
    insightStatus: 'idle',
    chartWidth: 320,
    chartHeight: 180
  },

  renderIntervalMs: 120,

  buildMeasurementPreviewList(measurements) {
    return (Array.isArray(measurements) ? measurements : []).map((item) => ({
      id: item.id,
      title: item.title,
      resultTag: item.resultTag,
      startedAt: item.startedAt,
      durationLabel: item.durationLabel,
      metrics: item.metrics,
      summary: item.summary,
      briefAnalysis: item.briefAnalysis,
      briefAdvice: item.briefAdvice,
      generatedReportText: item.generatedReportText || '',
      generatedReportSource: item.generatedReportSource || '',
      generatedReportError: item.generatedReportError || '',
      generatedReportUpdatedAt: item.generatedReportUpdatedAt || ''
    }));
  },

  onLoad() {
    const systemInfo = wx.getSystemInfoSync();
    this.setData({
      chartWidth: Math.max(280, Math.floor(systemInfo.windowWidth - 56)),
      chartHeight: 180
    });

    this.unsubscribeRuntime = holdBleRuntime.subscribe((state) => {
      this.applyRuntimeState(state);
    });
  },

  onUnload() {
    if (this.renderTimer) {
      clearTimeout(this.renderTimer);
      this.renderTimer = null;
    }
    if (this.unsubscribeRuntime) {
      this.unsubscribeRuntime();
      this.unsubscribeRuntime = null;
    }
  },

  applyRuntimeState(state) {
    const passiveWindow = state.latestPassiveWindow;
    const activeWindow = state.latestActiveWindow;
    const latestMeasurement = (state.activeMeasurements || [])[0] || null;
    this.activeWavePoints = latestMeasurement && Array.isArray(latestMeasurement.ppgWavePoints)
      ? latestMeasurement.ppgWavePoints
      : [];
    this.activeBeatMarkerPoints = latestMeasurement && Array.isArray(latestMeasurement.ppgBeatMarkerPoints)
      ? latestMeasurement.ppgBeatMarkerPoints
      : [];
    this.setData({
      adapterStatus: state.adapterStatus,
      connectionStatus: state.connectionStatus,
      isConnected: state.isConnected,
      deviceName: state.deviceName,
      currentDeviceState: state.currentDeviceState,
      currentGuideText: state.currentGuideText,
      currentPhaseText: state.currentPhaseText,
      currentCalibrationStep: state.currentCalibrationStep || 0,
      phaseRemainingMs: state.phaseRemainingMs || 0,
      currentRespBpm: state.currentRespBpm,
      currentHeartBpm: state.currentHeartBpm,
      currentMotionLevel: state.currentMotionLevel,
      currentBeatCount: state.currentBeatCount,
      currentAxisName: state.currentAxisName,
      latestPassiveWindowText: passiveWindow
        ? `窗口 ${passiveWindow.window_id || 0} / 呼吸 ${passiveWindow.resp_rate_bpm || 0} 次/分`
        : '',
      latestActiveWindowText: activeWindow
        ? `测量 ${activeWindow.measurement_id || 0} / 心率 ${activeWindow.heart_rate_bpm || 0} bpm`
        : '',
      debugLogCount: (state.debugLogs || []).length,
      activeMeasurements: this.buildMeasurementPreviewList(state.activeMeasurements || []),
      dailyAnalyses: state.dailyAnalyses || [],
      overallSummary: state.overallSummary || null,
      insightStatus: state.insightStatus || 'idle'
    });
    this.scheduleChartDraw();
  },

  scheduleChartDraw() {
    if (this.chartDrawPending) {
      return;
    }

    this.chartDrawPending = true;
    this.renderTimer = setTimeout(() => {
      this.chartDrawPending = false;
      this.renderTimer = null;
      this.drawActivePreviewChart();
    }, this.renderIntervalMs);
  },

  drawActivePreviewChart() {
    const ctx = wx.createCanvasContext('homeActivePpgCanvas', this);
    const width = this.data.chartWidth;
    const height = this.data.chartHeight;
    const padding = 16;
    const innerWidth = width - padding * 2;
    const innerHeight = height - padding * 2;
    const points = this.activeWavePoints || [];
    const markers = this.activeBeatMarkerPoints || [];
    const pointCount = Math.max(points.length, markers.length);

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
    points.concat(markers).forEach((point, index) => {
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

    const drawSeries = (series, color, lineWidth) => {
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
      ctx.setLineWidth(lineWidth);
      ctx.stroke();
    };

    drawSeries(points, '#1A1A1A', 2);
    drawSeries(markers, '#FF2A8B', 1.5);
    ctx.draw();
  },

  handleScanAndConnect() {
    holdBleRuntime.startScanAndConnect();
  },

  disconnectDevice() {
    holdBleRuntime.disconnect();
  },

  clearAllCachedData() {
    holdBleRuntime.clearCachedData();
  },

  async startBreathGuide() {
    try {
      await holdBleRuntime.startBreathGuide();
      wx.showToast({
        title: '呼吸引导已启动',
        icon: 'success',
        duration: 1800
      });
    } catch (error) {
      wx.showToast({
        title: error && error.message === 'bluetooth-not-ready' ? '请先连接设备' : '启动失败',
        icon: 'none',
        duration: 2200
      });
    }
  },

  openDebugPage() {
    wx.navigateTo({ url: '/pages/index/index' });
  },

  openDailyAnalysis() {
    wx.navigateTo({ url: '/pages/daily-analysis/index' });
  },

  openOverallAnalysis() {
    wx.navigateTo({ url: '/pages/overall-analysis/index' });
  },

  openLatestReport() {
    const latestMeasurement = (this.data.activeMeasurements || [])[0];
    const runtimeState = holdBleRuntime.getState();
    const latestActiveWindow = runtimeState ? runtimeState.latestActiveWindow : null;
    const reportId = resolveLatestActiveReportId(latestMeasurement, latestActiveWindow);

    wx.navigateTo({
      url: reportId
        ? `/pages/active-report/index?id=${reportId}`
        : '/pages/active-report/index'
    });
  },

  openLatestReportCard() {
    this.openLatestReport();
  },

  refreshOverallInsight() {
    holdBleRuntime.requestOverallInsightRefresh();
  }
});