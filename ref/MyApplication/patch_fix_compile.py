# -*- coding: utf-8 -*-
import codecs
import re

path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with codecs.open(path, 'r', 'utf-8') as f:
    text = f.read()

# Fix line 456
bad_line = '''callLLMForReply("系统指令：你的系统刚刚启动！请用一句非常简短、随和的口语向用户主动打招呼（比如问接下来干点啥）。注意：尽管这是打招呼，你也必须严格按照系统提示词的纯JSON格式返回！你可以把 target 和 state 填为 '无'，把 steps 填为 []，只在 reply 字段里写这句打招呼的话。绝对不能直接返回纯文本！"，比如直接问现在要做什么？或接下来我们干点啥？。绝对不要出现拆解任务、系统指令、好的等书面或AI感的话。")'''
fixed_line = '''callLLMForReply("系统指令：你的系统刚刚启动！请用一句非常简短、随和的口语向用户主动打招呼（比如问接下来干点啥）。注意：尽管这是打招呼，你也必须严格按照系统提示词的纯JSON格式返回！你可以把 target 和 state 填为 '无'，把 steps 填为 []，只在 reply 字段里写这句打招呼的话。绝对不能直接返回纯文本！")'''
if bad_line in text:
    text = text.replace(bad_line, fixed_line)

# Fix line 847: MediaType.parse is deprecated, use "application/json".toMediaTypeOrNull()
dep1 = 'okhttp3.MediaType.parse("application/json")'
fixed1 = '"application/json".toMediaTypeOrNull()'
text = text.replace(dep1, fixed1)

# Fix line 862: response.body()?.string() -> response.body?.string()
dep2 = 'response.body()?.string()'
fixed2 = 'response.body?.string()'
text = text.replace(dep2, fixed2)

# Fix escape sequences
dep3 = 'replyText.take(50).replace("\\\\n", " ")'
fixed3 = 'replyText.take(50).replace("\\n", " ")'
text = text.replace(dep3, fixed3)

dep4 = 'joinToString("\\\\n")'
fixed4 = 'joinToString("\\n")'
text = text.replace(dep4, fixed4)

# One more place
dep5 = 'replyText.split("\\\\n")'
fixed5 = 'replyText.split("\\n")'
text = text.replace(dep5, fixed5)

dep6 = 'tvActionSteps.text = "步骤：\\\\n" + stepStr'
fixed6 = 'tvActionSteps.text = "步骤：\\n" + stepStr'
text = text.replace(dep6, fixed6)

dep7 = 'tvActionSteps.text = "步骤：\\\\n(无)"'
fixed7 = 'tvActionSteps.text = "步骤：\\n(无)"'
text = text.replace(dep7, fixed7)

with codecs.open(path, 'w', 'utf-8') as f:
    f.write(text)

