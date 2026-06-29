let pollTimer = null; 
let innerAudioContext = null; 
const recorderManager = wx.getRecorderManager();

Page({
  data: {
    statusText: '正在建立轮询连接...',
    statusColor: '#ff9900',
    receivedMessage: '等待云端数据...',
    imageUrl: '',
    audioUrl: '',
    userVoice: '',
    aiReply: '',
    steps: [],
    isPlaying: false,
    isRecording: false,
    recordHint: '按住说话，松开发送'
  },

  onLoad() {
    console.log('🚀 页面加载，初始化超级播放器与录音机...');
    innerAudioContext = wx.createInnerAudioContext();
    wx.setInnerAudioOption({ obeyMuteSwitch: false }); // 无视物理静音键

    innerAudioContext.onPlay(() => {
      console.log('▶️ 音频开始播放了');
      this.setData({ receivedMessage: '🔊 正在外放 Gulu 传来的语音...', isPlaying: true });
    });

    innerAudioContext.onEnded(() => {
      console.log('⏹️ 播放自然结束');
      this.setData({ receivedMessage: '✅ 语音播放完毕，可点击重新播放 👇', isPlaying: false });
    });

    innerAudioContext.onError((res) => {
      console.error('❌ 播放报错！', res);
      this.setData({ receivedMessage: '❌ 播放出错，请看控制台', isPlaying: false });
    });

    recorderManager.onStart(() => {
      console.log('🎙️ 录音开始');
      this.setData({
        isRecording: true,
        recordHint: '松开结束，正在录音...',
        receivedMessage: '🎙️ 正在录音，松开发送...'
      });
    });

    recorderManager.onStop((res) => {
      console.log('🎤 录音结束，临时路径:', res.tempFilePath);
      this.setData({
        isRecording: false,
        recordHint: '按住说话，松开发送',
        receivedMessage: '⬆️ 正在上传指令给 Gulu...'
      });

      if (res && res.tempFilePath) {
        this.uploadCommandAudio(res.tempFilePath);
      }
    });

    recorderManager.onError((err) => {
      console.error('❌ 录音失败', err);
      this.setData({
        isRecording: false,
        recordHint: '录音失败，请重试',
        receivedMessage: '❌ 录音失败，请检查麦克风权限'
      });
    });

    this.fetchCloudData();
    pollTimer = setInterval(() => {
      this.fetchCloudData();
    }, 2000);
  },

  onUnload() {
    if (pollTimer) clearInterval(pollTimer);
    if (innerAudioContext) innerAudioContext.destroy();
    if (this.data.isRecording) {
      recorderManager.stop();
    }
  },

  startRecord() {
    wx.authorize({
      scope: 'scope.record',
      success: () => {
        if (innerAudioContext) {
          innerAudioContext.stop();
        }

        recorderManager.start({
          duration: 15000,
          sampleRate: 16000,
          numberOfChannels: 1,
          encodeBitRate: 48000,
          format: 'pcm'
        });
      },
      fail: () => {
        wx.showModal({
          title: '需要麦克风权限',
          content: '按住说话需要开启录音权限，请在设置中允许。',
          success: (modalRes) => {
            if (modalRes.confirm) {
              wx.openSetting();
            }
          }
        });
      }
    });
  },

  stopRecord() {
    if (!this.data.isRecording) {
      return;
    }
    recorderManager.stop();
  },

  uploadCommandAudio(tempFilePath) {
    this.setData({
      recordHint: '正在发送语音...',
      receivedMessage: '⬆️ 正在上传指令给 Gulu...'
    });

    const cloudPath = `commands/cmd_${Date.now()}_${Math.random().toString(36).slice(2)}.pcm`;

    wx.cloud.uploadFile({
      cloudPath,
      filePath: tempFilePath,
      success: (uploadRes) => {
        console.log('☁️ 指令音频上云成功:', uploadRes.fileID);
        const db = wx.cloud.database();
        db.collection('app_commands').add({
          data: {
            audio_url: uploadRes.fileID,
            status: 'unread',
            timestamp: db.serverDate()
          },
          success: () => {
            this.setData({
              recordHint: '按住说话，松开发送',
              receivedMessage: '✅ 指令已发送，Gulu 马上执行！'
            });
            wx.showToast({ title: '发送成功', icon: 'success' });
          },
          fail: (err) => {
            console.error('写入 app_commands 失败', err);
            this.setData({
              recordHint: '发送失败，请重试',
              receivedMessage: '❌ 指令登记失败'
            });
          }
        });
      },
      fail: (err) => {
        console.error('上传指令失败', err);
        this.setData({
          recordHint: '上传失败，请重试',
          receivedMessage: '❌ 指令上传失败'
        });
      }
    });
  },

  fetchCloudData() {
    const that = this;
    const db = wx.cloud.database();

    db.collection('device_status')
      .orderBy('timestamp', 'desc') 
      .limit(10) // 🌟 核心解法 1：把目光放宽到 10 条！绝不漏掉被极速覆盖的录音！
      .get({
        success: function(res) {
          if (res.data.length > 0) {
            let updateData = {
              statusText: '✅ 监控中',
              statusColor: '#07c160'
            };

            // 状态栏依然显示绝对最新的提示
            updateData.receivedMessage = res.data[0].status || that.data.receivedMessage;

            let foundAudio = false;
            let foundImage = false;
            let foundDialogue = false;
            let shouldAutoPlay = false;

            // 🌟 核心解法 2：往前翻旧账，把各个板块最新的一条拼图找齐
            for (let i = 0; i < res.data.length; i++) {
              let record = res.data[i];

              // 找图片
              if (!foundImage && record.image_url) {
                updateData.imageUrl = record.image_url;
                foundImage = true;
              }

              // 找声音
              if (!foundAudio && record.audio_url) {
                if (record.audio_url !== that.data.audioUrl) {
                  shouldAutoPlay = true; // 发现一条之前没见过的录音！
                }
                updateData.audioUrl = record.audio_url;
                foundAudio = true;
              }

              // 找对话文字
              if (!foundDialogue && (record.user_voice_text || record.ai_reply_text)) {
                updateData.userVoice = record.user_voice_text || '';
                updateData.aiReply = record.ai_reply_text || '';
                updateData.steps = record.ai_steps || [];
                foundDialogue = true;
              }

              // 如果三个都找到了，就停止往前找
              if (foundImage && foundAudio && foundDialogue) break;
            }

            that.setData(updateData, () => {
              if (shouldAutoPlay && !that.data.isRecording) {
                console.log("🔔 检测到全新语音，触发自动播放！");
                that.playAudio();
              }
            });
          }
        }
      });
  },

  playAudio() {
    if (!this.data.audioUrl) {
      wx.showToast({ title: '暂无语音可播', icon: 'none' });
      return;
    }

    console.log("👆 准备播放语音:", this.data.audioUrl);
    this.setData({ receivedMessage: '⏳ 正在下载语音缓存...' });

    // 播放前强制清空内存，防卡死
    innerAudioContext.stop();

    // 🌟 核心解法 3：暴力下载本地播放流，微信绝对不会再哑火！
    const executePlay = (url) => {
      wx.downloadFile({
        url: url,
        success: (res) => {
          if (res.statusCode === 200) {
            console.log("⬇️ 强行下载到本地成功:", res.tempFilePath);
            this.setData({ receivedMessage: '🔊 正在播放语音...' });
            innerAudioContext.src = res.tempFilePath;
            setTimeout(() => { innerAudioContext.play(); }, 100);
          } else {
            this.setData({ receivedMessage: '❌ 语音下载失败' });
          }
        },
        fail: (err) => {
          console.error("下载报错了:", err);
          this.setData({ receivedMessage: '❌ 无法下载语音' });
        }
      });
    };

    if (this.data.audioUrl.startsWith('cloud://')) {
      wx.cloud.getTempFileURL({
        fileList: [this.data.audioUrl],
        success: res => {
          if (res.fileList && res.fileList[0].tempFileURL) {
            executePlay(res.fileList[0].tempFileURL);
          } else {
            this.setData({ receivedMessage: '❌ 链接转换失败' });
          }
        },
        fail: err => {
          this.setData({ receivedMessage: '❌ 无法访问云存储' });
        }
      });
    } else {
      executePlay(this.data.audioUrl);
    }
  }
});