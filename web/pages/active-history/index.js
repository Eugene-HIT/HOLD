const { activeMeasurements } = require('../../utils/mock-health-data');

Page({
  data: {
    activeMeasurements: []
  },

  onLoad() {
    this.setData({ activeMeasurements });
  },

  openReport(event) {
    const { id } = event.currentTarget.dataset;
    if (!id) {
      return;
    }

    wx.navigateTo({
      url: `/pages/active-report/index?id=${id}`
    });
  }
});