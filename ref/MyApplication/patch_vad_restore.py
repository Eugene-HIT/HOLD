# -*- coding: utf-8 -*-
with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'r', encoding='utf-8') as f:
    t = f.read()

old_vad = '''                // 🌟 【完美恢复】插入打断逻辑 1：Voice Interrupt (边说边打断)  
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
                            android.util.Log.i("AI_DEBUG", "VOICE INTERRUPT TRIGGERED!")
                            ++currentTurnId
                            isInterrupted = true
                            try { mediaPlayer?.setOnCompletionListener(null); mediaPlayer?.stop(); mediaPlayer?.reset() } catch(e:Exception){}
                            try { audioTrack?.pause(); audioTrack?.flush() } catch(e:Exception){}
                            isPlayingAudio = false
                            isAIThinking = false
                            try { aliyunWebSocket?.cancel() } catch (e: Exception) {}

                            runOnUiThread { tvAiStatus.text = "🚫已打断AI，重新 倾听中..." }

                            isRecordingLocal = true
                            audioBufferQueue.clear()
                            interruptFrames = 0
                        }
                    } else {
                        if (interruptFrames > 0) interruptFrames--
                    }
                }'''

new_vad = '''                // 2. 16-bit VAD AI Logic
                if (!isAIThinking) {
                    var maxEnergy = 0
                    val shortBuffer = java.nio.ByteBuffer.wrap(data).order(java.nio.ByteOrder.LITTLE_ENDIAN).asShortBuffer()
                    while (shortBuffer.hasRemaining()) {
                        val energy = Math.abs(shortBuffer.get().toInt() ?: 0)
                        if (energy > maxEnergy) maxEnergy = energy
                    }

                    if (maxEnergy > 2000) {
                        if (!isRecordingLocal) {
                            android.util.Log.i("AI_DEBUG", "VAD trigger start")
                            isRecordingLocal = true
                            runOnUiThread { tvAiStatus.text = "🎙️正在录音... (安静1.5秒发送)" }
                        }
                        audioBufferQueue.add(data)

                        silenceRunnable?.let { silenceHandler.removeCallbacks(it) }
                        silenceRunnable = Runnable {
                            android.util.Log.i("AI_DEBUG", "VAD trigger silence end")
                            isRecordingLocal = false
                            isAIThinking = true
                            playbackBuffer.reset()
                            audioTrack?.pause()
                            audioTrack?.flush()
                            if (isPlayingAudio) audioTrack?.play()
                            runOnUiThread { tvAiStatus.text = "🚀打包上传音频推给STT..." }
                            processAndUploadAudio()
                        }
                        silenceHandler.postDelayed(silenceRunnable!!, 1500)
                    } else {
                        if (isRecordingLocal) {
                            audioBufferQueue.add(data)
                        }
                    }
                }'''

if old_vad in t:
    t = t.replace(old_vad, new_vad)
    with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'w', encoding='utf-8') as f:
        f.write(t)
    print("VAD Restored!")
else:
    print("Could not find old VAD logic to replace!")
