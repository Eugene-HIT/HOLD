# -*- coding: utf-8 -*-
import re
with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'r', encoding='utf-8') as f:
    t = f.read()

t = re.sub(r'historyLog\.add\(Pair\(userText, "\{\\"target\\":\\"\w?\\", \\"state\\":\\"\w?\\", \\"reply\\":\\"\w?\\"\}"\)\)', 
    r'historyLog.add(Pair(userText, "{\\"target\\":\\"qtarget\\", \\"state\\":\\"qstate\\", \\"reply\\":\\"qfinalReply\\"}"))'.replace('q', '$'), t)
    
t = t.replace('historyLog.add(Pair(userText, "{\\"target\\":\\"\\", \\"state\\":\\"\\", \\"reply\\":\\"\\"}"))',
    r'historyLog.add(Pair(userText, "{\\"target\\":\\"qtarget\\", \\"state\\":\\"qstate\\", \\"reply\\":\\"qfinalReply\\"}"))'.replace('q', '$'))

with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'w', encoding='utf-8') as f:
    f.write(t)
print("Finished!!")
