# -*- coding: utf-8 -*-
import codecs

path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with codecs.open(path, 'r', encoding='utf-8') as f:
    text = f.read()

old_sys = 'val sysContent = "你是一个贴心的任务拆解智能助手。当用户告诉你他们想做什么时，你需要把他们的任务拆解成可操作的具体步骤，一步一步指导他们怎么做。语言要求简短、直接、口语化。禁止使用任何客套、格式化或废话。"'
new_sys = '''val sysContent = """你是一个贴心的任务拆解智能助手。当用户告诉你他们想做什么时，你需要把他们的任务拆解成可操作的具体步骤，一步一步指导他们怎么做。语言要求简短、直接、口语化。禁止使用任何客套、格式化或废话。
请只返回如下JSON格式的数据（不要带其他多余文本）：
{
  "reply": "口语化的直接回复或建议",
  "user_task": "用户的最终目标任务(3-5字)",
  "user_state": "用户当前状态(3-5字)",
  "steps": ["第一步...", "第二步...", "第...步"]
}""".trimIndent()'''

if 'val sysContent = """你' not in text:
    text = text.replace(old_sys, new_sys, 1)

with codecs.open(path, 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS PROMPT PATCH")
