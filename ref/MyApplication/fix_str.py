# -*- coding: utf-8 -*-
import re

file_path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(file_path, 'r', encoding='utf-8') as file:
    content = file.read()

content = content.replace("str(e)", "e.message")

with open(file_path, 'w', encoding='utf-8') as file:
    file.write(content)
