# -*- coding: utf-8 -*-
with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'r', encoding='utf-8') as f:
    text = f.read()

old_block = '''                        if (stepsArr != null) {
                            for (i in 0 until stepsArr.length()) stepsList.add(stepsArr.getString(i))
                        }

                        runOnUiThread {'''

new_block = '''                        if (stepsArr != null) {
                            for (i in 0 until stepsArr.length()) stepsList.add(stepsArr.getString(i))
                        }

                        // 🌟 新增 6：把大姐姐的回复和拆解的任务发给小程序！
                        syncDialogueToCloud(userText, finalReply, stepsList)

                        runOnUiThread {'''

if old_block in text and 'syncDialogueToCloud(userText, finalReply, stepsList)' not in text:
    text = text.replace(old_block, new_block)
    with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Injected 6 (LLM trigger) successfully!")
else:
    print("Injection 6 missed or already injected.")
