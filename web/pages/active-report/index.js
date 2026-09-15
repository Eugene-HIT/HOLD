const { getMeasurementById } = require('../../utils/mock-health-data');

Page({
  data: {
    report: null
  },

  onLoad(options) {
    const report = getMeasurementById(options.id);
    this.setData({ report });
  }
});