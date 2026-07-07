const holdBleRuntime = require('../../utils/hold-ble-runtime');

Page({
  data: {
    overallSummary: null,
    insightStatus: 'idle',
    detailedReportStatus: 'idle',
    detailedReport: '',
    detailedReportUpdatedAt: '',
    detailedReportSource: '',
    detailedReportError: ''
  },

  onLoad() {
    this.unsubscribeRuntime = holdBleRuntime.subscribe((state) => {
      this.setData({
        overallSummary: state.overallSummary || null,
        insightStatus: state.insightStatus || 'idle'
      });
    });
  },

  onUnload() {
    if (this.unsubscribeRuntime) {
      this.unsubscribeRuntime();
      this.unsubscribeRuntime = null;
    }
  },

  refreshInsight() {
    holdBleRuntime.requestOverallInsightRefresh();
  },

  async generateDetailedReport() {
    if (this.data.detailedReportStatus === 'running') {
      return;
    }

    const state = holdBleRuntime.getState();
    const latestDaily = (state.dailyAnalyses || [])[0] || holdBleRuntime.buildFallbackDailyAnalysis() || null;
    const latestActive = (state.activeMeasurements || [])[0] || null;
    const prompt = [
      '你是健康监测综合报告助手。',
      '请根据以下当前全部真实缓存数据，分析用户目前的整体状态与近期趋势，而不是逐项复述原始数据。',
      '要求：',
      '1. 不使用医学诊断口吻。',
      '2. 按五段输出：整体状态概览、呼吸趋势、当天心率与胸口PPG趋势、指部PPG检测、综合建议。',
      '3. 重点回答用户现在整体偏稳定还是偏波动、哪些结论可信、哪些结论仍需更多数据验证。',
      '4. 明确指出数据量不足或质量不足的地方，但不要因为数据少而拒绝回答。',
      `整体摘要: ${JSON.stringify(this.data.overallSummary || {})}`,
      `当前全部日级分析: ${JSON.stringify(state.dailyAnalyses || [])}`,
      `当前全部主动检测: ${JSON.stringify(state.activeMeasurements || [])}`,
      `最近呼吸波形采样: ${JSON.stringify(latestDaily ? (latestDaily.respWavePoints || []).slice(-160) : [])}`,
      `最近呼吸跳点采样: ${JSON.stringify(latestDaily ? (latestDaily.respBeatMarkerPoints || []).slice(-160) : [])}`,
      `最近胸口PPG波形采样: ${JSON.stringify(latestDaily ? (latestDaily.chestPpgWavePoints || []).slice(-220) : [])}`,
      `最近胸口PPG跳点采样: ${JSON.stringify(latestDaily ? (latestDaily.chestPpgBeatMarkerPoints || []).slice(-220) : [])}`,
      `最近指部PPG波形采样: ${JSON.stringify(latestActive ? (latestActive.ppgWavePoints || []) : [])}`,
      `最近指部PPG跳点采样: ${JSON.stringify(latestActive ? (latestActive.ppgBeatMarkerPoints || []) : [])}`
    ].join('\n');

    this.setData({ detailedReportStatus: 'running', detailedReportSource: '', detailedReportError: '' });

    try {
      const result = await wx.cloud.callFunction({
        name: 'health_insight',
        data: {
          prompt,
          report_kind: 'overall_detailed'
        }
      });
      const cloudResult = result && result.result ? result.result : {};
      this.setData({
        detailedReportStatus: 'done',
        detailedReport: cloudResult.reply_text || '云端暂未返回详尽报告文本。',
        detailedReportUpdatedAt: new Date().toLocaleString(),
        detailedReportSource: cloudResult.source || 'unknown',
        detailedReportError: cloudResult.error_message || ''
      });
    } catch (error) {
      this.setData({
        detailedReportStatus: 'fallback',
        detailedReport: '详尽报告请求已经发起，但小程序侧没有拿到云函数结果。',
        detailedReportUpdatedAt: new Date().toLocaleString(),
        detailedReportSource: 'client-error',
        detailedReportError: error && error.message ? error.message : 'unknown'
      });
    }
  }
});