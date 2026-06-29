import re

path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("private lateinit var tabPool: TextView", "private lateinit var tabPool: android.widget.Button")
text = text.replace("private lateinit var tabDebug: TextView", "private lateinit var tabDebug: android.widget.Button")

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
print("done!")
