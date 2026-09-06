const holdBleRuntime = require('../../utils/hold-ble-runtime');

Page({
  data: {
    activeTab: 'active',
    activeMeasurements: [],
    dailyAnalyses: [],
    activeCount: 0,
    dailyCount: 0
  },

  buildMeasurementPreviewList(measurements) {
    return (Array.isArray(measurements) ? measurements : []).map((item) => ({
      id: item.id,
      title: item.title,
      resultTag: item.resultTag,
      startedAt: item.startedAt,
      durationLabel: item.durationLabel,
      summary: item.summary,
      metrics: item.metrics,
      generatedReportText: item.generatedReportText || '',
      generatedReportSource: item.generatedReportSource || '',
      generatedReportError: item.generatedReportError || '',
      generatedReportUpdatedAt: item.generatedReportUpdatedAt || ''
    }));
  },

  buildDailyPreviewList(days) {
    return (Array.isArray(days) ? days : []).map((item) => ({
      dayKey: `${item.dayKey || item.day || ''}`,
      day: item.day || '',
      title: item.title || '',
      respirationAvg: item.respirationAvg,
      heartRateAvg: item.heartRateAvg,
      windowCount: item.windowCount,
      summary: item.summary || ''
    }));
  },

  onLoad() {
    this.unsubscribeRuntime = holdBleRuntime.subscribe((state) => {
      const activeMeasurements = this.buildMeasurementPreviewList(state.activeMeasurements || []);
      const dailyAnalyses = this.buildDailyPreviewList(state.dailyAnalyses || []);
      this.setData({
        activeMeasurements,
        dailyAnalyses,
        activeCount: activeMeasurements.length,
        dailyCount: dailyAnalyses.length
      });
    });
  },

  onUnload() {
    if (this.unsubscribeRuntime) {
      this.unsubscribeRuntime();
      this.unsubscribeRuntime = null;
    }
  },

  switchRecordTab(event) {
    const tab = event.currentTarget.dataset.tab;
    if (!tab || tab === this.data.activeTab) {
      return;
    }
    this.setData({ activeTab: tab });
  },

  openReport(event) {
    const { id } = event.currentTarget.dataset;
    if (!id) {
      return;
    }

    wx.navigateTo({
      url: `/pages/active-report/index?id=${id}`
    });
  },

  async generateReport(event) {
    const { id } = event.currentTarget.dataset;
    if (!id) {
      return;
    }

    await holdBleRuntime.requestActiveMeasurementInsight(id, { force: true });
  },

  openDaily(event) {
    const { day } = event.currentTarget.dataset;
    wx.navigateTo({
      url: day
        ? `/pages/daily-analysis/index?day=${encodeURIComponent(day)}`
        : '/pages/daily-analysis/index'
    });
  }
});
