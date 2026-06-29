import codecs

p = 'D:/ADHD/MyApplication/app/src/main/java/com/example/myapplication/MainActivity.kt'
with codecs.open(p, 'r', 'utf-8') as f:
    t = f.read()

# 1. uploadToRealAI
old_up = '''    private fun uploadToRealAI(audioData: ByteArray) {
        val taskId'''.replace('\n', '\r\n')
new_up = '''    private fun uploadToRealAI(audioData: ByteArray) {
        isInterrupted = false
        val taskId'''.replace('\n', '\r\n')
if old_up in t:
    t = t.replace(old_up, new_up)
    print("uploadToRealAI patched")
else:
    print("uploadToRealAI failed")

# 2. callLLMForReply
old_llm = '''            private fun callLLMForReply(userText: String) {
        val sysContent'''.replace('\n', '\r\n')
new_llm = '''            private fun callLLMForReply(userText: String) {
        isInterrupted = false
        val sysContent'''.replace('\n', '\r\n')
if old_llm in t:
    t = t.replace(old_llm, new_llm)
    print("callLLMForReply patched")
else:
    print("callLLMForReply failed")

# 3. resetAI
old_reset = '''    private fun resetAI(delayMs: Long = 0) {
        Handler(Looper.getMainLooper()).postDelayed({
            isAIThinking = false'''.replace('\n', '\r\n')
new_reset = '''    private fun resetAI(delayMs: Long = 0) {
        Handler(Looper.getMainLooper()).postDelayed({
            isInterrupted = false
            isAIThinking = false'''.replace('\n', '\r\n')
if old_reset in t:
    t = t.replace(old_reset, new_reset)
    print("resetAI patched")
else:
    print("resetAI failed")

old_reset2 = '''            playbackBuffer.reset()
            audioTrack?.pause()'''.replace('\n', '\r\n')
new_reset2 = '''            playbackBuffer.reset()
            try { mediaPlayer?.stop(); mediaPlayer?.release(); mediaPlayer = null } catch(e:Exception){}
            audioTrack?.pause()'''.replace('\n', '\r\n')
if old_reset2 in t:
    t = t.replace(old_reset2, new_reset2)
    print("resetAI 2 patched")

with codecs.open(p, 'w', 'utf-8') as f:
    f.write(t)
