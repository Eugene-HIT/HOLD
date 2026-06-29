# -*- coding: utf-8 -*-
import codecs
import re

path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with codecs.open(path, 'r', 'utf-8') as f:
    text = f.read()

# Fix the broken code
pattern = r'''val stepsList = mutableListOf<String>\(\)\s*replyText\.split\("\s*"\)\.forEach \{ line ->\s*val t = line\.trim\(\)\s*// 提取带数字、项目符号的行，或者是没有句号的短句作为步骤\s*if \(t\.matches\(Regex\("\^\(\?:\\?d\+\[\\?\.\\?x20、，-\]\|\[-\*•\]\)\.\+"\)\) \|\| \(t\.isNotEmpty\(\) && t\.length < 40 && !t\.contains\("。"\) && !t\.contains\("？"\) && !t\.contains\("！"\)\)\) \{\s*// 清理开头的数字和符号\s*val cleanStep = t\.replace\(Regex\("\^\(\?:\\?d\+\[\\?\.\\?x20、，-\]\|\[-\*•\]\)\\?s\*"   ?\), ""\)\s*if \(cleanStep\.isNotEmpty\(\)\) stepsList\.add\(cleanStep\)\s*\}\s*\}\s*if \(stepsList\.isEmpty\(\)\) \{\s*stepsList\.add\(replyText\) // fallback\s*\}\s*// ✅ 关键：把 AI 的完整回复和拆解好的步骤同步给小程序\s*syncDialogueToCloud\(userText, replyText, stepsList\)'''

# Alternatively just do a substring replace of the exact broken block
