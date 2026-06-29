import sys
import re

path = r'D:/ADHD/MyApplication/app/src/main/java/com/example/myapplication/MainActivity.kt'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. ADD VAR
if "private var currentInterruptSessionId" not in text:
    text = text.replace('class MainActivity : AppCompatActivity() {', 
                        'class MainActivity : AppCompatActivity() {\n    private var currentInterruptSessionId = 0')

# 2. MODIFY InterruptAgent
old_inter = """    private fun InterruptAgent() {
        runOnUiThread {
            tvStatus.text = "检测到硬件中断 (0x02)"
            tvAiStatus.text = "硬件触发，正在录音中..."
            try {
                audioTrack?.pause()
                audioTrack?.flush()
            } catch(e: Exception){}
        }
        isAIThinking = false
        silenceRunnable?.let { silenceHandler.removeCallbacks(it) }
    }"""
new_inter = """    private fun InterruptAgent() {
        currentInterruptSessionId++ // 递增SessionId，丢弃旧网络回调
        runOnUiThread {
            tvStatus.text = "检测到硬件中断 (0x02)"
            tvAiStatus.text = "硬件触发，正在录音中..."
            try {
                mediaPlayer?.stop()
                mediaPlayer?.release()
                mediaPlayer = null
            } catch(e: Exception){}
            try {
                audioTrack?.pause()
                audioTrack?.flush()
            } catch(e: Exception){}
        }
        isAIThinking = false
        silenceRunnable?.let { silenceHandler.removeCallbacks(it) }
    }"""
if old_inter in text:
    text = text.replace(old_inter, new_inter)
else:
    print("WARNING: old_inter not matched")

# 3. Add to uploadToRealAI
text = re.sub(r'(\s+)uploadToRealAI\(finalWavBytes\)', r'\g<1>uploadToRealAI(finalWavBytes, currentInterruptSessionId)', text)
text = text.replace('private fun uploadToRealAI(audioData: ByteArray) {', 'private fun uploadToRealAI(audioData: ByteArray, reqSessionId: Int) {')
text = text.replace('if (event == "task-finished") {\n                        if (outObj != null',
                    'if (event == "task-finished") {\n                        if (reqSessionId != currentInterruptSessionId) return\n                        if (outObj != null')
text = text.replace('callLLMForReply(finalStr)', 'callLLMForReply(finalStr, reqSessionId)')

# 4. Add to callLLMForReply
text = text.replace('private fun callLLMForReply(userText: String) {', 'private fun callLLMForReply(userText: String, reqSessionId: Int) {')
text = text.replace('val respStr = response.body?.string() ?: ""\n                try {\n                    val jsonObj = JSONObject(respStr)',
                    'val respStr = response.body?.string() ?: ""\n                if (reqSessionId != currentInterruptSessionId) return\n                try {\n                    val jsonObj = JSONObject(respStr)')
text = text.replace('callTTSForAudio(replyText)', 'callTTSForAudio(replyText, reqSessionId)')

# 5. Add to callTTSForAudio
text = text.replace('private fun callTTSForAudio(textToRead: String) {', 'private fun callTTSForAudio(textToRead: String, reqSessionId: Int) {')
text = text.replace('playBase64Audio(audioData)', 'playBase64Audio(audioData, reqSessionId)')

# 6. Add to playBase64Audio
text = text.replace('private fun playBase64Audio(base64Str: String) {', 'private fun playBase64Audio(base64Str: String, reqSessionId: Int) {')
text = text.replace('Handler(Looper.getMainLooper()).post {\n                mediaPlayer?.release()', 
                    'if (reqSessionId != currentInterruptSessionId) return\n            Handler(Looper.getMainLooper()).post {\n                mediaPlayer?.release()')

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print("Patch 5 applied safely")