import sys

with open(r'd:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'r', encoding='utf-8') as f:
    current = f.read()

with open(r'd:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.backup.txt', 'r', encoding='utf-8') as f:
    backup = f.read()

print("Current size:", len(current))
print("Backup size:", len(backup))
