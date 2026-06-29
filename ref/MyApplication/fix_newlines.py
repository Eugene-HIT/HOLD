import re

kt_path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(kt_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Fix literal newlines in strings
text = re.sub(r'\.append\("(.*?)\n\s*"\)', r'.append("\1\\n")', text)
text = re.sub(r'tvActionSteps\.text = "(.*?)：\n"\s*\+\s*stepsText', r'tvActionSteps.text = "\1：\\n" + stepsText', text)

with open(kt_path, 'w', encoding='utf-8') as f:
    f.write(text)

print("Kotlin newlines fixed!")
