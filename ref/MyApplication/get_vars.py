import re

with open(r'd:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.backup.txt', 'r', encoding='utf-16') as f:
    text = f.read()

vars = re.findall(r'(    data class HelpRequest.*?)(?=\n    override fun onCreate)', text, re.DOTALL)
if vars:
    print(vars[0][:2000])

