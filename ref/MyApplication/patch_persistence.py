# -*- coding: utf-8 -*-
with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add fields
fields_old = '    private val historyLog = mutableListOf<Pair<String, String>>()'
fields_new = '''    private val historyLog = mutableListOf<Pair<String, String>>()
    private var lastKnownTask = "未知"
    private var lastKnownState = "未知"
    private var lastKnownStepsText = "暂无步骤"
    private val lastKnownStepsList = mutableListOf<String>()'''

if 'lastKnownTask' not in text:
    text = text.replace(fields_old, fields_new)

# 2. Add parse logic
parse_old = '''                      var userTask = "未知"
                      var userState = "未知"
                      var stepsText = "等待识别..."
                      var finalReplyText = replyText
                      val extractedSteps = mutableListOf<String>()

                      // ✅ 完全保留你最原始完美的 JSON 解析代码！绝对不会坏！
                      try {
                          var contentStr = replyText.trim()
                          if (contentStr.startsWith("`json")) { contentStr = contentStr.substring(7) }
                          else if (contentStr.startsWith("`")) { contentStr = contentStr.substring(3) }
                          if (contentStr.endsWith("`")) { contentStr = contentStr.substring(0, contentStr.length - 3) }
                          contentStr = contentStr.trim()

                          val contentObj = org.json.JSONObject(contentStr)
                          val innerReply = contentObj.optString("reply")
                          if (innerReply.isNotEmpty()) {
                              finalReplyText = innerReply
                          }
                          userTask = contentObj.optString("user_task", "未知")
                          userState = contentObj.optString("user_state", "未知")
                          val stepsArray = contentObj.optJSONArray("steps")
                          if (stepsArray != null && stepsArray.length() > 0) {
                              val sb = java.lang.StringBuilder()
                              for (i in 0 until stepsArray.length()) {
                                  val s = stepsArray.getString(i)
                                  extractedSteps.add(s)
                                  sb.append(i + 1).append(". ").append(s).append("\\n")
                              }
                              stepsText = sb.toString().trim()
                          }'''

parse_new = '''                      var userTask = lastKnownTask
                      var userState = lastKnownState
                      var stepsText = lastKnownStepsText
                      var finalReplyText = replyText
                      val extractedSteps = mutableListOf<String>()
                      extractedSteps.addAll(lastKnownStepsList)

                      // ✅ 完全保留你最原始完美的 JSON 解析代码！绝对不会坏！
                      try {
                          var contentStr = replyText.trim()
                          if (contentStr.startsWith("`json")) { contentStr = contentStr.substring(7) }
                          else if (contentStr.startsWith("`")) { contentStr = contentStr.substring(3) }
                          if (contentStr.endsWith("`")) { contentStr = contentStr.substring(0, contentStr.length - 3) }
                          contentStr = contentStr.trim()

                          val contentObj = org.json.JSONObject(contentStr)
                          val innerReply = contentObj.optString("reply")
                          if (innerReply.isNotEmpty()) {
                              finalReplyText = innerReply
                          }
                          
                          val parsedTask = contentObj.optString("user_task", "未知")
                          if (parsedTask != "未知" && parsedTask.isNotEmpty()) {
                              userTask = parsedTask
                              lastKnownTask = parsedTask
                          }
                          
                          val parsedState = contentObj.optString("user_state", "未知")
                          if (parsedState != "未知" && parsedState.isNotEmpty()) {
                              userState = parsedState
                              lastKnownState = parsedState
                          }
                          
                          val stepsArray = contentObj.optJSONArray("steps")
                          if (stepsArray != null && stepsArray.length() > 0) {
                              val sb = java.lang.StringBuilder()
                              extractedSteps.clear()
                              lastKnownStepsList.clear()
                              for (i in 0 until stepsArray.length()) {
                                  val s = stepsArray.getString(i)
                                  extractedSteps.add(s)
                                  lastKnownStepsList.add(s)
                                  sb.append(i + 1).append(". ").append(s).append("\\n")
                              }
                              stepsText = sb.toString().trim()
                              lastKnownStepsText = stepsText
                          }'''

if parse_old in text:
    text = text.replace(parse_old, parse_new)
    print("Parsed JSON patch applied via string replacement")
else:
    # Try regex fallback for parse logic due to spacing
    import re
    import sys
    print("Could not match parse_old exactly. Trying Regex fallback.")
    fallback_regex = r'var userTask = "未知"\s*var userState = "未知"\s*var stepsText = "等待识别\.\.\."\s*var finalReplyText = replyText\s*val extractedSteps = mutableListOf<String>\(\)\s*(.*?)\s*\} catch \(e: Exception\)'
    
    match = re.search(fallback_regex, text, re.DOTALL)
    if match:
        text = text[:match.start()] + parse_new.replace('\\n', '\\\\n') + "\n                      } catch (e: Exception)" + text[match.end():]
        print("Regex fallback succeeded.")
    else:
        print("Regex fallback failed as well!")
        sys.exit(1)

with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'w', encoding='utf-8') as f:
    f.write(text)

print("Patching complete.")
