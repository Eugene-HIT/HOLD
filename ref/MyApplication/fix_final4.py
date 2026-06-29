import re

kt_path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(kt_path, 'r', encoding='utf-8') as f:
    text = f.read()

text = re.sub(r'val interp = leftVal \+ fraction \* \(rightVal - leftVal\)\s*var v = interp\.toInt\(\)',
              'val interp = leftVal + fraction * (rightVal - leftVal)\n                            var v = (interp * 0.35).toInt()',
              text)

with open(kt_path, 'w', encoding='utf-8') as f:
    f.write(text)
print("Regex replaced!")
