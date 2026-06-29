# -*- coding: utf-8 -*-
import codecs

path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with codecs.open(path, 'r', 'utf-8') as f:
    text = f.read()

bad_str = 'okhttp3.MediaType.Companion.toMediaTypeOrNull("application/json; charset=utf-8")'
fixed_str = '"application/json; charset=utf-8".toMediaTypeOrNull()'

text = text.replace(bad_str, fixed_str)

with codecs.open(path, 'w', 'utf-8') as f:
    f.write(text)

print("FIXED OKHTTP MEDIA TYPE!")
