import re

kt_path = 'D:/ADHD/MyApplication/app/src/main/java/com/example/myapplication/MainActivity.kt'
with open(kt_path, 'r', encoding='utf-8') as f:
    kt_code = f.read()

# 1. Add variables
if 'var isInterrupted = false' not in kt_code:
    kt_code = kt_code.replace(
        'private var isAIThinking = false',
        'private var isAIThinking = false\n    @Volatile private var isInterrupted = false\n    private var interruptFrames = 0'
    )

# 2. Add interrupt break condition in streamPcmToEsp32
if 'if (isInterrupted) break' not in kt_code:
    kt_code = kt_code.replace(
        'while (offset < audioBytes.size) {',
        'while (offset < audioBytes.size) {\n                    if (isInterrupted) break'
    )

# 3. Reset isInterrupted at the beginning of streamPcmToEsp32
if '@Volatile private var isInterrupted' in kt_code and 'isInterrupted = false' not in kt_code.split('streamPcmToEsp32')[1][:200]:
    kt_code = kt_code.replace(
        'writeSemaphore.release() // Allow the first chunk to proceed immediately',
        'isInterrupted = false\n                interruptFrames = 0\n                writeSemaphore.release() // Allow the first chunk to proceed immediately'
    )

# 4. Insert Interrupt VAD logic in onCharacteristicChanged
interrupt_logic = '''                // 1.5 Interrupt Logic (User talks while AI plays/thinks)
                if (isAIThinking || isPlayingAudio) {
                    var maxEnergy = 0
                    val shortBuffer = java.nio.ByteBuffer.wrap(data).order(java.nio.ByteOrder.LITTLE_ENDIAN).asShortBuffer()
                    while (shortBuffer.hasRemaining()) {
                        val energy = Math.abs(shortBuffer.get().toInt())
                        if (energy > maxEnergy) maxEnergy = energy
                    }
                    if (maxEnergy > 2000) { // Slightly higher threshold to avoid self-echo triggering (TODO: AEC)
                        interruptFrames++
                        if (interruptFrames > 4) { // 4 frames of loud noise
                            android.util.Log.i("AI_DEBUG", "INTERRUPT TRIGGERED!")
                            isInterrupted = true
                            isPlayingAudio = false
                            isAIThinking = false
                            writeSemaphore.release(100) // free TTS stream lock
                            try { audioTrack?.pause(); audioTrack?.flush() } catch (e: Exception) {}
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
'''

if '// 1.5 Interrupt Logic' not in kt_code:
    kt_code = kt_code.replace(
        '                // 2. 16-bit VAD AI Logic',
        interrupt_logic + '\n                // 2. 16-bit VAD AI Logic'
    )

with open(kt_path, 'w', encoding='utf-8') as f:
    f.write(kt_code)

print("PATCH APPLIED")