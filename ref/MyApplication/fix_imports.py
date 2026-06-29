# -*- coding: utf-8 -*-
with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'r', encoding='utf-8') as f:
    text = f.read()

import re

# Fix HelpRequest multiple definition
if text.count('data class HelpRequest') > 1:
    print('Found multiple HelpRequest')
    parts = text.split('data class HelpRequest')
    text = parts[0] + 'data class HelpRequest' + parts[1]
    
# Clean duplicate variables in class
vars_to_clean = ["private lateinit var tvUserTask", "private lateinit var tvUserState", "private lateinit var tvActionSteps", "private lateinit var poolView", "private lateinit var helpDetailView", "private lateinit var poolListLayout", "private lateinit var tvDetailTask", "private lateinit var taskListContainer", "private var poolItems"]

for var in vars_to_clean:
    if text.count(var) > 1:
        first = text.find(var)
        rest = text[first + len(var):].replace(var + " : TextView", "").replace(var + " : View", "").replace(var + " : LinearLayout", "").replace(var + " = mutableListOf<HelpRequest>()", "").replace(var, "")
        text = text[:first + len(var)] + rest

with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS CLEAN")
