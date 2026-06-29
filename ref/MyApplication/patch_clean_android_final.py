import re

kt_path = 'D:/ADHD/MyApplication/app/src/main/java/com/example/myapplication/MainActivity.kt'
with open(kt_path, 'r', encoding='utf-8') as f:
    kt_code = f.read()

# 1. REMOVE the duplicated CMD_CHAR_UUID block entirely and rewrite it cleanly.
# Find the start of the first } else if (uuid == CMD_CHAR_UUID) { 
# and remove everything up to } else if (uuid == MIC_AUDIO_CHAR_UUID) {
start_str = '} else if (uuid == CMD_CHAR_UUID) {'
end_str = '} else if (uuid == MIC_AUDIO_CHAR_UUID) {'

start_idx = kt_code.find(start_str)
end_idx = kt_code.rfind(end_str) # To remove all duplicates if any

if start_idx != -1 and end_idx != -1:
    kt_code = kt_code[:start_idx] + '} else if (uuid == MIC_AUDIO_CHAR_UUID) {' + kt_code[end_idx + len(end_str):]
else:
    print("Could not find CMD or MIC UUID blocks to scrub.")

# Now clean insert before MIC_AUDIO_CHAR_UUID
cmd_block = '''} else if (uuid == CMD_CHAR_UUID) {
                    if (data.isNotEmpty()) {
                        if (data[0].toInt() == 0x02) {
                            android.util.Log.i("AI_DEBUG", "HARDWARE LONG PRESS INTERRUPT")
                            isInterrupted = true
                            isAIThinking = false
                            try { audioTrack?.pause(); audioTrack?.flush() } catch (e: Exception) {}
                            try { mediaPlayer?.stop(); mediaPlayer?.reset() } catch (e: Exception) {}
                            try { aliyunWebSocket?.cancel() } catch (e: Exception) {}
                            writeSemaphore.release(100) // free TTS stream lock

                            runOnUiThread { tvAiStatus.text = "🚫 已打断AI，等待你讲话..." }
                            isRecordingLocal = true
                            audioBufferQueue.clear()
                            silenceRunnable?.let { silenceHandler.removeCallbacks(it) }
                        } else if (data[0].toInt() == 0x03) {
                            android.util.Log.i("AI_DEBUG", "HARDWARE PTT RELEASE - EOF")
                            if (isRecordingLocal) {
                                isRecordingLocal = false
                                isAIThinking = true
                                playbackBuffer.reset()
                                runOnUiThread { tvAiStatus.text = "打包上传音频推给 STT..." }
                                processAndUploadAudio()
                            }
                        }
                    }
                '''
kt_code = kt_code.replace('} else if (uuid == MIC_AUDIO_CHAR_UUID) {', cmd_block + '} else if (uuid == MIC_AUDIO_CHAR_UUID) {')

# 2. REMOVE VAD (maxEnergy > 800) inside MIC_AUDIO_CHAR_UUID
vad_start_str = 'if (!isAIThinking) {'
vad_end_str = 'val now = System.currentTimeMillis()'

v_s_idx = kt_code.find(vad_start_str)
v_e_idx = kt_code.find(vad_end_str, v_s_idx)

if v_s_idx != -1 and v_e_idx != -1:
    clean_vad = '''if (!isAIThinking && isRecordingLocal) {
                      audioBufferQueue.add(data)
                  }
                  
                  '''
    kt_code = kt_code[:v_s_idx] + clean_vad + kt_code[v_e_idx:]
else:
    print("Could not find VAD block to replace.")

with open(kt_path, 'w', encoding='utf-8') as f:
    f.write(kt_code)
print("Android Push-To-Talk logic and Audio interrupts successfully updated!")