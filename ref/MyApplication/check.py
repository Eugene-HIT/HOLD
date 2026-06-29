# -*- coding: utf-8 -*-
with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if "override fun onDescriptorWrite" in line:
        for j in range(i, i+40):
            if j < len(lines):
                print(f"{j}: {lines[j].strip()}")
        break
