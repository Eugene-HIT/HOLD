# -*- coding: utf-8 -*-
import codecs
import re

path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with codecs.open(path, 'r', 'utf-8') as f:
    text = f.read()

# Add syncDialogueToCloud after LLM reply
pattern = r'(Log\.i\("AI_DEBUG", "LLM Success: " \+ replyText\))'

replacement = '''val stepsList = mutableListOf<String>()
                    replyText.split("\\n").forEach { line ->
                        val t = line.trim()
                        // 提取带数字、项目符号的行，或者是没有句号的短句作为步骤
                        if (t.matches(Regex("^(?:\\\\d+[\\\\.\\\\x20、，-]|[-*•]).+")) || (t.isNotEmpty() && t.length < 40 && !t.contains("。") && !t.contains("？") && !t.contains("！"))) {
                            // 清理开头的数字和符号
                            val cleanStep = t.replace(Regex("^(?:\\\\d+[\\\\.\\\\x20、，-]|[-*•])\\\\s*"), "")
                            if (cleanStep.isNotEmpty()) stepsList.add(cleanStep)
                        }
                    }
                    if (stepsList.isEmpty()) {
                        stepsList.add(replyText) // fallback
                    }
                    // ✅ 关键：把 AI 的完整回复和拆解好的步骤同步给小程序
                    syncDialogueToCloud(userText, replyText, stepsList)

                    \\1'''

text = re.sub(pattern, replacement, text)

with codecs.open(path, 'w', 'utf-8') as f:
    f.write(text)

print("Added syncDialogueToCloud to callLLMForReply")
