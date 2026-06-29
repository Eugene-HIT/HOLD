import re

path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("poolItems.add(HelpRequest(\"Tom\", \"不知道要做什么，状态是迷茫\"))", "poolItems.add(HelpRequest(\"Tom\", \"不知道要做什么，状态是迷茫\"))\n        renderPool()")

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
print("done!")
