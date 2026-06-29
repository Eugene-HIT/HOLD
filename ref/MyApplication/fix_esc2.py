import re

kt_path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(kt_path, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('TTS from \\$inRate', 'TTS from $inRate')
text = text.replace('to \\$targetRate', 'to $targetRate')

with open(kt_path, 'w', encoding='utf-8') as f:
    f.write(text)
