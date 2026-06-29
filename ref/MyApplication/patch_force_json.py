# -*- coding: utf-8 -*-
with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'r', encoding='utf-8') as f:
    text = f.read()

old_code = '''                    syncDialogueToCloud(userText, ttsReply, stepsList)
                    runOnUiThread {
                        if (targetStr.isNotEmpty()) tvUserTask.text = "目标：" + targetStr
                        if (stateStr.isNotEmpty()) tvUserState.text = "状态：" + stateStr
                        else tvUserState.text = "状态：正在执行任务"

                        if (stepsList.isNotEmpty()) {
                            val stepStr = stepsList.mapIndexed { index, s -> "\. \" }.joinToString("\\n")
                            tvActionSteps.text = "步骤：\\n" + stepStr
                        } else {
                            tvActionSteps.text = "步骤：\\n(无)"
                        }
                        tvAiReply.text = "AI: " + ttsReply
                        tvAiStatus.text = "🔊 正在全自动生成逼真语音(TTS)..."   
                    }'''

new_code = '''                    syncDialogueToCloud(userText, ttsReply, stepsList)
                    runOnUiThread {
                        if (targetStr.isNotEmpty()) tvUserTask.text = "目标：" + targetStr
                        else tvUserTask.text = "解析未带目标，原始回复：" + replyText.take(50)
                        
                        if (stateStr.isNotEmpty()) tvUserState.text = "状态：" + stateStr
                        else tvUserState.text = "状态：正在执行任务"

                        if (stepsList.isNotEmpty()) {
                            val stepStr = stepsList.mapIndexed { index, s -> "\. \" }.joinToString("\\n")
                            tvActionSteps.text = "步骤：\\n" + stepStr
                        } else {
                            tvActionSteps.text = "步骤：\\n(无)"
                        }
                        tvAiReply.text = "AI: " + ttsReply
                        tvAiStatus.text = "🔊 正在全自动生成逼真语音(TTS)..."   
                    }'''

if old_code in text:
    text = text.replace(old_code, new_code)
    with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Patched UI overwrites")
else:
    print("Could not find old UI block")
