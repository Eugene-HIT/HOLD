import sys
import re

path = r'D:/ADHD/MyApplication/app/src/main/java/com/example/myapplication/MainActivity.kt'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add currentInterruptSessionId to MainActivity
if 'private var currentInterruptSessionId' not in text:
    text = text.replace('class MainActivity : AppCompatActivity() {', 
                        'class MainActivity : AppCompatActivity() {\n    private var currentInterruptSessionId = 0')

# 2. Modify InterruptAgent safely
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
# Find existing InterruptAgent
old_interrupt = re.search(r'private fun InterruptAgent\(\) \{[\s\S]*?audioTrack\?\.pause\(\)[\s\S]*?audioTrack\?\.flush\(\)[\s\S]*?catch\(e: Exception\)\{\}[\s\S]*?\}[\s\S]*?\}', text)
if old_interrupt:
    text = text.replace(old_interrupt.group(0), interrupt_body)
else:
    print("Could not find InterruptAgent to replace!!")

# 3. Add sessionId passing in calls
text = text.replace('uploadToRealAI(finalWavBytes)', 'uploadToRealAI(finalWavBytes, currentInterruptSessionId)')

text = text.replace('private fun uploadToRealAI(audioData: ByteArray) {', 'private fun uploadToRealAI(audioData: ByteArray, reqSessionId: Int) {')
# Inside uploadToRealAI, when checking task-finished
text = text.replace('if (event == "task-finished") {\n                        if (outObj != null', 
                    'if (event == "task-finished") {\n                        if (reqSessionId != currentInterruptSessionId) return\n                        if (outObj != null')
text = text.replace('callLLMForReply(finalStr)', 'callLLMForReply(finalStr, reqSessionId)')

text = text.replace('private fun callLLMForReply(userText: String) {', 'private fun callLLMForReply(userText: String, reqSessionId: Int) {')
text = text.replace('val respStr = response.body?.string() ?: ""\n                try {\n                    val jsonObj', 
                    'val respStr = response.body?.string() ?: ""\n                if (reqSessionId != currentInterruptSessionId) return\n                try {\n                    val jsonObj')
text = text.replace('callTTSForAudio(replyText)', 'callTTSForAudio(replyText, reqSessionId)')

text = text.replace('private fun callTTSForAudio(textToRead: String) {', 'private fun callTTSForAudio(textToRead: String, reqSessionId: Int) {')
text = text.replace('override fun onResponse(call: Call, response: Response) {\n                val respStr = response.body?.string() ?: ""\n                try {', 
                    'override fun onResponse(call: Call, response: Response) {\n                val respStr = response.body?.string() ?: ""\n                if (reqSessionId != currentInterruptSessionId) return\n                try {')
text = re.sub(r'override fun onResponse\(call: Call, response: Response\) \{\s*val respStr = response\.body\?\.string\(\) \?: ""\s*try \{\s*val jsonObj', 
              r'override fun onResponse(call: Call, response: Response) {\n                val respStr = response.body?.string() ?: ""\n                if (reqSessionId != currentInterruptSessionId) return\n                try {\n                    val jsonObj', text, count=1)
text = text.replace('playBase64Audio(audioData)', 'playBase64Audio(audioData, reqSessionId)')

text = text.replace('private fun playBase64Audio(base64Str: String) {', 'private fun playBase64Audio(base64Str: String, reqSessionId: Int) {')
text = text.replace('// Play on Android\n            Handler(Looper.getMainLooper()).post {', 
                    '// Play on Android\n            if (reqSessionId != currentInterruptSessionId) return\n            Handler(Looper.getMainLooper()).post {')

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print("Patch 3 applied")
