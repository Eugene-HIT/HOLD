/**
 * miniprogram_hosting.js
 * -----------------------
 * 微信云托管调用示例（替代云函数）
 * 
 * 使用 wx.cloud.callContainer 调用云托管服务
 * 需要在云托管控制台配置：
 *   - 服务名: ppg-predict（需与下面一致）
 *   - 路径: /api/ppg_predict
 *   - 环境ID: 你的云开发环境ID
 * 
 * 使用前确保：
 * 1. 已开通云开发和云托管
 * 2. App.js 中已调用 wx.cloud.init({ env: '你的环境ID' })
 * 3. 微信小程序基础库 >= 2.23.0
 */

// 调用 PPG 情感检测 API
async function callPpgPredict(t_ms, sig) {
  try {
    const res = await wx.cloud.callContainer({
      env: 'prod-xxxxxxxxxxxxxx',  // 替换为你的云开发环境ID
      path: '/api/ppg_predict',
      method: 'POST',
      header: {
        'content-type': 'application/json'
      },
      data: {
        t_ms: t_ms,  // 设备时间戳数组（毫秒）
        sig: sig     // PPG 信号数组（与 t_ms 等长）
      }
    });

    if (res.statusCode === 200) {
      const result = res.data;
      if (result.code === 0) {
        // 调用成功
        console.log('检测完成:', result.data);
        return result.data;
      } else {
        // 业务错误
        console.error('业务错误:', result.message);
        throw new Error(result.message);
      }
    } else {
      // HTTP 错误
      console.error('HTTP 错误:', res.statusCode);
      throw new Error(`HTTP ${res.statusCode}`);
    }
  } catch (err) {
    console.error('调用云托管失败:', err);
    throw err;
  }
}

// 示例：在页面中使用
// Page({
//   async onLoad() {
//     // 假设已经获取到传感器数据
//     const t_ms = [0, 40, 80, ...];
//     const sig = [50000, 50200, 49800, ...];
//     
//     try {
//       const result = await callPpgPredict(t_ms, sig);
//       console.log('预测结果:', result.predictions);
//     } catch (err) {
//       console.error('检测失败:', err);
//     }
//   }
// });

module.exports = {
  callPpgPredict
};
