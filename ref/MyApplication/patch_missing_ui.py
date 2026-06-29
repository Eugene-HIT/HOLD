# -*- coding: utf-8 -*-
import codecs
import re

path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with codecs.open(path, 'r', 'utf-8') as f:
    text = f.read()

# Add lateinits
text = text.replace(
    'private lateinit var tvAiReply: TextView',
    'private lateinit var tvAiReply: TextView\n    private lateinit var tvUserTask: TextView\n    private lateinit var tvUserState: TextView\n    private lateinit var tvActionSteps: TextView'
)

# Add findViewByIds
text = text.replace(
    'tvAiReply = findViewById(R.id.tvAiReply)',
    'tvAiReply = findViewById(R.id.tvAiReply)\n        tvUserTask = findViewById(R.id.tvUserTask)\n        tvUserState = findViewById(R.id.tvUserState)\n        tvActionSteps = findViewById(R.id.tvActionSteps)'
)

# Update UI elements in STT and LLM Callbacks
# 1. Update tvUserState and tvUserTask when STT finishes
text = re.sub(
    r'(runOnUiThread \{ tvUserVoice\.text = "\? " \+ finalStr; tvAiStatus\.text = "🚀 STT成功，呼叫智谱大\?.." \})',
    r'\1\n                        runOnUiThread { tvUserTask.text = "目标：" + finalStr; tvUserState.text = "状态：Gulu 正在拆解任务..." }',
    text
)

# 2. Update tvActionSteps when steps are extracted
text = re.sub(
    r'(syncDialogueToCloud\(userText, replyText, stepsList\))',
    r'\1\n                    runOnUiThread {\n                        tvActionSteps.text = "步骤：\\n" + stepsList.joinToString("\\n")\n                        tvUserState.text = "状态：正在执行任务"\n                    }',
    text
)


with codecs.open(path, 'w', 'utf-8') as f:
    f.write(text)

print("UI patches applied.")
