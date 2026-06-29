import codecs
p = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with codecs.open(p, 'r', encoding='utf-8') as f:
    text = f.read()

old_str = '            } else if (uuid == MIC_AUDIO_CHAR_UUID) {'
new_str = '''            } else if (uuid == CMD_CHAR_UUID) {
                if (data.isNotEmpty() && data[0] == 0x02.toByte()) {
                    InterruptAgent()
                    isRecordingLocal = true
                    audioBufferQueue.clear()
                    runOnUiThread { tvAiStatus.text = "🎤 硬件端正在讲话..." }
                } else if (data.isNotEmpty() && data[0] == 0x03.toByte()) {
                    if (isRecordingLocal) {
                        isRecordingLocal = false
                        isAIThinking = true
                        runOnUiThread { tvAiStatus.text = "⏳ 打包上传音频推给 STT ..." }
                        processAndUploadAudio()
                    }
                }
            } else if (uuid == MIC_AUDIO_CHAR_UUID) {'''

if old_str in text and 'uuid == CMD_CHAR_UUID' not in text[text.find(old_str)-50:text.find(old_str)]: 
    text = text.replace(old_str, new_str)
    with codecs.open(p, 'w', encoding='utf-8') as f:
        f.write(text)
    print("Injected PTT listener successfully!")
else:
    print("Already injected or couldn't find the target string.")
