const holdBleRuntime = require('../../utils/hold-ble-runtime');

Page({
  data: {
    activeMeasurements: []
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

  onLoad() {
    this.unsubscribeRuntime = holdBleRuntime.subscribe((state) => {
      this.setData({
        activeMeasurements: this.buildMeasurementPreviewList(state.activeMeasurements || [])
      });
    });
  },

  onUnload() {
    if (this.unsubscribeRuntime) {
      this.unsubscribeRuntime();
      this.unsubscribeRuntime = null;
    }
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
  }
});