import sys
import re

path = r'D:/ADHD/MyApplication/app/src/main/java/com/example/myapplication/MainActivity.kt'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

cmd_parse_block = """            } else if (uuid == CMD_CHAR_UUID) {
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
            } else if (uuid == MIC_AUDIO_CHAR_UUID) {"""

# Replace taking care of spaces
text = re.sub(r'(\s+)\} else if \(uuid == MIC_AUDIO_CHAR_UUID\) \{', cmd_parse_block, text)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print("Injected CMD_CHAR_UUID parser!")
