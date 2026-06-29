# -*- coding: utf-8 -*-
import re

file_path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# I will use regex because whitespace may differ
content = re.sub(
    r'(runOnUiThread \{ tvStatus\.text = "Camera Data" \}[\s\S]*?\})',
    r'\1\n                // Trigger auto greet when camera descriptor is configured\n                runOnUiThread { tvStatus.text = "设备就绪！AI 准备中..." }\n                isAIThinking = true\n                historyLog.clear()\n                callLLMForReply("系统指令：新设备已连接。请向用户简短打招呼，问他想要做什么任务。注意：这只是开场，请直接作为助手开口，不要回复好的等废话。")\n',
    content
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
