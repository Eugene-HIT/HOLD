import sys

with open(r'd:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'r', encoding='utf-8') as f:
    current = f.read()

try:
    with open(r'd:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.backup.txt', 'r', encoding='utf-16') as f:
        backup = f.read()
except Exception as e:
    print(e)
    with open(r'd:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.backup.txt', 'r', encoding='utf-8', errors='ignore') as f:
        backup = f.read()


print("Current size chars:", len(current))
print("Backup size chars:", len(backup))
