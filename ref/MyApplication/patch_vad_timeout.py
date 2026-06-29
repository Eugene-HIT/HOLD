import re

file_path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix VAD trigger race condition and increase timeout to 2.5s
old_vad = '''                          silenceRunnable?.let { silenceHandler.removeCallbacks(it) }
                          silenceRunnable = Runnable {
                              Log.i("AI_DEBUG", "VAD trigger silence end")
                              isRecordingLocal = false
                              isAIThinking = true
                              playbackBuffer.reset()
                              audioTrack?.pause()
                              audioTrack?.flush()
                              if (isPlayingAudio) audioTrack?.play()
                              runOnUiThread { tvAiStatus.text = "?打包上传音频推给 STT ?.." }
                              processAndUploadAudio()
                          }
                          silenceHandler.postDelayed(silenceRunnable!!, 1500)'''

new_vad = '''                          silenceRunnable?.let { silenceHandler.removeCallbacks(it) }
                          silenceRunnable = Runnable {
                              if (isAIThinking) return@Runnable // Prevents race condition double-uploads
                              Log.i("AI_DEBUG", "VAD trigger silence end")
                              isRecordingLocal = false
                              isAIThinking = true
                              playbackBuffer.reset()
                              audioTrack?.pause()
                              audioTrack?.flush()
                              if (isPlayingAudio) audioTrack?.play()
                              runOnUiThread { tvAiStatus.text = "?打包上传音频推给 STT ?.." }
                              processAndUploadAudio()
                          }
                          silenceHandler.postDelayed(silenceRunnable!!, 2500)'''

# Using regex to ignore special chars like ?
content = re.sub(r'silenceRunnable\?\.let \{ silenceHandler\.removeCallbacks\(it\) \}\s*silenceRunnable = Runnable \{\s*Log\.i\("AI_DEBUG", "VAD trigger silence end"\)\s*isRecordingLocal = false\s*isAIThinking = true\s*playbackBuffer\.reset\(\)\s*audioTrack\?\.pause\(\)\s*audioTrack\?\.flush\(\)\s*if \(isPlayingAudio\) audioTrack\?\.play\(\)\s*runOnUiThread \{ tvAiStatus\.text = "[^"]*" \}\s*processAndUploadAudio\(\)\s*\}\s*silenceHandler\.postDelayed\(silenceRunnable!!, 1500\)', 
'''                          silenceRunnable?.let { silenceHandler.removeCallbacks(it) }
                          silenceRunnable = Runnable {
                              if (isAIThinking) return@Runnable
                              Log.i("AI_DEBUG", "VAD trigger silence end")
                              isRecordingLocal = false
                              isAIThinking = true
                              playbackBuffer.reset()
                              audioTrack?.pause()
                              audioTrack?.flush()
                              if (isPlayingAudio) audioTrack?.play()
                              runOnUiThread { tvAiStatus.text = "打包上传音频推给 STT..." }
                              processAndUploadAudio()
                          }
                          silenceHandler.postDelayed(silenceRunnable!!, 2500)''', content)

# Update the log print
content = content.replace('runOnUiThread { tvAiStatus.text = "?正在录音... (安静1.5秒发?" }', 'runOnUiThread { tvAiStatus.text = " 正在录音... (安静2.5秒发送)" }')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Patch logic applied")