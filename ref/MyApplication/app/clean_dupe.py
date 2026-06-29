# -*- coding: utf-8 -*-
import re

file_path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(file_path, 'r', encoding='utf-8') as file:
    content = file.read()

# Fix duplicates in imports
content = re.sub(r'(import android\.media\.AudioRecord\nimport android\.media\.MediaRecorder\nimport java\.io\.ByteArrayOutputStream\nimport android\.view\.MotionEvent\n)+', r'\1', content)

# Fix duplicate fields
content = re.sub(r'(\s*private var pttAudioRecord: AudioRecord\? = null\s*private var isRecordingPtt = false\s*private val pttAudioBuffer = ByteArrayOutputStream\(\))+', r'\n    private var pttAudioRecord: AudioRecord? = null\n    private var isRecordingPtt = false\n    private val pttAudioBuffer = ByteArrayOutputStream()\n', content)

# Fix duplicate button logic
btn_logic = r'\s*val btnPushToTalk: Button = findViewById\(R\.id\.btnPushToTalk\)[\s\S]*?else -> false\s*\}\s*\}'
content = re.sub(btn_logic + r'(' + btn_logic + ')+', lambda m: m.group(0)[:len(m.group(0))//2], content)
# Wait, let's just find and replace using exact sting
# Actually, the quickest way to fix this is to rewrite the file by replacing everything that looks like duplicate.

with open(file_path, 'w', encoding='utf-8') as file:
    file.write(content)
