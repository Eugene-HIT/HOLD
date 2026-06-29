import sys

with open(r'd:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.backup.txt', 'r', encoding='utf-16') as f:
    text = f.read()

with open('restore.txt', 'w', encoding='utf-8') as out:
    out.write(text)
