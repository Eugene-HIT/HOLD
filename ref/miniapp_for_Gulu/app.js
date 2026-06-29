App({
  onLaunch() {
    // 告诉小程序你的云环境 ID 是什么
    wx.cloud.init({
      env: 'cloud1-2g65h7na8576f841', // ⚠️ 注意：填你自己的！
      traceUser: true // 记录访问用户，方便日后调试
    })
    
    console.log('☁️ 微信云开发初始化完成！')
  }
})