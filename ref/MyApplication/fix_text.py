# -*- coding: utf-8 -*-
import re

file_path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(file_path, 'r', encoding='utf-8') as file:
    content = file.read()

content = content.replace('"Recording..."', '"录音中..."')
content = content.replace('"Hold to Talk"', '"按住录音，松开发送"')

with open(file_path, 'w', encoding='utf-8') as file:
    file.write(content)
