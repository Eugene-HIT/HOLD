const holdBleRuntime = require('../../utils/hold-ble-runtime');

function formatCount(value) {
  return value === 0 || value ? `${value}` : '--';
}

Page({
  data: {
    hasToday: false,
    todayResp: '--',
    todayHeart: '--',
    todayWindows: '--',
    todaySummary: '',

    overallSummary: null,
    sections: [],
    insightStatus: 'idle'
  },

  buildSections(summary) {
    const list = summary && Array.isArray(summary.sections) ? summary.sections : [];
    const pick = (key, title, emptyText) => {
      const found = list.filter((item) => item && item.key === key)[0];
      return {
        key,
        title,
        body: found && found.body ? found.body : emptyText
      };
    };

    return [
      pick('resp', '呼吸报告', '暂无呼吸窗口数据，连接设备并佩戴一段时间后会自动积累。'),
      pick('heart', '心率报告', '暂无心率趋势数据，连接设备并佩戴一段时间后会自动积累。')
    ];
  },

  onLoad() {
    this.unsubscribeRuntime = holdBleRuntime.subscribe((state) => {
      const overallSummary = state.overallSummary || { title: '整体分析', summary: '', advice: '', updatedAt: '', sections: [] };
      const latestDaily = (state.dailyAnalyses || [])[0] || null;
      this.setData({
        overallSummary,
        insightStatus: state.insightStatus || 'idle',
        sections: this.buildSections(overallSummary),

        hasToday: !!latestDaily,
        todayResp: latestDaily ? formatCount(latestDaily.respirationAvg) : '--',
        todayHeart: latestDaily ? formatCount(latestDaily.heartRateAvg) : '--',
        todayWindows: latestDaily ? formatCount(latestDaily.windowCount) : '--',
        todaySummary: latestDaily ? (latestDaily.summary || '') : ''
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

  openDailyAnalysis() {
    wx.navigateTo({ url: '/pages/daily-analysis/index' });
  }
});