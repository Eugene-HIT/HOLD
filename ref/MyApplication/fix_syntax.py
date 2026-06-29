# -*- coding: utf-8 -*-
with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    stripped = line.strip()
    if stripped.startswith(': android.widget.TextView') or stripped.startswith(': android.widget.LinearLayout') or stripped.startswith(': TextView'):
        continue
    new_lines.append(line)

with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("SUCCESS CLEAN LINES")
