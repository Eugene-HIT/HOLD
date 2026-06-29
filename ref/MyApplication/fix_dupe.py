# -*- coding: utf-8 -*-
with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'r', encoding='utf-8') as f:
    orig = f.read()

orig = orig.replace('    private var hasGreeted = false\n    private var hasGreeted = false', '    private var hasGreeted = false')
orig = orig.replace('                hasGreeted = false\n                hasGreeted = false', '                hasGreeted = false')

with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'w', encoding='utf-8') as f:
    f.write(orig)
