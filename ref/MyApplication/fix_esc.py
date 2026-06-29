import re

kt_path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(kt_path, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('TTS from \\ to \\', 'TTS from \ to \')

with open(kt_path, 'w', encoding='utf-8') as f:
    f.write(text)
