const holdBleRuntime = require('../../utils/hold-ble-runtime');

Page({
  data: {
    adapterStatus: '未初始化',
    connectionStatus: '未连接',
    deviceName: '',
    scanning: false,
    lastEventTime: '',
    lastPacketType: '',
    lastEventRaw: '',
    currentDeviceState: '',
    currentGuideText: '',
    currentPhaseText: '',
    currentRespBpm: '',
    currentHeartBpm: '',
    currentMotionLevel: '',
    currentBeatCount: 0,
    respWaveSummary: '',
    heartWaveSummary: '',
    debugLogs: [],
    chartWidth: 320,
    chartHeight: 180
  },

  renderIntervalMs: 180,

  onLoad() {
    this.unsubscribeRuntime = holdBleRuntime.subscribe((state) => {
      this.pendingRuntimeState = state;
      this.scheduleStateFlush();
    });

    const systemInfo = wx.getSystemInfoSync();
    this.setData({
      chartWidth: Math.max(280, Math.floor(systemInfo.windowWidth - 56)),
      chartHeight: 180
    });
  },

  onReady() {
    this.chartDrawPending = false;
    this.drawWaveCharts();
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

  scheduleStateFlush() {
    if (this.renderTimer) {
      return;
    }

    this.renderTimer = setTimeout(() => {
      this.renderTimer = null;
      if (this.pendingRuntimeState) {
        this.applyRuntimeState(this.pendingRuntimeState);
      }
    }, this.renderIntervalMs);
  },

  handleScanAndConnect() {
    holdBleRuntime.startScanAndConnect();
  },

  applyRuntimeState(state) {
    this.respWavePoints = state.respWavePoints || [];
    this.respBeatMarkerPoints = state.respBeatMarkerPoints || [];
    this.heartWavePoints = state.heartWavePoints || [];
    this.heartBeatMarkerPoints = state.heartBeatMarkerPoints || [];
    this.setData({
      adapterStatus: state.adapterStatus,
      connectionStatus: state.connectionStatus,
      deviceName: state.deviceName,
      scanning: state.scanning,
      lastEventTime: state.lastEventTime,
      lastPacketType: state.lastPacketType,
      lastEventRaw: (state.lastEventRaw || '').slice(0, 220),
      currentDeviceState: state.currentDeviceState,
      currentGuideText: state.currentGuideText,
      currentPhaseText: state.currentPhaseText,
      currentRespBpm: state.currentRespBpm,
      currentHeartBpm: state.currentHeartBpm,
      currentMotionLevel: state.currentMotionLevel,
      currentBeatCount: state.currentBeatCount,
      respWaveSummary: state.respWaveSummary,
      heartWaveSummary: state.heartWaveSummary,
      debugLogs: (state.debugLogs || []).slice(0, 8)
    });
    this.scheduleChartDraw();
  },

  scheduleChartDraw() {
    if (this.chartDrawPending) {
      return;
    }

    this.chartDrawPending = true;
    setTimeout(() => {
      this.chartDrawPending = false;
      this.drawWaveCharts();
    }, this.renderIntervalMs);
  },

  drawWaveCharts() {
    this.drawDualWaveChart('respWaveCanvas', this.respWavePoints, this.respBeatMarkerPoints, {
      primaryStrokeStyle: '#D9A441',
      secondaryStrokeStyle: '#C44B1D'
    });

    this.drawHeartWaveChart();
  },

  drawDualWaveChart(canvasId, primaryPoints, secondaryPoints, options) {
    const ctx = wx.createCanvasContext(canvasId, this);
    const width = this.data.chartWidth;
    const height = this.data.chartHeight;
    const padding = 16;
    const innerWidth = width - padding * 2;
    const innerHeight = height - padding * 2;
    const firstSeries = primaryPoints || [];
    const secondSeries = secondaryPoints || [];
    const pointCount = Math.max(firstSeries.length, secondSeries.length);

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
    firstSeries.concat(secondSeries).forEach((point, index) => {
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

    drawSeries(firstSeries, options.primaryStrokeStyle, 2);
    drawSeries(secondSeries, options.secondaryStrokeStyle, 1.5);
    ctx.draw();
  },

  drawHeartWaveChart() {
    const ctx = wx.createCanvasContext('heartWaveCanvas', this);
    const width = this.data.chartWidth;
    const height = this.data.chartHeight;
    const padding = 16;
    const innerWidth = width - padding * 2;
    const innerHeight = height - padding * 2;
    const filteredPoints = this.heartWavePoints || [];
    const beatMarkerPoints = this.heartBeatMarkerPoints || [];
    const pointCount = Math.max(filteredPoints.length, beatMarkerPoints.length);

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
    const mergedPoints = filteredPoints.concat(beatMarkerPoints);
    mergedPoints.forEach((point, index) => {
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

    const drawSeries = (points, strokeStyle, lineWidth) => {
      if (!points || points.length < 2) {
        return;
      }

      ctx.beginPath();
      points.forEach((point, index) => {
        const x = padding + (innerWidth * index) / (points.length - 1);
        const ratio = (point - minValue) / (maxValue - minValue);
        const y = padding + innerHeight - ratio * innerHeight;
        if (index === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      });
      ctx.setStrokeStyle(strokeStyle);
      ctx.setLineWidth(lineWidth);
      ctx.stroke();
    };

    drawSeries(filteredPoints, '#111111', 2);
    drawSeries(beatMarkerPoints, '#FF2A8B', 1.5);
    ctx.draw();
  },

  clearDebugPanels() {
    holdBleRuntime.clearCachedData();
  },

  disconnectDevice() {
    holdBleRuntime.disconnect();
  }
});