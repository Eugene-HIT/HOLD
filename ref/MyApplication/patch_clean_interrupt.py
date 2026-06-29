# -*- coding: utf-8 -*-
import codecs

p = 'D:/ADHD/MyApplication/app/src/main/java/com/example/myapplication/MainActivity.kt'
with codecs.open(p, 'r', 'utf-8') as f:
    t = f.read()

def safe_replace(old_str, new_str, label):
    global t
    old_str = old_str.replace('\n', '\r\n')
    new_str = new_str.replace('\n', '\r\n')
    if old_str in t:
        t = t.replace(old_str, new_str)
        print(f"{label} Patched")
    else:
        print(f"Failed to find: {label}")

old_vars = '''    private var isRecordingLocal = false
    private var isAIThinking = false
    private var hasGreeted = false'''
new_vars = '''    private var isRecordingLocal = false
    private var isAIThinking = false
    @Volatile private var isInterrupted = false
    private var interruptFrames = 0
    private var hasGreeted = false'''
safe_replace(old_vars, new_vars, "Variables")


old_vad = '''                // 2. 16-bit VAD AI Logic
                if (!isAIThinking) {
                    var maxEnergy = 0'''
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
safe_replace(old_vad, new_vad, "VAD Logic")


old_stream = '''            if (gatt != null && spkChar != null && audioBytes.isNotEmpty()) {
                // 💡 鸿蒙最终杀手锏 V4：底层协议栈硬件流控回调 (Strict Flow Control)
                val chunkSize = 400 // 每包25ms数据，显著降低系统调用频率，充分利用 512 MTU
                var offset = 0
                
                // 发送流之前清空可能废弃的信号量，并给第一发开绿灯
                bleWriteSemaphore.drainPermits()
                bleWriteSemaphore.release()

                while (offset < audioBytes.size) {
                    var length = Math.min(chunkSize, audioBytes.size - offset)'''

new_stream = '''            if (gatt != null && spkChar != null && audioBytes.isNotEmpty()) {
                isInterrupted = false // Reset for fresh stream
                // 💡 鸿蒙最终杀手锏 V4：底层协议栈硬件流控回调 (Strict Flow Control)
                val chunkSize = 400 // 每包25ms数据，显著降低系统调用频率，充分利用 512 MTU
                var offset = 0
                
                // 发送流之前清空可能废弃的信号量，并给第一发开绿灯
                bleWriteSemaphore.drainPermits()
                bleWriteSemaphore.release()

                while (offset < audioBytes.size) {
                    if (isInterrupted) {
                        android.util.Log.i("BLE_DEBUG", "stream aborted due to interrupt")
                        break
                    }
                    var length = Math.min(chunkSize, audioBytes.size - offset)'''
safe_replace(old_stream, new_stream, "Stream Loop")


old_ptt = '''    @SuppressLint("MissingPermission")
    private fun startPttRecording() {
        if (androidx.core.content.ContextCompat.checkSelfPermission(this, android.Manifest.permission.RECORD_AUDIO) != android.content.pm.PackageManager.PERMISSION_GRANTED) {
            return
        }
        val minBufSize = android.media.AudioRecord.getMinBufferSize(16000, android.media.AudioFormat.CHANNEL_IN_MONO, android.media.AudioFormat.ENCODING_PCM_16BIT)'''

new_ptt = '''    @SuppressLint("MissingPermission")
    private fun startPttRecording() {
        if (androidx.core.content.ContextCompat.checkSelfPermission(this, android.Manifest.permission.RECORD_AUDIO) != android.content.pm.PackageManager.PERMISSION_GRANTED) {
            return
        }
        
        // Interrupt AI if currently speaking
        android.util.Log.i("AI_DEBUG", "User Pressed PTT! Interrupting AI.")
        isInterrupted = true
        try { mediaPlayer?.stop(); mediaPlayer?.release(); mediaPlayer = null } catch(e:Exception){}
        try { aliyunWebSocket?.cancel() } catch (e: Exception) {}
        isPlayingAudio = false
        isAIThinking = false
        runOnUiThread { tvAiStatus.text = "🚫用户按键，直接倾听..." }

        val minBufSize = android.media.AudioRecord.getMinBufferSize(16000, android.media.AudioFormat.CHANNEL_IN_MONO, android.media.AudioFormat.ENCODING_PCM_16BIT)'''
safe_replace(old_ptt, new_ptt, "PTT Logic")


old_reset = '''            playbackBuffer.reset()
            audioTrack?.pause()
            audioTrack?.flush()'''

new_reset = '''            playbackBuffer.reset()
            try { mediaPlayer?.stop(); mediaPlayer?.release(); mediaPlayer = null } catch(e:Exception){}
            audioTrack?.pause()
            audioTrack?.flush()'''
safe_replace(old_reset, new_reset, "Reset Logic")

with codecs.open(p, 'w', 'utf-8') as f:
    f.write(t)
print("All done!")
