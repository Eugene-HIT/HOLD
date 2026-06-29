import re

with open(r'd:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.backup.txt', 'r', encoding='utf-16') as f:
    backup = f.read()

classes = re.findall(r'data class HelpRequest.*?\}', backup, re.DOTALL)
print("Found HelpRequest:", len(classes))
if classes: print(classes[0][:200])

pool_methods = re.findall(r'(private fun refreshPoolUI.*?)(?=\n\s*private fun|\Z)', backup, re.DOTALL)
print("Found pool_methods:", len(pool_methods))
if pool_methods: print(pool_methods[0][:200])

