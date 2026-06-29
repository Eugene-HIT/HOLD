# -*- coding: utf-8 -*-
import codecs
import re

p = 'D:/ADHD/MyApplication/app/src/main/java/com/example/myapplication/MainActivity.kt'
with codecs.open(p, 'r', 'utf-8') as f:
    t = f.read()

# 1. Variables
old_vars = r'    private var isRecordingLocal = false\s+private var isAIThinking = false\s+private var hasGreeted = false'
new_vars = '''    private var isRecordingLocal = false
    private var isAIThinking = false
    @Volatile private var isInterrupted = false
    private var interruptFrames = 0
    private var hasGreeted = false'''
if re.search(old_vars, t):
    t = re.sub(old_vars, new_vars.replace('\n', '\r\n'), t)
    print("Variables Patched")

# 2. VAD Logic
old_vad = r'                // 2\. 16-bit VAD AI Logic\s+if \(!isAIThinking\) \{\s+var maxEnergy = 0'
new_vad = '''                // 1.5 Interrupt Logic (User talks while AI plays/thinks)
                if (isAIThinking || mediaPlayer?.isPlaying == true) {
                    var maxEnergy = 0
                    val shortBuffer = java.nio.ByteBuffer.wrap(data).order(java.nio.ByteOrder.LITTLE_ENDIAN).asShortBuffer()
                    while (shortBuffer.hasRemaining()) {
                        val energy = Math.abs(shortBuffer.get().toInt())
                        if (energy > maxEnergy) maxEnergy = energy
                    }
                    if (maxEnergy > 2000) {
                        interruptFrames++
                        if (interruptFrames > 4) {
                            android.util.Log.i("AI_DEBUG", "INTERRUPT TRIGGERED!")
                            isInterrupted = true
                            try { mediaPlayer?.stop(); mediaPlayer?.release(); mediaPlayer = null } catch(e:Exception){}
                            isPlayingAudio = false
                            isAIThinking = false
                            try { aliyunWebSocket?.cancel() } catch (e: Exception) {}

                            runOnUiThread { tvAiStatus.text = "🚫已打断AI，重新倾听中..." }

                            isRecordingLocal = true
                            audioBufferQueue.clear()
                            interruptFrames = 0
                        }
                    } else {
                        if (interruptFrames > 0) interruptFrames--
                    }
                }

                // 2. 16-bit VAD AI Logic
                if (!isAIThinking && mediaPlayer?.isPlaying != true) {
                    var maxEnergy = 0'''
if re.search(old_vad, t):
    t = re.sub(old_vad, new_vad.replace('\n', '\r\n'), t)
    print("VAD Logic Patched")


# 3. Stream Loop
old_stream = r'                bleWriteSemaphore\.drainPermits\(\)\s+bleWriteSemaphore\.release\(\)\s+while \(offset < audioBytes\.size\) \{\s+var length = Math\.min\(chunkSize, audioBytes\.size - offset\)'
new_stream = '''                bleWriteSemaphore.drainPermits()
                bleWriteSemaphore.release()
                isInterrupted = false

                while (offset < audioBytes.size) {
                    if (isInterrupted) {
                        android.util.Log.i("BLE_DEBUG", "stream aborted due to interrupt")
                        break
                    }
                    var length = Math.min(chunkSize, audioBytes.size - offset)'''
if re.search(old_stream, t):
    t = re.sub(old_stream, new_stream.replace('\n', '\r\n'), t)
    print("Stream Patched")

# 4. PTT
old_ptt = r'    private fun startPttRecording\(\) \{\s+if \(androidx\.core\.content\.ContextCompat\.checkSelfPermission'
new_ptt = '''    private fun startPttRecording() {
        if (androidx.core.content.ContextCompat.checkSelfPermission'''
if re.search(old_ptt, t):
    # We just want to insert the interrupt code after the permission check
    pass 
# let's be more specific for PTT
old_ptt2 = r'        if \(androidx\.core\.content\.ContextCompat\.checkSelfPermission\(this, android\.Manifest\.permission\.RECORD_AUDIO\) != android\.content\.pm\.PackageManager\.PERMISSION_GRANTED\) \{\s+return\s+\}\s+val minBufSize'
new_ptt2 = '''        if (androidx.core.content.ContextCompat.checkSelfPermission(this, android.Manifest.permission.RECORD_AUDIO) != android.content.pm.PackageManager.PERMISSION_GRANTED) {
            return
        }
        
        android.util.Log.i("AI_DEBUG", "User Pressed PTT! Interrupting AI.")
        isInterrupted = true
        try { mediaPlayer?.stop(); mediaPlayer?.release(); mediaPlayer = null } catch(e:Exception){}
        try { aliyunWebSocket?.cancel() } catch (e: Exception) {}
        isPlayingAudio = false
        isAIThinking = false
        runOnUiThread { tvAiStatus.text = "🚫用户按键，直接倾听..." }

        val minBufSize'''
if re.search(old_ptt2, t):
    t = re.sub(old_ptt2, new_ptt2.replace('\n', '\r\n'), t)
    print("PTT Patched")


# 5. Reset AI
old_reset = r'            playbackBuffer\.reset\(\)\s+audioTrack\?\.pause\(\)\s+audioTrack\?\.flush\(\)'
new_reset = '''            playbackBuffer.reset()
            try { mediaPlayer?.stop(); mediaPlayer?.release(); mediaPlayer = null } catch(e:Exception){}
            audioTrack?.pause()
            audioTrack?.flush()'''
if re.search(old_reset, t):
    t = re.sub(old_reset, new_reset.replace('\n', '\r\n'), t)
    print("Reset Patched")


with codecs.open(p, 'w', 'utf-8') as f:
    f.write(t)
