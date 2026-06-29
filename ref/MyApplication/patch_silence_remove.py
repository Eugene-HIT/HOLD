# -*- coding: utf-8 -*-
with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. 0x02 branch
old_0x02 = '''                    if (data[0].toInt() == 0x02) {
                        isHardwarePtt = true
                        ++currentTurnId
                        isInterrupted = true
                        isAIThinking = false'''

new_0x02 = '''                    if (data[0].toInt() == 0x02) {
                        isHardwarePtt = true
                        ++currentTurnId
                        isInterrupted = true
                        isAIThinking = false
                        silenceRunnable?.let { silenceHandler.removeCallbacks(it) }'''

text = text.replace(old_0x02, new_0x02)

# 2. startPttRecording
old_ptt = '''        android.util.Log.i("AI_DEBUG", "User Pressed PTT! Interrupting AI.")
        ++currentTurnId
        isInterrupted = true
        try { mediaPlayer?.setOnCompletionListener(null); mediaPlayer?.stop(); mediaPlayer?.reset() } catch (e: Exception) {}'''

new_ptt = '''        android.util.Log.i("AI_DEBUG", "User Pressed PTT! Interrupting AI.")
        ++currentTurnId
        isInterrupted = true
        silenceRunnable?.let { silenceHandler.removeCallbacks(it) }
        try { mediaPlayer?.setOnCompletionListener(null); mediaPlayer?.stop(); mediaPlayer?.reset() } catch (e: Exception) {}'''

text = text.replace(old_ptt, new_ptt)

with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'w', encoding='utf-8') as f:
    f.write(text)

print("Patch applied for silence clearing")
