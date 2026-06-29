import re

kt_path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(kt_path, 'r', encoding='utf-8', errors='ignore') as f:
    kt_content = f.read()

# Fix the reparentViews(true) missing issue
kt_content = re.sub(
    r'tvDetailTask\.text = item\.task\s+helpDetailView\.visibility = android\.view\.View\.VISIBLE\s*\}',
    r'tvDetailTask.text = item.task\n                      helpDetailView.visibility = android.view.View.VISIBLE\n                      reparentViews(true)\n                  }',
    kt_content
)

with open(kt_path, 'w', encoding='utf-8') as f:
    f.write(kt_content)
