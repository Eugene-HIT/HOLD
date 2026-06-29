import re

kt_path = 'app/src/main/java/com/example/myapplication/MainActivity.kt'
with open(kt_path, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('tag = "task_cb_$completedTasks"', 'tag = "task_cb_$i"')

with open(kt_path, 'w', encoding='utf-8') as f:
    f.write(text)
print("Tag init fixed!")
