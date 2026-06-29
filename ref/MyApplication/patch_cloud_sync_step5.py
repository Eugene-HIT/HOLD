# -*- coding: utf-8 -*-
import re

with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'r', encoding='utf-8') as f:
    t = f.read()

# 5. callLLMForReply NLP trigger
p5_old = r'val finalReply = parsed\.optString\("reply", "好的"\)(?:\s|\r|\n)*runOnUiThread \{'
p5_new = '''val finalReply = parsed.optString("reply", "好的")
                        
                        // 🌟 新增 6：把大姐姐的回复和拆解的任务发给小程序！
                        syncDialogueToCloud(userText, finalReply, stepsList)

                        runOnUiThread {'''

if re.search(p5_old, t) and 'syncDialogueToCloud(userText, finalReply, stepsList)' not in t:
    t = re.sub(p5_old, p5_new, t)
    print("Injected 6 (LLM trigger)")
else:
    print("Could not find trigger 5. Let's see what is there.")
    match = re.search(r'val finalReply = .+', t)
    if match:
        print("Found:", match.group(0))

with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'w', encoding='utf-8') as f:
    f.write(t)
