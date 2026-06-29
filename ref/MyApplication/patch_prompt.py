# -*- coding: utf-8 -*-
import re

file_path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the greeting prompt
old_prompt = "系统指令：请向用户打招呼，并直接询问现在想要拆解什么任务。语言简短自然，禁止出现像'好的'这种系统性回复，不要提及'开机'、'设备'等字眼。"
new_prompt = "系统指令：请用一句非常简短、随和的口语向用户打招呼，比如直接问现在要做什么？或接下来我们干点啥？。绝对不要出现拆解任务、系统指令、好的等书面或AI感的话。"

content = content.replace(old_prompt, new_prompt)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
