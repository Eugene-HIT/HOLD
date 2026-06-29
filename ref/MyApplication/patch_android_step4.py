kt_path = 'D:/ADHD/MyApplication/app/src/main/java/com/example/myapplication/MainActivity.kt'
with open(kt_path, 'r', encoding='utf-8') as f:
    kt_code = f.read()

start_str = "// 2. 16-bit VAD AI Logic"
end_str = "val now = System.currentTimeMillis()"

start_idx = kt_code.find(start_str)
end_idx = kt_code.find(end_str, start_idx)

new_vad = '''// 2. 16-bit VAD AI Logic
                if (!isAIThinking) {
                    var maxEnergy = 0
                    val shortBuffer = java.nio.ByteBuffer.wrap(data).order(java.nio.ByteOrder.LITTLE_ENDIAN).asShortBuffer()
                    while (shortBuffer.hasRemaining()) {
                        val energy = Math.abs(shortBuffer.get().toInt())        
                        if (energy > maxEnergy) maxEnergy = energy
                    }

                    if (isRecordingLocal) {
                        audioBufferQueue.add(data)

                        if (maxEnergy > 800) {
                            silenceRunnable?.let { silenceHandler.removeCallbacks(it) }
                            silenceRunnable = Runnable {
                                if (isAIThinking) return@Runnable
                                android.util.Log.i("AI_DEBUG", "VAD trigger silence end")
                                isRecordingLocal = false
                                isAIThinking = true
                                playbackBuffer.reset()
                                try { audioTrack?.pause(); audioTrack?.flush(); if (isPlayingAudio) audioTrack?.play() } catch (e: Exception) {}
                                runOnUiThread { tvAiStatus.text = "打包上传音频推给 STT..." }
                                processAndUploadAudio()
                            }
                            silenceHandler.postDelayed(silenceRunnable!!, 2500) 
                        }
                    }
                }

                '''
kt_code = kt_code[:start_idx] + new_vad + kt_code[end_idx:]

with open(kt_path, 'w', encoding='utf-8') as f:
    f.write(kt_code)
print("Step 4 complete!")