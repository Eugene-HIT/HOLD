import re

kt_path = 'app/src/main/java/com/example/myapplication/MainActivity.kt'
with open(kt_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Fix the template logic
text = text.replace('"task_cb_"', '"task_cb_$completedTasks"')

with open(kt_path, 'w', encoding='utf-8') as f:
    f.write(text)
print("Fix applied!")
