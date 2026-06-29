import sys
import re

with open(r'd:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.backup.txt', 'r', encoding='utf-16') as f:
    text = f.read()

onCreate = re.search(r'(override fun onCreate\(.*?)(\n    private fun |\n    override fun )', text, re.DOTALL)
if onCreate:
    with open('tmp_oncreate.txt', 'w', encoding='utf-8') as f:
        f.write(onCreate.group(1))
