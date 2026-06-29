# -*- coding: utf-8 -*-
with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'r', encoding='utf-8') as f:
    text = f.read()

old_0x02 = '''                    if (data[0].toInt() == 0x02) {
                        ++currentTurnId
                        isInterrupted = true'''

new_0x02 = '''                    if (data[0].toInt() == 0x02) {
                        isHardwarePtt = true
                        ++currentTurnId
                        isInterrupted = true'''

if old_0x02 in text:
    text = text.replace(old_0x02, new_0x02)
    with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'w', encoding='utf-8') as f:
        f.write(text)
    print("0x02 patched successfully!")
else:
    print("Could not find exact old_0x02 string.")
