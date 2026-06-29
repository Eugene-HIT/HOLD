import re
with open(r'd:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'r', encoding='utf-8') as f:
    text = f.read()

funcs = re.findall(r'fun \w+\(', text)
print(funcs)
