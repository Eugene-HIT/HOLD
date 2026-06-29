import sys

with open(r'd:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix the silence constraint logic:
# When isAIThinking is true, incoming mic data should be dropped entirely, not added to queue.
target_mic = '''                    if (uuid == MIC_AUDIO_CHAR_UUID) {
                        if (isPlayingAudio && !isAIThinking) {
                            playbackBuffer.write(data)'''

# Wait, in processAndUploadAudio and other chunks we need to find where audioBufferQueue.add(data) happens
