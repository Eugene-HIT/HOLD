# -*- coding: utf-8 -*-
with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'r', encoding='utf-8') as f:
    text = f.read()

old_decode = 'val audioBytes = Base64.decode(base64Str, Base64.DEFAULT)'
new_decode = 'val audioBytes = android.util.Base64.decode(base64Str, android.util.Base64.DEFAULT)'

if old_decode in text:
    text = text.replace(old_decode, new_decode)
    with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Fixed Base64")
else:
    print("Could not find Base64 to fix!")
