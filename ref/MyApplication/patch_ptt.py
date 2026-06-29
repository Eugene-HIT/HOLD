# -*- coding: utf-8 -*-
import re

with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add isHardwarePtt variable
var_search = r'private var isRecordingPtt = false'
if var_search in text and 'private var isHardwarePtt' not in text:
    text = text.replace(var_search, "private var isRecordingPtt = false\n    private var isHardwarePtt = false")

# 2. Update 0x02 branch
hw_down_old = r'''if (data\[0\]\.toInt\(\) == 0x02) {
                        \+\+currentTurnId'''
hw_down_new = '''if (data[0].toInt() == 0x02) {
                        isHardwarePtt = true
                        ++currentTurnId'''
text = re.sub(hw_down_old, hw_down_new, text)

# 3. Update 0x03 branch
hw_up_old = r'''} else if \(data\[0\]\.toInt\(\) == 0x03\) \{
                        if \(isRecordingLocal\) \{'''
hw_up_new = '''} else if (data[0].toInt() == 0x03) {
                        isHardwarePtt = false
                        if (isRecordingLocal) {'''
text = re.sub(hw_up_old, hw_up_new, text)

# 4. Update resetAI
reset_old = r'''isRecordingLocal = false
            audioBufferQueue\.clear\(\)'''
reset_new = '''isRecordingLocal = false
            isHardwarePtt = false
            audioBufferQueue.clear()'''
text = re.sub(reset_old, reset_new, text)

# 5. Update VAD Block
vad_old = r'''// 2\. 16-bit VAD AI Logic
                if \(!isAIThinking && mediaPlayer\?\.isPlaying != true\) \{
                    var maxEnergy = 0
                    val shortBuffer = java\.nio\.ByteBuffer\.wrap\(data\)\.order\(java\.nio\.ByteOrder\.LITTLE_ENDIAN\)\.asShortBuffer\(\)
                    while \(shortBuffer\.hasRemaining\(\)\) \{
                        val energy = Math\.abs\(shortBuffer\.get\(\)\.toInt\(\)\)
                        if \(energy > maxEnergy\) maxEnergy = energy
                    \}

                    if \(maxEnergy > 2000\) \{
                        if \(!isRecordingLocal\) \{
                            android\.util\.Log\.i\("AI_DEBUG", "VAD trigger start"\)
                            isRecordingLocal = true
                            runOnUiThread \{ tvAiStatus\.text = "🎙️正在录音\.\.\. \(安静1\.5秒发送\)" \}
                        \}
                        audioBufferQueue\.add\(data\)

                        silenceRunnable\?\.let \{ silenceHandler\.removeCallbacks\(it\) \}
                        silenceRunnable = Runnable \{
                            android\.util\.Log\.i\("AI_DEBUG", "VAD trigger silence end"\)
                            isRecordingLocal = false
                            isAIThinking = true
                            playbackBuffer\.reset\(\)
                            audioTrack\?\.pause\(\)
                            audioTrack\?\.flush\(\)
                            if \(isPlayingAudio\) audioTrack\?\.play\(\)
                            runOnUiThread \{ tvAiStatus\.text = "🚀打包上传音频推给STT\.\.\." \}
                            processAndUploadAudio\(\)
                        \}
                        silenceHandler\.postDelayed\(silenceRunnable!!, 1500\)
                    \} else \{
                        if \(isRecordingLocal\) \{
                            audioBufferQueue\.add\(data\)
                        \}
                    \}
                \}'''

vad_new = '''// 2. 16-bit VAD AI Logic
                if (isHardwarePtt) {
                    if (isRecordingLocal) {
                        audioBufferQueue.add(data)
                    }
                } else if (isRecordingPtt) {
                    // Do nothing with BLE audio if app UI PTT is recording
                } else if (!isAIThinking && mediaPlayer?.isPlaying != true) {
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

if re.search(vad_old.replace(' ', r'\s*').replace('\n', r'\s*'), text):
    text = re.sub(vad_old.replace(' ', r'\s*').replace('\n', r'\n\s*'), vad_new.replace('\n', '\r\n'), text, flags=re.DOTALL)
    print("VAD regex ok!")
else:
    # Fallback tight replace
    text = text.replace('''// 2. 16-bit VAD AI Logic
                if (!isAIThinking && mediaPlayer?.isPlaying != true) {''', '''// 2. 16-bit VAD AI Logic
                if (isHardwarePtt) {
                    if (isRecordingLocal) {
                        audioBufferQueue.add(data)
                    }
                } else if (isRecordingPtt) {
                    // Do nothing with BLE audio if app UI PTT is recording
                } else if (!isAIThinking && mediaPlayer?.isPlaying != true) {''')
    print("VAD fallback ok!")


with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'w', encoding='utf-8') as f:
    f.write(text)

print("Patch applied.")
