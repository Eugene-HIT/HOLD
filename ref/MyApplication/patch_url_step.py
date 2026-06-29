# -*- coding: utf-8 -*-
with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix the URL
old_url = '"[https://open.bigmodel.cn/api/paas/v4/chat/completions](https://open.bigmodel.cn/api/paas/v4/chat/completions)"'
new_url = '"https://open.bigmodel.cn/api/paas/v4/chat/completions"'
if old_url in text:
    text = text.replace(old_url, new_url)
    print("Fixed TTS URL!")
else:
    print("Could not find TTS URL.")

# Fix the cloud sync logic
old_sync = 'syncDialogueToCloud(userText, finalReplyText, extractedSteps)'
new_sync = '''val stepsForCloud = mutableListOf<String>()
                    stepsForCloud.add("🎯 目标：" + userTask)
                    stepsForCloud.add("💡 状态：" + userState)
                    stepsForCloud.addAll(extractedSteps)
                    
                    syncDialogueToCloud(userText, finalReplyText, stepsForCloud)'''
if old_sync in text:
    text = text.replace(old_sync, new_sync)
    print("Fixed cloud sync logic!")
else:
    print("Could not find sync logic.")

with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'w', encoding='utf-8') as f:
    f.write(text)
