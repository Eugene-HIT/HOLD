kt_path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(kt_path, 'r', encoding='utf-8') as f:
    text = f.read()

import re
text = re.sub(r'android\.util\.Log\.i\("AI_DEBUG", "Advanced Downsampling TTS from [^"]*"\)',
              r'android.util.Log.i("AI_DEBUG", "Advanced Downsampling TTS from " + inRate + " to " + targetRate)',
              text)

with open(kt_path, 'w', encoding='utf-8') as f:
    f.write(text)
