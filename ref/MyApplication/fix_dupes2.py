# -*- coding: utf-8 -*-
with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'r', encoding='utf-8') as f:
    text = f.read()

import re

lines = text.split('\n')
new_lines = []
seen_vars = set()

for line in lines:
    m = re.match(r'\s*private lateinit var (\w+):.*', line)
    if m:
        v = m.group(1)
        if v in seen_vars:
            continue
        seen_vars.add(v)
    new_lines.append(line)

with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))
print("SUCCESS DUPES CLEAN")
