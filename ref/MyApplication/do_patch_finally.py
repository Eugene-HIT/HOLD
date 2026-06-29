import codecs

p = 'D:/ADHD/MyApplication/app/src/main/java/com/example/myapplication/MainActivity.kt'
import io
with codecs.open(p, 'r', 'utf-8') as f:
    t = f.read()

# 1. PTT
old_ptt = '''    private fun startPttRecording() {
        if (androidx.core.content.ContextCompat.checkSelfPermission(this, android.Manifest.permission.RECORD_AUDIO) != android.content.pm.PackageManager.PERMISSION_GRANTED) {
            return
        }
        val minBufSize'''.replace('\n', '\r\n')

new_ptt = '''    private fun startPttRecording() {
        if (androidx.core.content.ContextCompat.checkSelfPermission(this, android.Manifest.permission.RECORD_AUDIO) != android.content.pm.PackageManager.PERMISSION_GRANTED) {
            return
        }
        isInterrupted = true
        isAIThinking = false
        isPlayingAudio = false
        try { mediaPlayer?.stop(); mediaPlayer?.release(); mediaPlayer = null } catch(e:Exception){}
        try { audioTrack?.pause(); audioTrack?.flush() } catch (e: Exception) {}
        runOnUiThread { tvAiStatus.text = "🚫 用户按键打断AI！" }
        val minBufSize'''.replace('\n', '\r\n')
if 'mediaPlayer?.stop()' not in t.split('private fun startPttRecording()')[1][:300]:
    t = t.replace(old_ptt, new_ptt)
else:
    print('PTT already patched')

# 2. resetAI
old_reset = '''            playbackBuffer.reset()
            audioTrack?.pause()'''.replace('\n', '\r\n')
new_reset = '''            playbackBuffer.reset()
            try { mediaPlayer?.stop(); mediaPlayer?.release(); mediaPlayer = null } catch(e:Exception){}
            audioTrack?.pause()'''.replace('\n', '\r\n')
if old_reset in t:
    t = t.replace(old_reset, new_reset)
else:
    print("Failed Reset")

# 3. VAD Interrupt
old_vad = '''                            isAIThinking = false
                            // WriteSemaphore removed
                            try { audioTrack?.pause(); audioTrack?.flush() } catch (e: Exception) {}'''.replace('\n', '\r\n')
new_vad = '''                            isAIThinking = false
                            try { mediaPlayer?.stop(); mediaPlayer?.release(); mediaPlayer = null } catch(e:Exception){}
                            // WriteSemaphore removed
                            try { audioTrack?.pause(); audioTrack?.flush() } catch (e: Exception) {}'''.replace('\n', '\r\n')
if old_vad in t:
    t = t.replace(old_vad, new_vad)
else:
    print("Failed VAD")

with codecs.open(p, 'w', 'utf-8') as f:
    f.write(t)

print("Applied CRLF PTT, VAD, and resetAI interruption links.")
