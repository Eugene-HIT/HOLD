# -*- coding: utf-8 -*-
with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'r', encoding='utf-8') as f:
    text = f.read()

import re

lines = text.split('\n')
new_lines = []

for line in lines:
    if "mediaPlayer?.stop()" in line or "mediaPlayer?.release()" in line or "mediaPlayer = null" in line or "audioTrack?.pause()" in line or "audioTrack?.flush()" in line:
        continue
    new_lines.append(line)

with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))
print("SUCCESS CLEAN 6")
