const cloud = require('wx-server-sdk')
cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV })
const db = cloud.database()

exports.main = async (event, context) => {
  try {
    // 1. 查找最早的一条“未读”指令 (先进先出)
    const result = await db.collection('app_commands')
      .where({ status: 'unread' })
      .orderBy('timestamp', 'asc')
      .limit(1)
      .get()

    // 2. 如果没有新指令，告诉安卓继续等
    if (result.data.length === 0) {
      return { code: 404, msg: '没有新指令' }
    }

    const command = result.data[0]

    // 3. 把这条指令标记为“已读”，防止安卓重复播放同一句话
    await db.collection('app_commands').doc(command._id).update({
      data: { status: 'read' }
    })

    // 4. 将 cloud:// 链接换成安卓能直接下载的 https:// 链接
    const fileList = [command.audio_url]
    const urlResult = await cloud.getTempFileURL({ fileList })

    return {
      code: 200,
      msg: '获取成功',
      audio_url: urlResult.fileList[0].tempFileURL
    }
  } catch (err) {
    return { code: 500, msg: err.message || err }
  }
}