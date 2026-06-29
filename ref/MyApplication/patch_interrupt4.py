import sys

path = r'D:/ADHD/MyApplication/app/src/main/java/com/example/myapplication/MainActivity.kt'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Session ID Class Variable
if 'private var currentInterruptSessionId' not in text:
    text = text.replace('class MainActivity : AppCompatActivity() {', 
                        'class MainActivity : AppCompatActivity() {\n    private var currentInterruptSessionId = 0')

# 2. Modify InterruptAgent
old_interrupt = """    private fun InterruptAgent() {
        runOnUiThread {
            tvStatus.text = "检测到硬件中断 (0x02)"
            tvAiStatus.text = "硬件触发，正在录音中..."
            try {
                audioTrack?.pause()
                audioTrack?.flush()
            } catch(e: Exception){}
        }
    }"""
new_interrupt = """    private fun InterruptAgent() {
        currentInterruptSessionId++ // 回调隔离
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
    }"""
if old_interrupt in text:
    text = text.replace(old_interrupt, new_interrupt)
else:
    print("WARNING: Could not find old InterruptAgent text exactly!")

# 3. uploadToRealAI
text = text.replace('uploadToRealAI(finalWavBytes)', 'uploadToRealAI(finalWavBytes, currentInterruptSessionId)')
text = text.replace('private fun uploadToRealAI(audioData: ByteArray) {', 'private fun uploadToRealAI(audioData: ByteArray, reqSessionId: Int) {')
text = text.replace('if (event == "task-finished") {\n                        if (outObj != null', 
                    'if (event == "task-finished") {\n                        if (reqSessionId != currentInterruptSessionId) return\n                        if (outObj != null')
text = text.replace('callLLMForReply(finalStr)', 'callLLMForReply(finalStr, reqSessionId)')

# 4. callLLMForReply
text = text.replace('private fun callLLMForReply(userText: String) {', 'private fun callLLMForReply(userText: String, reqSessionId: Int) {')
text = text.replace('val respStr = response.body?.string() ?: ""\n                try {\n                    val jsonObj', 
                    'val respStr = response.body?.string() ?: ""\n                if (reqSessionId != currentInterruptSessionId) return\n                try {\n                    val jsonObj')
text = text.replace('callTTSForAudio(replyText)', 'callTTSForAudio(replyText, reqSessionId)')

# 5. callTTSForAudio
text = text.replace('private fun callTTSForAudio(textToRead: String) {', 'private fun callTTSForAudio(textToRead: String, reqSessionId: Int) {')

# Find the specific onResponse in callTTSForAudio to replace
old_onresponse_tts = """            override fun onResponse(call: Call, response: Response) {
                val respStr = response.body?.string() ?: ""
                try {
                    val jsonObj"""
new_onresponse_tts = """            override fun onResponse(call: Call, response: Response) {
                val respStr = response.body?.string() ?: ""
                if (reqSessionId != currentInterruptSessionId) return
                try {
                    val jsonObj"""
if text.count(old_onresponse_tts) == 1:
    text = text.replace(old_onresponse_tts, new_onresponse_tts)
elif text.count(old_onresponse_tts) > 1: # Both LLM and TTS have it if not replaced earlier
    # We already replaced LLM one (it was identical), so we'll replace all that are left
    text = text.replace(old_onresponse_tts, new_onresponse_tts)
elif text.count(old_onresponse_tts) == 0:
    print("Warning: old_onresponse_tts not found")

text = text.replace('playBase64Audio(audioData)', 'playBase64Audio(audioData, reqSessionId)')

# 6. playBase64Audio
text = text.replace('private fun playBase64Audio(base64Str: String) {', 'private fun playBase64Audio(base64Str: String, reqSessionId: Int) {')
text = text.replace('Handler(Looper.getMainLooper()).post {\n                mediaPlayer?.release()', 
                    'if (reqSessionId != currentInterruptSessionId) return\n            Handler(Looper.getMainLooper()).post {\n                mediaPlayer?.release()')

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print("Patch 4 applied")
