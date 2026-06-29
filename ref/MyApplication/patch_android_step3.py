kt_path = 'D:/ADHD/MyApplication/app/src/main/java/com/example/myapplication/MainActivity.kt'
with open(kt_path, 'r', encoding='utf-8') as f:
    kt_code = f.read()

cmd_handler_block = '''} else if (uuid == CMD_CHAR_UUID) {
                    if (data.isNotEmpty()) {
                        if (data[0].toInt() == 0x02) {
                            android.util.Log.i("AI_DEBUG", "HARDWARE LONG PRESS INTERRUPT")
                            isInterrupted = true
                            isPlayingAudio = false
                            isAIThinking = false
                            try { audioTrack?.pause(); audioTrack?.flush() } catch (e: Exception) {}
                            try { aliyunWebSocket?.cancel() } catch (e: Exception) {}
                            writeSemaphore.release(100) // free TTS stream lock

                            runOnUiThread { tvAiStatus.text = "🚫已打断AI，重新倾听中..." }
                            isRecordingLocal = true
                            audioBufferQueue.clear()
                        } else if (data[0].toInt() == 0x03) {
                            android.util.Log.i("AI_DEBUG", "HARDWARE PTT RELEASE - EOF")
                            if (isRecordingLocal) {
                                isRecordingLocal = false
                                isAIThinking = true
                                playbackBuffer.reset()
                                silenceRunnable?.let { silenceHandler.removeCallbacks(it) }
                                runOnUiThread { tvAiStatus.text = "打包上传音频推给 STT..." }
                                processAndUploadAudio()
                            }
                        }
                    }
              '''
kt_code = kt_code.replace('} else if (uuid == MIC_AUDIO_CHAR_UUID) {', cmd_handler_block + '} else if (uuid == MIC_AUDIO_CHAR_UUID) {')

with open(kt_path, 'w', encoding='utf-8') as f:
    f.write(kt_code)
print("Step 3 complete!")