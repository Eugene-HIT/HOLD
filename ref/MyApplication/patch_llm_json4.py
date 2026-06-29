# -*- coding: utf-8 -*-
import re

with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'r', encoding='utf-8') as f:
    t = f.read()

# Try explicit replace
t = t.replace(r'historyLog.add(Pair(userText, "{\"target\":\"\", \"state\":\"\", \"reply\":\"\"}"))', r'historyLog.add(Pair(userText, "{\"target\":\"\", \"state\":\"\", \"reply\":\"\"}"))')

with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'w', encoding='utf-8') as f:
    f.write(t)
    
print("Replaced!")
