import re

file_path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(file_path, 'r', encoding='utf-8') as file:
    content = file.read()

content = content.replace(', Manifest.permission.RECORD_AUDIO, Manifest.permission.RECORD_AUDIO)', ',\n            Manifest.permission.RECORD_AUDIO\n        )')

with open(file_path, 'w', encoding='utf-8') as file:
    file.write(content)
