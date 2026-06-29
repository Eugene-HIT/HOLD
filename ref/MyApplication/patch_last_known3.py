# -*- coding: utf-8 -*-
import re

with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'r', encoding='utf-8') as f:
    text = f.read()

old_regex = r'var userTask = "(.*?)"\s*var userState = "(.*?)"\s*var stepsText = "(.*?)"\s*var finalReplyText = replyText\s*val extractedSteps = mutableListOf<String>\(\)\s*// ✅ 完全保留你最原始完美的 JSON 解析代码！绝对不会坏！\s*try \{\s*(.*?)\s*\} catch \(e: Exception\) \{\s*e\.printStackTrace\(\)\s*\}'

new_parse = '''var userTask = lastKnownTask
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
                        
                        val parsedTask = contentObj.optString("user_task", "")
                        if (parsedTask.isNotEmpty() && parsedTask != "未知") {
                            userTask = parsedTask
                            lastKnownTask = parsedTask
                        }
                        
                        val parsedState = contentObj.optString("user_state", "")
                        if (parsedState.isNotEmpty() && parsedState != "未知") {
                            userState = parsedState
                            lastKnownState = parsedState
                        }
                        
                        val stepsArray = contentObj.optJSONArray("steps")
                        if (stepsArray != null && stepsArray.length() > 0) {
                            extractedSteps.clear()
                            lastKnownStepsList.clear()
                            val sb = java.lang.StringBuilder()
                            for (i in 0 until stepsArray.length()) {
                                val s = stepsArray.getString(i)
                                extractedSteps.add(s)
                                lastKnownStepsList.add(s)
                                sb.append(i + 1).append(". ").append(s).append("\\n")
                            }
                            stepsText = sb.toString().trim()
                            lastKnownStepsText = stepsText
                        }
                    } catch (e: Exception) {
                        e.printStackTrace()
                    }'''

match = re.search(old_regex, text, flags=re.DOTALL)
if match:
    text = text[:match.start()] + new_parse.replace('\n', '\r\n') + text[match.end():]
    with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Replaced cache logic with regex!")
else:
    print("Regex failed to find the block!")
