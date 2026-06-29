import sys

with open(r'd:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.backup.txt', 'rb') as f:
    raw = f.read()

try:
    text = raw.decode('utf-16')
except Exception:
    text = raw.decode('utf-8', errors='ignore')

lines = text.split('\n')
for i, line in enumerate(lines):
    if 'fun onCreate' in line:
        for j in range(i, i+150):
            if j < len(lines):
                print(str(j) + ": " + lines[j])
        break
