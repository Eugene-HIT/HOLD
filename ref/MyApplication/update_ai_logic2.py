import sys

with open(r'd:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'r', encoding='utf-8') as f:
    text = f.read()

target = '''                          poolItems.add(0, HelpRequest(name = "Anny", task = helpTaskStr))
                          renderPool()'''
new = '''                          poolItems.add(0, HelpRequest(name = "Anny", task = helpTaskStr))
                          renderPool()
                          runOnUiThread { tabPool.performClick() }'''
text = text.replace(target, new)
with open(r'd:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'w', encoding='utf-8') as f:
    f.write(text)
