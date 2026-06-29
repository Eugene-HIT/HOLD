# -*- coding: utf-8 -*-
with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'r', encoding='utf-8') as f:
    t = f.read()

target_text = 'historyLog.add(Pair(userText, "{\\"target\\":\\"\\", \\"state\\":\\"\\", \\"reply\\":\\"\\"}"))'
new_text = 'historyLog.add(Pair(userText, "{\\"target\\":\\"\\", \\"state\\":\\"\\", \\"reply\\":\\"\\"}"))'

with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'w', encoding='utf-8') as f:
    f.write(t.replace(target_text, new_text))
    
print("Replaced!")
