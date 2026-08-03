/**
 * miniprogram_hosting.js
 * -----------------------
 * 微信云托管调用示例
 *
 * 需确保小程序与目标云开发环境已完成关联(见: https://docs.cloudbase.net/quick-start/create-env)
 *
 * 使用前确保：
 * 1. 已开通云开发和云托管
 * 2. App.js 中已调用 wx.cloud.init
 * 3. 微信小程序基础库 >= 2.23.0
 */

// 云开发环境ID
const ENV_ID = 'hold-dev-env-d2gukfp01ac296189';
// 云托管服务名
const SERVICE_NAME = 'ppg-predict';

// 调用 PPG 情感检测 API
async function callPpgPredict(t_ms, sig) {
  try {
    const result = await wx.cloud.callContainer({
      config: {
        env: ENV_ID,
      },
      path: '/api/ppg_predict',
      method: 'POST',
      header: {
        'X-WX-SERVICE': SERVICE_NAME,
        'content-type': 'application/json'
      },
      data: {
        t_ms: t_ms,
        sig: sig
      }
    });

    if (result.statusCode === 200) {
      const body = result.data;
      if (body.code === 0) {
        console.log('检测完成:', body.data);
        return body.data;
      } else {
        console.error('业务错误:', body.message);
        throw new Error(body.message);
      }
    } else {
      console.error('HTTP 错误:', result.statusCode);
      throw new Error(`HTTP ${result.statusCode}`);
    }
  } catch (err) {
    console.error('调用云托管失败:', err);
    throw err;
  }
}

module.exports = {
  callPpgPredict,
  ENV_ID,
  SERVICE_NAME
};
