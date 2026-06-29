import re

kt_path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(kt_path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add variable declarations
decl_pattern = r'private lateinit var tvAiReply: TextView'
decl_repl = '''private lateinit var tvAiReply: TextView
    private lateinit var tvUserTask: TextView
    private lateinit var tvUserState: TextView
    private lateinit var tvActionSteps: TextView'''
text = re.sub(decl_pattern, decl_repl, text)

# 2. Add findViewByIds
init_pattern = r'tvAiReply = findViewById\(R\.id\.tvAiReply\)'
init_repl = '''tvAiReply = findViewById(R.id.tvAiReply)
        tvUserTask = findViewById(R.id.tvUserTask)
        tvUserState = findViewById(R.id.tvUserState)
        tvActionSteps = findViewById(R.id.tvActionSteps)'''
text = re.sub(init_pattern, init_repl, text)

with open(kt_path, 'w', encoding='utf-8') as f:
    f.write(text)

print("Kotlin UI Variables Injected!")
