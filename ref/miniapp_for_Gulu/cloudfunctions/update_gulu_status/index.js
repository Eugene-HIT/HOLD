const cloud = require('wx-server-sdk')
const tcb = require('@cloudbase/node-sdk')
cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV })
const db = cloud.database()
const adminApp = tcb.init({ env: cloud.DYNAMIC_CURRENT_ENV })

exports.main = async (event, context) => {
  let data = {}
  
  // 🌟 终极修复：专门拦截并解密被微信网关加密的大体积录音数据！
  try { 
    let bodyStr = event.body
    if (event.isBase64Encoded) {
      bodyStr = Buffer.from(event.body, 'base64').toString('utf8')
    }
    data = JSON.parse(bodyStr) 
  } catch (e) { 
    data = event 
  }

  let fileID = null;

  try {
    if (data.action === 'getUploadMetadata') {
      const extension = data.fileType === 'image' ? 'jpg' : (data.extension || 'wav')
      const cloudPath = `gulu_media/${Date.now()}_${Math.random().toString(36).substr(2)}.${extension}`
      const uploadMeta = await adminApp.getUploadMetadata({ cloudPath })

      return {
        code: 200,
        msg: '获取直传凭证成功',
        cloudPath,
        url: uploadMeta.data.url,
        token: uploadMeta.data.token,
        authorization: uploadMeta.data.authorization,
        fileID: uploadMeta.data.fileId,
        cosFileId: uploadMeta.data.cosFileId,
        requestId: uploadMeta.requestId
      }
    }

    if (data.action === 'saveUploadedFile' && data.fileID && data.fileType) {
      const dbData = {
        status: data.status || (data.fileType === 'image' ? '📷 收到最新监控画面' : (data.fileType === 'audio' ? '🎵 收到最新语音' : '未知状态')),
        timestamp: db.serverDate(),
        user_voice_text: '',
        ai_reply_text: '',
        ai_steps: []
      }

      if (data.fileType === 'image') dbData.image_url = data.fileID
      if (data.fileType === 'audio') dbData.audio_url = data.fileID

      const addResult = await db.collection('device_status').add({ data: dbData })
      return { code: 200, msg: '登记上传文件成功', fileID: data.fileID, recordID: addResult._id }
    }

    // 1. 如果传来了文件（Base64格式），先存入【云存储】
    if (data.fileBase64 && data.fileType) {
      const buffer = Buffer.from(data.fileBase64, 'base64')
      const extension = data.fileType === 'image' ? 'jpg' : 'wav'
      const cloudPath = `gulu_media/${Date.now()}_${Math.random().toString(36).substr(2)}.${extension}`

      const uploadResult = await cloud.uploadFile({
        cloudPath: cloudPath,
        fileContent: buffer,
      })
      fileID = uploadResult.fileID 
    }

    // 2. 构造存入数据库的对象（全面兼容文件、文字、对话流）
    let dbData = {
      status: data.status || (data.fileType === 'image' ? '📷 收到最新监控画面' : (data.fileType === 'audio' ? '🎵 收到最新语音' : '未知状态')),
      timestamp: db.serverDate(),
      user_voice_text: data.user_voice_text || '', 
      ai_reply_text: data.ai_reply_text || '',     
      ai_steps: data.ai_steps || []                
    }
    
    // 🌟 修复保障：只有真的拿到了 fileID，才把 url 写进数据库
    if (data.fileType === 'image' && fileID) dbData.image_url = fileID;
    if (data.fileType === 'audio' && fileID) dbData.audio_url = fileID;

    await db.collection('device_status').add({ data: dbData })
    return { code: 200, msg: '同步成功', fileID: fileID }
  } catch (err) {
    console.error("云函数执行报错:", err)
    return { code: 500, msg: err.message || err }
  }
}