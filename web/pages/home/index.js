const holdBleRuntime = require('../../utils/hold-ble-runtime');

const BREATH_GUIDE_STATE = 'BREATH_GUIDE_SESSION';
const ACTIVE_TEST_STATE = 'FINGER_PPG_ACTIVE_TEST';
const ACTIVE_TEST_TARGET_SECONDS = 60;

function formatCount(value) {
  return value === 0 || value ? `${value}` : '--';
}

function resolveLatestReportId(latestMeasurement, latestActiveWindow) {
  if (latestMeasurement && latestMeasurement.id) {
    return `${latestMeasurement.id}`;
  }

  if (!latestActiveWindow) {
    return '';
  }

  const sessionId = latestActiveWindow.session_id;
  const measurementId = latestActiveWindow.measurement_id;

  if (sessionId !== null && sessionId !== undefined && sessionId !== '' &&
      measurementId !== null && measurementId !== undefined && measurementId !== '') {
    return `session-${sessionId}-measurement-${measurementId}`;
  }

  if (measurementId !== null && measurementId !== undefined && measurementId !== '') {
    return `${measurementId}`;
  }

  return `window-${latestActiveWindow.sample_start_ts_ms || 0}-${latestActiveWindow.sample_end_ts_ms || 0}`;
}

function buildLatestReportView(measurement) {
  if (!measurement) {
    return null;
  }

  const metrics = Array.isArray(measurement.metrics) ? measurement.metrics : [];
  return {
    id: measurement.id,
    title: measurement.title || '主动检测',
    startedAt: measurement.startedAt || '',
    resultTag: measurement.resultTag || '已完成',
    durationLabel: measurement.durationLabel || '',
    heartRate: metrics.length ? `${metrics[0].value || '--'}${metrics[0].unit || ''}` : '--',
    summary: measurement.summary || ''
  };
}

Page({
  data: {
    isConnected: false,
    connecting: false,
    deviceName: '',
    connectionText: '未连接设备',
    connectionHint: '连接后即可开始呼吸引导与数据查看。',

    respBpm: '--',
    heartBpm: '--',
    hasLiveData: false,
    liveUpdatedAt: '',

    hasGuide: false,
    guideText: '',
    guideMeta: '',
    breathGuideRunning: false,
    canStartBreathGuide: false,

    activeTestRunning: false,
    activeTestStarting: false,
    activeTestElapsed: 0,
    activeTestTarget: ACTIVE_TEST_TARGET_SECONDS,
    activeTestPercent: 0,
    activeTestHeart: '--',
    activeTestBeats: '--',

    hasLatestReport: false,
    latestReport: null,

    chartWidth: 320,
    chartHeight: 110
  },

  renderIntervalMs: 160,

  onLoad() {
    const systemInfo = wx.getSystemInfoSync();
    this.setData({
      chartWidth: Math.max(280, Math.floor(systemInfo.windowWidth - 88)),
      chartHeight: 110
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
    if (this.progressTimer) {
      clearInterval(this.progressTimer);
      this.progressTimer = null;
    }
    if (this.unsubscribeRuntime) {
      this.unsubscribeRuntime();
      this.unsubscribeRuntime = null;
    }
  },

  applyRuntimeState(state) {
    this.respWavePoints = state.respWavePoints || [];
    this.chestPpgWavePoints = state.chestPpgWavePoints || [];

    const isConnected = !!state.isConnected;
    const connecting = !!state.scanning;
    const guideText = state.currentGuideText || '';
    const breathGuideRunning = state.currentDeviceState === BREATH_GUIDE_STATE;
    const calibrationStep = state.currentCalibrationStep || 0;
    const remainingSeconds = Math.max(0, Math.ceil((state.phaseRemainingMs || 0) / 1000));

    const guideMetaParts = [];
    if (calibrationStep) {
      guideMetaParts.push(`步骤 ${calibrationStep}`);
    }
    if (remainingSeconds) {
      guideMetaParts.push(`剩余 ${remainingSeconds} 秒`);
    }

    const latestMeasurement = (state.activeMeasurements || [])[0] || null;

    const activeTestRunning = state.currentDeviceState === ACTIVE_TEST_STATE;
    if (activeTestRunning && !this.activeTestStartedAtTsMs) {
      this.activeTestStartedAtTsMs = Date.now();
    }
    if (!activeTestRunning) {
      this.activeTestStartedAtTsMs = 0;
    }

    const activeTestElapsed = activeTestRunning
      ? Math.min(ACTIVE_TEST_TARGET_SECONDS, Math.max(0, Math.round((Date.now() - this.activeTestStartedAtTsMs) / 1000)))
      : 0;

    this.setData({
      isConnected,
      connecting,
      deviceName: state.deviceName || '',
      connectionText: isConnected ? (state.deviceName || '设备已连接') : (connecting ? '正在搜索设备…' : '未连接设备'),
      connectionHint: isConnected
        ? (breathGuideRunning ? '设备正在引导呼吸训练。' : '设备在线，数据实时同步中。')
        : (connecting ? '请保持设备开机并靠近手机。' : '连接后即可开始呼吸引导与数据查看。'),

      respBpm: formatCount(state.currentRespBpm),
      heartBpm: formatCount(state.currentHeartBpm),
      hasLiveData: !!(state.currentRespBpm || state.currentHeartBpm),
      liveUpdatedAt: state.lastEventTime || '',

      hasGuide: !!guideText,
      guideText,
      guideMeta: guideMetaParts.join(' · '),
      breathGuideRunning,
      canStartBreathGuide: isConnected && !breathGuideRunning,

      activeTestRunning,
      activeTestElapsed,
      activeTestPercent: Math.round((activeTestElapsed / ACTIVE_TEST_TARGET_SECONDS) * 100),
      activeTestHeart: formatCount(state.currentActiveHeartBpm || state.currentHeartBpm),
      activeTestBeats: formatCount(state.currentActiveBeatCount || state.currentBeatCount),

      hasLatestReport: !!latestMeasurement,
      latestReport: buildLatestReportView(latestMeasurement)
    });

    this.latestReportId = resolveLatestReportId(latestMeasurement, state.latestActiveWindow);
    this.ensureProgressTimer(activeTestRunning);
    this.scheduleChartDraw();
  },

  ensureProgressTimer(running) {
    if (running && !this.progressTimer) {
      this.progressTimer = setInterval(() => {
        this.updateActiveTestProgress();
      }, 1000);
      return;
    }

    if (!running && this.progressTimer) {
      clearInterval(this.progressTimer);
      this.progressTimer = null;
    }
  },

  updateActiveTestProgress() {
    if (!this.data.activeTestRunning || !this.activeTestStartedAtTsMs) {
      return;
    }

    const elapsed = Math.min(
      ACTIVE_TEST_TARGET_SECONDS,
      Math.max(0, Math.round((Date.now() - this.activeTestStartedAtTsMs) / 1000))
    );

    if (elapsed === this.data.activeTestElapsed) {
      return;
    }

    this.setData({
      activeTestElapsed: elapsed,
      activeTestPercent: Math.round((elapsed / ACTIVE_TEST_TARGET_SECONDS) * 100)
    });
  },

  scheduleChartDraw() {
    if (this.chartDrawPending) {
      return;
    }

    this.chartDrawPending = true;
    this.renderTimer = setTimeout(() => {
      this.chartDrawPending = false;
      this.renderTimer = null;
      this.drawWaveCharts();
    }, this.renderIntervalMs);
  },

  drawWaveCharts() {
    this.drawSeriesOnCanvas('homeRespCanvas', this.respWavePoints, '#3E7C59');
    this.drawSeriesOnCanvas('homeHeartCanvas', this.chestPpgWavePoints, '#B0583A');
  },

  drawSeriesOnCanvas(canvasId, points, color) {
    const ctx = wx.createCanvasContext(canvasId, this);
    const width = this.data.chartWidth;
    const height = this.data.chartHeight;
    const padding = 12;
    const innerWidth = width - padding * 2;
    const innerHeight = height - padding * 2;
    const series = (points || []).slice(-200);

    ctx.clearRect(0, 0, width, height);

    if (series.length < 2) {
      ctx.setFillStyle('#B4B4A6');
      ctx.setFontSize(12);
      ctx.fillText('等待设备数据…', padding + 4, height / 2);
      ctx.draw();
      return;
    }

    let minValue = series[0];
    let maxValue = series[0];
    series.forEach((point) => {
      if (point < minValue) {
        minValue = point;
      }
      if (point > maxValue) {
        maxValue = point;
      }
    });

    if (maxValue === minValue) {
      maxValue += 1;
      minValue -= 1;
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
    ctx.setLineWidth(2);
    ctx.stroke();
    ctx.draw();
  },

  connectDevice() {
    if (this.data.isConnected || this.data.connecting) {
      return;
    }
    holdBleRuntime.startScanAndConnect();
  },

  async startBreathGuide() {
    if (this.data.breathGuideRunning) {
      wx.showToast({ title: '引导已在进行中', icon: 'none', duration: 1600 });
      return;
    }

    if (!this.data.isConnected) {
      wx.showToast({ title: '请先连接设备', icon: 'none', duration: 1800 });
      return;
    }

    try {
      await holdBleRuntime.startBreathGuide();
      wx.showToast({ title: '呼吸引导已启动', icon: 'success', duration: 1800 });
    } catch (error) {
      wx.showToast({
        title: error && error.message === 'bluetooth-not-ready' ? '请先连接设备' : '启动失败，请重试',
        icon: 'none',
        duration: 2200
      });
    }
  },

  async startActiveTest() {
    if (this.data.activeTestRunning) {
      wx.showToast({ title: '检测进行中', icon: 'none', duration: 1600 });
      return;
    }

    if (!this.data.isConnected) {
      wx.showToast({ title: '请先连接设备', icon: 'none', duration: 1800 });
      return;
    }

    this.setData({ activeTestStarting: true });
    try {
      await holdBleRuntime.startActiveTest({ durationMs: ACTIVE_TEST_TARGET_SECONDS * 1000 });
      wx.showToast({ title: '已下发检测指令', icon: 'success', duration: 1800 });
    } catch (error) {
      wx.showToast({
        title: error && error.message === 'bluetooth-not-ready' ? '请先连接设备' : '指令发送失败，请重试',
        icon: 'none',
        duration: 2200
      });
    } finally {
      this.setData({ activeTestStarting: false });
    }
  },

  openDebugPage() {
    wx.navigateTo({ url: '/pages/debug/index' });
  },

  openLatestReport() {
    wx.navigateTo({
      url: this.latestReportId
        ? `/pages/active-report/index?id=${this.latestReportId}`
        : '/pages/active-report/index'
    });
  }
});
