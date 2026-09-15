const { dailyAnalyses } = require('../../utils/mock-health-data');

Page({
  data: {
    dailyAnalyses: [],
    activeIndex: 0,
    activeDay: null
  },

  onLoad() {
    this.setData({
      dailyAnalyses,
      activeDay: dailyAnalyses[0]
    });
  },

  switchDay(event) {
    const index = Number(event.currentTarget.dataset.index || 0);
    const activeDay = this.data.dailyAnalyses[index] || this.data.dailyAnalyses[0];
    this.setData({
      activeIndex: index,
      activeDay
    });
  }
});