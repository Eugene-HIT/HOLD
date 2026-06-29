# -*- coding: utf-8 -*-
import re

with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'r', encoding='utf-8') as f:
    t = f.read()

# Try explicit replace correctly
target_text = 'historyLog.add(Pair(userText, "{\\"target\\":\\"\\", \\"state\\":\\"\\", \\"reply\\":\\"\\"}"))'
new_text = 'historyLog.add(Pair(userText, "{\\"target\\":\\"\\", \\"state\\":\\"\\", \\"reply\\":\\"\\"}"))'

t = t.replace(target_text, new_text)

with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'w', encoding='utf-8') as f:
    f.write(t)
    
print("Replaced!")
