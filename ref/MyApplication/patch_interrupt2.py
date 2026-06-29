import sys
import re

path = r'D:/ADHD/MyApplication/app/src/main/java/com/example/myapplication/MainActivity.kt'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add currentInterruptSessionId to MainActivity class variables
if 'private var currentInterruptSessionId' not in text:
    text = text.replace('class MainActivity : AppCompatActivity() {', 
                        'class MainActivity : AppCompatActivity() {\n    private var currentInterruptSessionId = 0')

# 2. Modify InterruptAgent 
interrupt_body = """    private fun InterruptAgent() {
        currentInterruptSessionId++ // invalidate running/pending network tasks
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
# old logic
old_interrupt = re.search(r'private fun InterruptAgent\(\) \{[\s\S]*?audioTrack\?\.pause\(\)[\s\S]*?audioTrack\?\.flush\(\)[\s\S]*?catch\(e: Exception\)\{\}[\s\S]*?\}[\s\S]*?\}', text)
if old_interrupt:
    text = text.replace(old_interrupt.group(0), interrupt_body)
else:
    print("WARNING: Could not match InterruptAgent")

# 3. processAndUploadAudio
text = text.replace('uploadToRealAI(finalWavBytes)', 'uploadToRealAI(finalWavBytes, currentInterruptSessionId)')

# 4. uploadToRealAI
text = text.replace('private fun uploadToRealAI(audioData: ByteArray) {', 'private fun uploadToRealAI(audioData: ByteArray, reqSessionId: Int) {')
text = text.replace('if (event == "task-finished") {', 'if (event == "task-finished") {\n                        if (reqSessionId != currentInterruptSessionId) return\n')
text = text.replace('callLLMForReply(finalStr)', 'callLLMForReply(finalStr, reqSessionId)')

# 5. callLLMForReply
text = text.replace('private fun callLLMForReply(userText: String) {', 'private fun callLLMForReply(userText: String, reqSessionId: Int) {')
text = text.replace('val respStr = response.body?.string() ?: ""\n                try {', 
                    'val respStr = response.body?.string() ?: ""\n                if (reqSessionId != currentInterruptSessionId) return\n                try {')
text = text.replace('callTTSForAudio(replyText)', 'callTTSForAudio(replyText, reqSessionId)')

# 6. callTTSForAudio
text = text.replace('private fun callTTSForAudio(textToRead: String) {', 'private fun callTTSForAudio(textToRead: String, reqSessionId: Int) {')
text = text.replace('val respStr = response.body?.string() ?: ""\n                try {', 
                    'val respStr = response.body?.string() ?: ""\n                if (reqSessionId != currentInterruptSessionId) return\n                try {')
text = text.replace('playBase64Audio(audioData)', 'playBase64Audio(audioData, reqSessionId)')

# 7. playBase64Audio
text = text.replace('private fun playBase64Audio(base64Str: String) {', 'private fun playBase64Audio(base64Str: String, reqSessionId: Int) {')
text = text.replace('// Play on Android\n            Handler(Looper.getMainLooper()).post {', 
                    '// Play on Android\n            if (reqSessionId != currentInterruptSessionId) return\n            Handler(Looper.getMainLooper()).post {')

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print("Patch applied successfully")
