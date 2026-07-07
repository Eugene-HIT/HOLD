const holdBleRuntime = require('./utils/hold-ble-runtime');

App({
  onLaunch() {
    if (!wx.cloud) {
      console.error('当前基础库不支持云开发');
      return;
    }

    wx.cloud.init({
      traceUser: true,
      env: 'hold-dev-env-d2gukfp01ac296189'
    });

    holdBleRuntime.init();
  },

  globalData: {
    bleRuntime: holdBleRuntime
  }
});