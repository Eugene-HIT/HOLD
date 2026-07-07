const holdBleRuntime = require('../../utils/hold-ble-runtime');

Page({
  data: {
    dailyAnalyses: [],
    activeIndex: 0,
    activeDay: null,
    chartWidth: 320,
    chartHeight: 180,
    reportStatus: 'idle',
    reportText: '',
    reportUpdatedAt: '',
    reportSource: '',
    reportError: ''
  },

  renderIntervalMs: 120,

  buildDayTabItems(days) {
    return (Array.isArray(days) ? days : []).map((item) => ({
      day: item.day,
      title: item.title
    }));
  },

  buildActiveDayView(day) {
    if (!day) {
      return null;
    }

    return {
      day: day.day,
      title: day.title,
      respirationAvg: day.respirationAvg,
      heartRateAvg: day.heartRateAvg,
      stabilityScore: day.stabilityScore,
      insight: day.insight,
      summary: day.summary,
      suggestion: day.suggestion,
      timeline: Array.isArray(day.timeline) ? day.timeline : []
    };
  },

  onLoad() {
    const systemInfo = wx.getSystemInfoSync();
    this.setData({
      chartWidth: Math.max(280, Math.floor(systemInfo.windowWidth - 56)),
      chartHeight: 180
    });

    this.unsubscribeRuntime = holdBleRuntime.subscribe((state) => {
      this.pendingRuntimeState = state;
      this.scheduleStateFlush();
    });
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
      if (!this.pendingRuntimeState) {
        return;
      }
      const state = this.pendingRuntimeState;
      const dailyAnalyses = state.dailyAnalyses || [];
      this.currentDailyAnalyses = dailyAnalyses;
      const activeIndex = Math.min(this.data.activeIndex || 0, Math.max(0, dailyAnalyses.length - 1));
      const fallbackDay = holdBleRuntime.buildFallbackDailyAnalysis();
      const activeDay = dailyAnalyses[activeIndex] || fallbackDay;
      this.activeDayPayload = activeDay || null;
      this.setData({
        dailyAnalyses: this.buildDayTabItems(dailyAnalyses),
        activeIndex,
        activeDay: this.buildActiveDayView(activeDay),
        reportText: activeDay && activeDay.generatedReport ? activeDay.generatedReport : (this.data.reportText || ''),
        reportUpdatedAt: activeDay && activeDay.generatedReportUpdatedAt ? activeDay.generatedReportUpdatedAt : (this.data.reportUpdatedAt || ''),
        reportSource: activeDay && activeDay.generatedReportSource ? activeDay.generatedReportSource : (this.data.reportSource || ''),
        reportError: activeDay && activeDay.generatedReportError ? activeDay.generatedReportError : (this.data.reportError || '')
      });
      this.scheduleChartDraw();
    }, this.renderIntervalMs);
  },

  switchDay(event) {
    const index = Number(event.currentTarget.dataset.index || 0);
    const activeDay = (this.currentDailyAnalyses && this.currentDailyAnalyses[index]) || holdBleRuntime.buildFallbackDailyAnalysis();
    this.activeDayPayload = activeDay || null;
    this.setData({
      activeIndex: index,
      activeDay: this.buildActiveDayView(activeDay),
      reportText: activeDay && activeDay.generatedReport ? activeDay.generatedReport : '',
      reportUpdatedAt: activeDay && activeDay.generatedReportUpdatedAt ? activeDay.generatedReportUpdatedAt : '',
      reportSource: activeDay && activeDay.generatedReportSource ? activeDay.generatedReportSource : '',
      reportError: activeDay && activeDay.generatedReportError ? activeDay.generatedReportError : ''
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
    const day = this.activeDayPayload;
    this.drawWaveChart('respWaveCanvas',
      this.buildSlidingWindowSeries(day ? day.respWavePoints : [], 240, 240, false),
      this.buildSlidingWindowSeries(day ? day.respBeatMarkerPoints : [], 240, 240, true), {
      lineColor: '#D5983C',
      markerColor: '#C44B1D'
    });
    this.drawWaveChart('chestPpgCanvas',
      this.buildSlidingWindowSeries(day ? day.chestPpgWavePoints : [], 240, 240, false),
      this.buildSlidingWindowSeries(day ? day.chestPpgBeatMarkerPoints : [], 240, 240, true), {
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
    const activeDay = this.activeDayPayload || holdBleRuntime.buildFallbackDailyAnalysis() || {
      day: '当前缓存',
      respirationAvg: Number(holdBleRuntime.getState().currentRespBpm || 0),
      heartRateAvg: Number(holdBleRuntime.getState().currentHeartBpm || 0),
      windowCount: 0,
      latestWindowId: 0,
      respWavePoints: [],
      respBeatMarkerPoints: [],
      chestPpgWavePoints: [],
      chestPpgBeatMarkerPoints: [],
      timeline: []
    };
    if (this.data.reportStatus === 'running') {
      return;
    }

    this.setData({ reportStatus: 'running', reportError: '', reportSource: '' });
    const respWavePoints = activeDay.respWavePoints || [];
    const respBeatPoints = activeDay.respBeatMarkerPoints || [];
    const chestWavePoints = activeDay.chestPpgWavePoints || [];
    const chestBeatPoints = activeDay.chestPpgBeatMarkerPoints || [];
    const prompt = [
      '你是健康监测日报助手。',
      '请根据以下真实缓存数据，评估用户当前这一时段的整体呼吸与心率状态，而不是逐点复述图形。',
      '要求：',
      '1. 不使用医学诊断口吻。',
      '2. 分成四段：当前状态概览、呼吸观察、胸口PPG与心率观察、建议。',
      '3. 重点回答用户目前整体状态、节律稳定性、近期是否有需要继续观察的地方。',
      '4. 若数据量不足，请在正文中直接说明不足之处，不要拒绝回答。',
      '5. 避免只是重复“某个点高某个点低”，要给出面向用户状态的总结。',
      `日期: ${activeDay.day || ''}`,
      `统计: ${JSON.stringify({ respirationAvg: activeDay.respirationAvg, heartRateAvg: activeDay.heartRateAvg, windowCount: activeDay.windowCount, latestWindowId: activeDay.latestWindowId })}`,
      `呼吸曲线总点数: ${respWavePoints.length}`,
      `呼吸跳点总点数: ${respBeatPoints.length}`,
      `胸口PPG曲线总点数: ${chestWavePoints.length}`,
      `胸口PPG跳点总点数: ${chestBeatPoints.length}`,
      `呼吸曲线采样: ${JSON.stringify(this.sampleSeriesForDisplay(respWavePoints, 180, false))}`,
      `呼吸跳点采样: ${JSON.stringify(this.sampleSeriesForDisplay(respBeatPoints, 180, true))}`,
      `胸口PPG曲线采样: ${JSON.stringify(this.sampleSeriesForDisplay(chestWavePoints, 360, false))}`,
      `胸口PPG跳点采样: ${JSON.stringify(this.sampleSeriesForDisplay(chestBeatPoints, 360, true))}`,
      `时段记录: ${JSON.stringify(activeDay.timeline || [])}`
    ].join('\n');

    try {
      const result = await wx.cloud.callFunction({
        name: 'health_insight',
        data: {
          prompt,
          report_kind: 'daily_report'
        }
      });
      const cloudResult = result && result.result ? result.result : {};
      this.setData({
        reportStatus: 'done',
        reportText: cloudResult.reply_text || '云端暂未返回报告文本。',
        reportUpdatedAt: new Date().toLocaleString(),
        reportSource: cloudResult.source || 'unknown',
        reportError: cloudResult.error_message || ''
      });
    } catch (error) {
      this.setData({
        reportStatus: 'fallback',
        reportText: '报告生成请求已经发起，但小程序侧没有拿到云函数结果。',
        reportUpdatedAt: new Date().toLocaleString(),
        reportSource: 'client-error',
        reportError: error && error.message ? error.message : 'unknown'
      });
    }
  }
});