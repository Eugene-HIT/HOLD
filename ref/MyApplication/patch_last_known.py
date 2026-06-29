# -*- coding: utf-8 -*-
with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'r', encoding='utf-8') as f:
    text = f.read()

# Add global state holders
globals_injection = '''    private val poolItems = mutableListOf<HelpRequest>()
    private var lastKnownTask = "未知"
    private var lastKnownState = "未知"
    private var lastKnownStepsText = "暂无步骤"
    private var lastKnownStepsList = mutableListOf<String>()'''
text = text.replace('    private val poolItems = mutableListOf<HelpRequest>()', globals_injection)

# Replace parse logic
old_parse = '''                    var userTask = "未知"
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
                                sb.append(i + 1).append(". ").append(s).append("\n")
                            }
                            stepsText = sb.toString().trim()
                        }
                    } catch (e: Exception) {
                        e.printStackTrace()
                    }'''

new_parse = '''                    var userTask = lastKnownTask
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
                            extractedSteps.clear()
                            val sb = java.lang.StringBuilder()
                            for (i in 0 until stepsArray.length()) {
                                val s = stepsArray.getString(i)
                                extractedSteps.add(s)
                                sb.append(i + 1).append(". ").append(s).append("\n")
                            }
                            stepsText = sb.toString().trim()
                            lastKnownStepsList.clear()
                            lastKnownStepsList.addAll(extractedSteps)
                            lastKnownStepsText = stepsText
                        }
                    } catch (e: Exception) {
                        e.printStackTrace()
                    }'''

if old_parse in text:
    text = text.replace(old_parse, new_parse)
    print("Replaced cache logic!")
else:
    print("Could not find the parse logic block.")

with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'w', encoding='utf-8') as f:
    f.write(text)

