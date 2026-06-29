import codecs

p = 'D:/ADHD/MyApplication/app/src/main/java/com/example/myapplication/MainActivity.kt'
with codecs.open(p, 'r', 'utf-8') as f:
    t = f.read()

if 'import okhttp3.MediaType.Companion.toMediaTypeOrNull' not in t:
    t = t.replace('import okhttp3.OkHttpClient', 
                  'import okhttp3.OkHttpClient\nimport okhttp3.MediaType.Companion.toMediaTypeOrNull')

# Fix the cloud sync syntax error
s_cloud = """        val body = okhttp3.RequestBody.create(
            okhttp3.MediaType.Companion.toMediaTypeOrNull("application/json; charset=utf-8"),
            jsonObj.toString()
        )"""
r_cloud = """        val body = okhttp3.RequestBody.create("application/json; charset=utf-8".toMediaTypeOrNull(), jsonObj.toString())"""
t = t.replace(s_cloud, r_cloud)

# Also there might be another occurrence in cloud sync
t = t.replace('        val body = okhttp3.RequestBody.create(\n            okhttp3.MediaType.Companion.toMediaTypeOrNull("application/json; charset=utf-8"),\n            jsonObj.toString()\n        )', r_cloud)

# Fix the log syntax error
t = t.replace('"\\ 媒体上传失败: "', '"媒体上传失败: "')
t = t.replace('"\\ 云端返回: "', '"云端返回: "')

# Fix deprecation in the other okhttp body creations: 
# okhttp3MediaType.parse("application/json") -> "application/json".toMediaTypeOrNull()
t = t.replace('okhttp3.MediaType.parse("application/json")', '"application/json".toMediaTypeOrNull()')

# Now apply the huge JSON patch!
idx1 = t.find('private fun callLLMForReply(userText: String) {')
idx2 = t.find('private fun callTTSForAudio')

old_block = t[idx1:idx2]

new_block = """private fun callLLMForReply(userText: String) {
        val sysContent = \"\"\"你是一个贴心的任务拆解智能助手。无论用户说什么，必须严格按以下JSON格式输出，绝对禁止输出其他任何文字或额外的Markdown代码块标记：
{
  "target": "用户的最终目标",
  "state": "用户的当前状态、情绪或所处情境",
  "steps": ["极其简短的动作1", "极其简短的动作2"],
  "reply": "只有一句话的口语化回应。"
}
说明： 
target 是一句话概括最终目标； state 是一句话概括当前状态或情绪； steps 是拆解的动作数组，必须极简； reply 是口语化的简短回应（不超过20字），要随和。\"\"\"

        val messagesArray = com.google.gson.JsonArray()
        val sysMsg = com.google.gson.JsonObject().apply { addProperty("role", "system"); addProperty("content", sysContent) }
        messagesArray.add(sysMsg)

        for (round in historyLog) {
            val uMsg = com.google.gson.JsonObject().apply { addProperty("role", "user"); addProperty("content", round.first) }
            val aMsg = com.google.gson.JsonObject().apply { addProperty("role", "assistant"); addProperty("content", round.second) }
            messagesArray.add(uMsg)
            messagesArray.add(aMsg)
        }

        val curMsg = com.google.gson.JsonObject().apply { addProperty("role", "user"); addProperty("content", userText) }
        messagesArray.add(curMsg)

        val reqBodyJson = com.google.gson.JsonObject().apply {
            addProperty("model", "glm-4-flash")
            add("messages", messagesArray)
            val formatStr = com.google.gson.JsonObject()
            formatStr.addProperty("type", "json_object")
            add("response_format", formatStr)
        }

        val body = okhttp3.RequestBody.create("application/json".toMediaTypeOrNull(), reqBodyJson.toString())
        val request = okhttp3.Request.Builder()
            .url("https://open.bigmodel.cn/api/paas/v4/chat/completions")       
            .addHeader("Authorization", "Bearer " + ZHIPU_KEY)
            .post(body)
            .build()

        okHttpClient.newCall(request).enqueue(object : okhttp3.Callback {       
            override fun onFailure(call: okhttp3.Call, e: java.io.IOException) {
                android.util.Log.e("AI_DEBUG", "LLM Network Error: " + e.message)
                runOnUiThread { tvAiStatus.text = "✖ LLM 网络错误" }
                resetAI(1500)
            }

            override fun onResponse(call: okhttp3.Call, response: okhttp3.Response) {
                val respStr = response.body?.string() ?: ""
                try {
                    val jsonObj = org.json.JSONObject(respStr)
                    val choices = jsonObj.getJSONArray("choices")
                    val replyText = choices.getJSONObject(0).getJSONObject("message").getString("content")

                    val stepsList = mutableListOf<String>()
                    var targetStr = ""
                    var stateStr = ""
                    var ttsReply = replyText

                    try {
                        var cleanJson = replyText.trim()
                        val startIndex = cleanJson.indexOf("{")
                        val endIndex = cleanJson.lastIndexOf("}")
                        if (startIndex != -1 && endIndex != -1 && endIndex >= startIndex) {
                            cleanJson = cleanJson.substring(startIndex, endIndex + 1)
                        } else {
                            throw Exception("No JSON braces found")
                        }

                        val aiData = org.json.JSONObject(cleanJson)
                        targetStr = aiData.optString("target", "无目标")
                        stateStr = aiData.optString("state", "无状态")
                        ttsReply = aiData.optString("reply", replyText)

                        val stepsArr = aiData.optJSONArray("steps")
                        if (stepsArr != null) {
                            for (i in 0 until stepsArr.length()) {
                                stepsList.add(stepsArr.getString(i))
                            }
                        }

                        historyLog.add(Pair(userText, cleanJson))
                        while (historyLog.size > 10) { historyLog.removeAt(0) } 

                    } catch (e: Exception) {
                        val errMsg = e.message ?: "Unknown"
                        android.util.Log.e("AI_DEBUG", "Not JSON: " + errMsg)    
                        runOnUiThread {
                           tvUserTask.text = "JSON解析失败"
                           val etxt = errMsg.take(30)
                           tvAiReply.text = "Error: " + etxt
                           tvActionSteps.text = replyText.take(100)
                        }
                        resetAI(4000)
                        return
                    }

                    if (!userText.startsWith("系统指令：")) {
                         syncDialogueToCloud(userText, ttsReply, stepsList)     
                    }

                    runOnUiThread {
                        if (targetStr.isNotEmpty() && targetStr != "无目标") {
                            tvUserTask.text = "目标：" + targetStr
                        } else {
                            tvUserTask.text = "未含目标"
                        }

                        tvUserState.text = "状态：" + stateStr
                        
                        if (stepsList.isNotEmpty()) {
                            val stepStr = stepsList.mapIndexed { index, s -> (index + 1).toString() + ". " + s }.joinToString("\\n")
                            tvActionSteps.text = "步骤：\\n" + stepStr
                        } else {
                            tvActionSteps.text = "步骤：\\n(无)"
                        }
                        tvAiReply.text = "AI: " + ttsReply
                        tvAiStatus.text = "🔊 正在生成语音(TTS)..."   
                    }

                    android.util.Log.i("AI_DEBUG", "LLM Success, TTS string: " + ttsReply)
                    callTTSForAudio(ttsReply)
                } catch (e: Exception) {
                    android.util.Log.e("AI_DEBUG", "LLM parse failed: " + e.message + " json: " + respStr)
                    runOnUiThread { tvAiStatus.text = "✖ LLM 解析异常" }        
                    resetAI(1500)
                }
            }
        })
    }
"""

t = t.replace(old_block, new_block + '\n    ')
codecs.open(p, 'w', 'utf-8').write(t)
print("Safe JSON Patch Applied Successfully!")
