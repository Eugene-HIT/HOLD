import re

with open(r'd:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.backup.txt', 'r', encoding='utf-16') as f:
    text = f.read()

# Let's extract renderPool, reparentViews, buildRoundRect
methods = re.findall(r'(    private fun reparentViews.*?)(?=\n    private fun |\Z)', text, re.DOTALL)
for m in methods:
    print(m[:100])
