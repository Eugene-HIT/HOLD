# -*- coding: utf-8 -*-
import re

with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'r', encoding='utf-8') as f:
    t = f.read()

# Fix string interpolation for variables that were interpreted early by powershell instead of being treated as literal text
old_str = r'historyLog\.add\(Pair\(userText, "\{\\"target\\":\\"\\", \\"state\\":\\"\\", \\"reply\\":\\"\\"\}"\)\)'
new_str = r'historyLog.add(Pair(userText, "{\\"target\\":\\"\\", \\"state\\":\\"\\", \\"reply\\":\\"\\"}"))'

t = re.sub(old_str, new_str.replace('\n', '\r\n'), t)

with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'w', encoding='utf-8') as f:
    f.write(t)
print("Finished!")
