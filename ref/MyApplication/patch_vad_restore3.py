# -*- coding: utf-8 -*-
import re

with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'r', encoding='utf-8') as f:
    text = f.read()

old_vad_regex = r'// 🌟 【完美恢复】插入打断逻辑 1：Voice Interrupt \(边说边打断\).*?if \(interruptFrames > 0\) interruptFrames--\s*\}\s*\}'

new_vad = '''                // 2. 16-bit VAD AI Logic
                if (!isAIThinking && mediaPlayer?.isPlaying != true) {
                    var maxEnergy = 0
                    val shortBuffer = java.nio.ByteBuffer.wrap(data).order(java.nio.ByteOrder.LITTLE_ENDIAN).asShortBuffer()
                    while (shortBuffer.hasRemaining()) {
                        val energy = Math.abs(shortBuffer.get().toInt())
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

if re.search(old_vad_regex, text, flags=re.DOTALL):
    text = re.sub(old_vad_regex, new_vad, text, flags=re.DOTALL)
    with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'w', encoding='utf-8') as f:
        f.write(text)
    print("VAD completely Restored via regex!!")
else:
    print("Regex failed again!")
