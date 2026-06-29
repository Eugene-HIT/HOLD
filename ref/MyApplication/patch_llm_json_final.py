# -*- coding: utf-8 -*-
with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'r', encoding='utf-8') as f:
    text = f.read()

idx1 = text.find('val stepsList = mutableListOf<String>()')
idx2 = text.find('} catch (e: Exception) {\n                    Log.e("AI_DEBUG", "LLM parse failed:')

if idx1 != -1 and idx2 != -1:
    new_code = '''val stepsList = mutableListOf<String>()
                    var targetStr = ""
                    var stateStr = ""
                    var ttsReply = replyText

                    try {
                        var cleanJson = replyText.trim()
                        if (cleanJson.startsWith("`json")) cleanJson = cleanJson.substring(7)
                        if (cleanJson.startsWith("`")) cleanJson = cleanJson.substring(3)
                        if (cleanJson.endsWith("`")) cleanJson = cleanJson.substring(0, cleanJson.length - 3)
                        cleanJson = cleanJson.trim()

                        val aiData = org.json.JSONObject(cleanJson)
                        targetStr = aiData.optString("target", "")
                        stateStr = aiData.optString("state", "")
                        ttsReply = aiData.optString("reply", replyText)

                        val stepsArr = aiData.optJSONArray("steps")
                        if (stepsArr != null) {
                            for (i in 0 until stepsArr.length()) {
                                stepsList.add(stepsArr.getString(i))
                            }
                        }
                    } catch (e: Exception) {
                        android.util.Log.e("AI_DEBUG", "Not JSON, fallback to raw: \")
                        
                        val linesArray = replyText.split("\\n")
                        for (lineText in linesArray) {
                            val tStr = lineText.trim()
                            if (tStr.matches(Regex("^(?:\\\\d+[\\\\.\\\\x20、，-]|[-*•]).+")) || (tStr.isNotEmpty() && tStr.length < 40 && !tStr.contains("。") && !tStr.contains("？") && !tStr.contains("！"))) {
                                val cleanStep = tStr.replace(Regex("^(?:\\\\d+[\\\\.\\\\x20、，-]|[-*•])\\\\s*"), "")
                                if (cleanStep.isNotEmpty()) stepsList.add(cleanStep)
                            }
                        }
                        if (stepsList.isEmpty()) {
                            stepsList.add(replyText)
                        }
                    }

                    syncDialogueToCloud(userText, ttsReply, stepsList)
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
                    }

                    android.util.Log.i("AI_DEBUG", "LLM Success, TTS string: " + ttsReply)
                    callTTSForAudio(ttsReply)
                '''
    text = text[:idx1] + new_code + text[idx2:]
    with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Patched correctly!")
else:
    print("Could not find indices:", idx1, idx2)
