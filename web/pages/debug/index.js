const holdBleRuntime = require('../../utils/hold-ble-runtime');

function readEnvironmentInfo() {
  let systemInfo = {};
  try {
    systemInfo = wx.getSystemInfoSync() || {};
  } catch (error) {
    systemInfo = {};
  }

  return {
    sdkVersion: systemInfo.SDKVersion || '未知',
    platform: systemInfo.platform || '未知',
    system: systemInfo.system || '未知',
    brand: systemInfo.brand || '未知',
    bluetoothEnabled: systemInfo.bluetoothEnabled === undefined ? '未知' : String(systemInfo.bluetoothEnabled)
  };
}

Page({
  data: {
    adapterStatus: '未初始化',
    connectionStatus: '未连接',
    deviceName: '',
    scanning: false,
    isConnected: false,
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
    currentSignalQuality: 0,
    currentAxisName: '',
    currentCalibrationStep: 0,
    phaseRemainingMs: 0,
    respWaveSummary: '',
    heartWaveSummary: '',
    debugLogs: [],
    debugLogTotal: 0,
    logExpanded: false,
    envInfo: {},
    storageUsageText: '',
    archiveRows: [],
    chartWidth: 320,
    chartHeight: 180
  },

  renderIntervalMs: 180,

  onLoad() {
    const systemInfo = wx.getSystemInfoSync();
    this.setData({
      chartWidth: Math.max(280, Math.floor(systemInfo.windowWidth - 56)),
      chartHeight: 180,
      envInfo: readEnvironmentInfo()
    });
    this.refreshStorageUsage();

    this.unsubscribeRuntime = holdBleRuntime.subscribe((state) => {
      this.pendingRuntimeState = state;
      this.scheduleStateFlush();
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

  applyRuntimeState(state) {
    this.respWavePoints = state.respWavePoints || [];
    this.respBeatMarkerPoints = state.respBeatMarkerPoints || [];
    this.heartWavePoints = state.heartWavePoints || [];
    this.heartBeatMarkerPoints = state.heartBeatMarkerPoints || [];
    const logs = state.debugLogs || [];

    this.setData({
      adapterStatus: state.adapterStatus,
      connectionStatus: state.connectionStatus,
      deviceName: state.deviceName,
      scanning: state.scanning,
      isConnected: state.isConnected,
      lastEventTime: state.lastEventTime,
      lastPacketType: state.lastPacketType,
      lastEventRaw: state.lastEventRaw || '',
      currentDeviceState: state.currentDeviceState,
      currentGuideText: state.currentGuideText,
      currentPhaseText: state.currentPhaseText,
      currentRespBpm: state.currentRespBpm,
      currentHeartBpm: state.currentHeartBpm,
      currentMotionLevel: state.currentMotionLevel,
      currentBeatCount: state.currentBeatCount,
      currentSignalQuality: state.currentSignalQuality || 0,
      currentAxisName: state.currentAxisName,
      currentCalibrationStep: state.currentCalibrationStep || 0,
      phaseRemainingMs: state.phaseRemainingMs || 0,
      respWaveSummary: state.respWaveSummary,
      heartWaveSummary: state.heartWaveSummary,
      debugLogTotal: logs.length,
      debugLogs: this.data.logExpanded ? logs.slice() : logs.slice(0, 8),
      archiveRows: this.buildArchiveRows(state)
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
      primaryStrokeStyle: '#3E7C59',
      secondaryStrokeStyle: '#C98A2E'
    });

    this.drawDualWaveChart('heartWaveCanvas', this.heartWavePoints, this.heartBeatMarkerPoints, {
      primaryStrokeStyle: '#1B2419',
      secondaryStrokeStyle: '#B4472F'
    });
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
    ctx.setFillStyle('#FFFDF7');
    ctx.fillRect(0, 0, width, height);
    ctx.setStrokeStyle('rgba(27, 36, 25, 0.07)');
    ctx.setLineWidth(1);
    for (let index = 0; index <= 4; index += 1) {
      const y = padding + (innerHeight / 4) * index;
      ctx.beginPath();
      ctx.moveTo(padding, y);
      ctx.lineTo(width - padding, y);
      ctx.stroke();
    }

    if (pointCount < 2) {
      ctx.setFillStyle('#B4B4A6');
      ctx.setFontSize(13);
      ctx.fillText('等待数据', padding + 8, height / 2);
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

  refreshStorageUsage() {
    try {
      const info = wx.getStorageInfoSync();
      this.setData({
        storageUsageText: `${info.currentSize || 0} KB / ${info.limitSize || 0} KB · ${(info.keys || []).length} 个 key`
      });
    } catch (error) {
      this.setData({ storageUsageText: '读取失败' });
    }
  },

  buildArchiveRows(state) {
    const measurement = (state.activeMeasurements || [])[0] || null;
    const window = state.latestActiveWindow || null;

    return [
      { label: '归档记录 ID', value: measurement ? String(measurement.id) : '--' },
      { label: '归档模式', value: (measurement && measurement.archiveMode) || '--' },
      { label: '可生成报告', value: measurement && measurement.archiveReady ? '是' : '否' },
      { label: '处理点数', value: `${(measurement && measurement.processedPointCount) || 0}` },
      { label: '完整缓存点数', value: `${(measurement && measurement.fullProcessedPointCount) || 0}` },
      { label: '完整 beat 数', value: `${(measurement && measurement.fullBeatCount) || 0}` },
      { label: '窗口分片', value: `${(measurement && measurement.receivedFragmentCount) || 0} / ${(measurement && measurement.fragmentTotal) || 0}` },
      { label: '最近窗口 ID', value: window ? String(window.window_id || window.measurement_id || '--') : '--' },
      { label: '最近窗口心率', value: window ? `${window.heart_rate_bpm || 0} bpm` : '--' }
    ];
  },

  handleScanAndConnect() {
    holdBleRuntime.startScanAndConnect();
  },

  disconnectDevice() {
    holdBleRuntime.disconnect();
  },

  clearDebugPanels() {
    wx.showModal({
      title: '清空调试窗口',
      content: '只清空当前页的波形与日志展示，不影响已归档的检测记录。确定继续？',
      confirmColor: '#2F5D3A',
      success: (result) => {
        if (!result.confirm) {
          return;
        }
        holdBleRuntime.clearCachedData();
        wx.showToast({ title: '已清空', icon: 'success', duration: 1500 });
      }
    });
  },

  clearAllCachedData() {
    wx.showModal({
      title: '删除全部数据缓存',
      content: '将永久删除本机归档的呼吸记录、主动检测与整体分析，且无法恢复。确定继续？',
      confirmText: '删除',
      confirmColor: '#A4442C',
      success: (result) => {
        if (!result.confirm) {
          return;
        }
        try {
          wx.clearStorageSync();
        } catch (error) {
          console.error('clear storage failed', error);
        }
        holdBleRuntime.clearCachedData();
        this.refreshStorageUsage();
        wx.showToast({ title: '已清空缓存', icon: 'success', duration: 1800 });
      }
    });
  },

  toggleLogExpanded() {
    const next = !this.data.logExpanded;
    const state = holdBleRuntime.getState() || {};
    const logs = state.debugLogs || [];
    this.setData({
      logExpanded: next,
      debugLogs: next ? logs.slice() : logs.slice(0, 8)
    });
  },

  copyRawMessage() {
    const text = this.data.lastEventRaw;
    if (!text) {
      wx.showToast({ title: '暂无原始消息', icon: 'none', duration: 1500 });
      return;
    }

    wx.setClipboardData({
      data: text,
      success: () => {
        wx.showToast({ title: '已复制', icon: 'success', duration: 1500 });
      }
    });
  },

  copyDebugLogs() {
    const logs = this.data.debugLogs || [];
    if (!logs.length) {
      wx.showToast({ title: '暂无日志', icon: 'none', duration: 1500 });
      return;
    }

    wx.setClipboardData({
      data: logs.join('\n'),
      success: () => {
        wx.showToast({ title: '已复制日志', icon: 'success', duration: 1500 });
      }
    });
  },

  startBreathGuide() {
    holdBleRuntime.startBreathGuide()
      .then(() => {
        wx.showToast({ title: '呼吸引导已启动', icon: 'success', duration: 1600 });
      })
      .catch((error) => {
        wx.showToast({
          title: error && error.message === 'bluetooth-not-ready' ? '请先连接设备' : '启动失败',
          icon: 'none',
          duration: 2000
        });
      });
  },

  startActiveTest() {
    holdBleRuntime.startActiveTest({ durationMs: 60000 })
      .then(() => {
        wx.showToast({ title: '已下发检测指令', icon: 'success', duration: 1600 });
      })
      .catch(() => {
        wx.showToast({ title: '指令发送失败', icon: 'none', duration: 2000 });
      });
  },

  goBackHome() {
    wx.switchTab({ url: '/pages/home/index' });
  }
});
