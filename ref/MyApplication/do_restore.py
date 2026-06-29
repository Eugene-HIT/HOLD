import re

with open(r'd:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.backup.txt', 'r', encoding='utf-16') as f:
    text = f.read()

m = re.search(r'data class HelpRequest(.*?)(?=    override fun onCreate)', text, re.DOTALL)
m2 = re.search(r'    override fun onCreate\(savedInstanceState: Bundle\?\)(.*?)(?=    private fun onProgressChanged)', text, re.DOTALL)
m3 = re.search(r'(    private fun reparentViews.*?)(?=\Z)', text, re.DOTALL)

with open('restore.txt', 'w', encoding='utf-8') as out:
    if m: out.write("VARS:\n" + m.group(0) + "\n================\n")
    if m2: out.write("ONCREATE:\n" + m2.group(0) + "\n================\n")
    if m3: out.write("METHODS:\n" + m3.group(0) + "\n================\n")
