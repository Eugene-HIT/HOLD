import re

kt_path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(kt_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Remove duplicate declarations
# The pattern might match the multiple declarations
text = re.sub(r'(private lateinit var tvActionSteps: TextView\s*)private lateinit var tvUserTask: TextView\s*private lateinit var tvUserState: TextView\s*private lateinit var tvActionSteps: TextView', r'\1', text)

# Remove duplicate initializations
text = re.sub(r'(tvActionSteps = findViewById\(R\.id\.tvActionSteps\)\s*)tvUserTask = findViewById\(R\.id\.tvUserTask\)\s*tvUserState = findViewById\(R\.id\.tvUserState\)\s*tvActionSteps = findViewById\(R\.id\.tvActionSteps\)', r'\1', text)

with open(kt_path, 'w', encoding='utf-8') as f:
    f.write(text)

print("Duplicates removed.")
