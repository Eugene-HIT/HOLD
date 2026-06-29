# -*- coding: utf-8 -*-
import codecs
import re

path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with codecs.open(path, 'r', 'utf-8') as f:
    text = f.read()

# 1. UI Additions
if 'tvUserTask' not in text:
    text = text.replace(
        'private lateinit var tvAiReply: TextView',
        'private lateinit var tvAiReply: TextView\n    private lateinit var tvUserTask: TextView\n    private lateinit var tvUserState: TextView\n    private lateinit var tvActionSteps: TextView'
    )
    text = text.replace(
        'tvAiReply = findViewById(R.id.tvAiReply)',
        'tvAiReply = findViewById(R.id.tvAiReply)\n        tvUserTask = findViewById(R.id.tvUserTask)\n        tvUserState = findViewById(R.id.tvUserState)\n        tvActionSteps = findViewById(R.id.tvActionSteps)'
    )
    
    text = re.sub(
        r'(runOnUiThread \{ tvUserVoice\.text = "\? " \+ finalStr; tvAiStatus\.text = ".*" \})',
        r'\1\n                        runOnUiThread { tvUserTask.text = "目标：" + finalStr; tvUserState.text = "状态：Gulu 正在拆解任务..." }',
        text
    )

# 2. Greeting Replacement
old_greet = 'callLLMForReply("系统指令：请用一句非常简短、随和的口语向用户打招呼'
new_greet = 'callLLMForReply("系统指令：你的系统刚刚启动！请用一句非常简短、随和的口语向用户主动打招呼（比如问接下来干点啥）。注意：尽管这是打招呼，你也必须严格按照系统提示词的纯JSON格式返回！你可以把 target 和 state 填为 \'无\'，把 steps 填为 []，只在 reply 字段里写这句打招呼的话。绝对不能直接返回纯文本！"'
if old_greet in text:
    text = text.replace(old_greet, new_greet)
else:
    # try regex just in case
    text = re.sub(r'callLLMForReply\("系统指令：请用一句非常简短、随和的口语向用户打招呼.*?"\)', new_greet + ')', text)

# 3. callLLMForReply overwrite
idx1 = text.find('private fun callLLMForReply(userText: String) {')
idx2 = text.find('private fun callTTSForAudio')

if idx1 != -1 and idx2 != -1:
    new_call_llm = '''private fun callLLMForReply(userText: String) {
        val sysContent = """你是一个贴心的任务拆解智能助手。当用户告诉你他们想做什么时，请精确地使用以下纯JSON格式输出！绝对禁止输出其他任何文字，不要加Markdown代码块标记（如 `json ）！
{
  "target": "写论文",
  "state": "拖延慵懒",
  "steps": ["坐起来", "走到桌前", "打开电脑"],
  "reply": "好的，要不要先尝试坐起来？"
}
说明：
target 是一句话概括最终目标；
state 是一句话概括当前状态或情绪；
steps 是拆解的动作数组，必须极简；
reply 是口语化的简短回应（不超过20字），要随和。
"""

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
            // 尝试强制大模型返回JSON对象结构
            val formatStr = com.google.gson.JsonObject()
            formatStr.addProperty("type", "json_object")
            add("response_format", formatStr)
        }

        val body = okhttp3.RequestBody.create(okhttp3.MediaType.parse("application/json"), reqBodyJson.toString())
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
                val respStr = response.body()?.string() ?: ""
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
                        targetStr = aiData.optString("target", "")
                        stateStr = aiData.optString("state", "")
                        ttsReply = aiData.optString("reply", replyText)

                        val stepsArr = aiData.optJSONArray("steps")
                        if (stepsArr != null) {
                            for (i in 0 until stepsArr.length()) {
                                stepsList.add(stepsArr.getString(i))
                            }
                        }

                        // 只有在成功解析出JSON后，才将正确格式放入历史记录！
                        historyLog.add(Pair(userText, cleanJson))
                        while (historyLog.size > 10) { historyLog.removeAt(0) }
                        
                    } catch (e: Exception) {
                        val errMsg = e.message ?: "Unknown"
                        android.util.Log.e("AI_DEBUG", "Not JSON: \. Raw: \")

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

                    if (userText.startsWith("系统指令：")) {
                         // 不上传到云端
                    } else {
                         syncDialogueToCloud(userText, ttsReply, stepsList)
                    }

                    runOnUiThread {
                        if (targetStr.isNotEmpty()) {
                            tvUserTask.text = "目标：" + targetStr
                        } else {
                            tvUserTask.text = "返回未含目标！原回复开头：" + replyText.take(50).replace("\\n", " ")
                        }

                        if (stateStr.isNotEmpty()) {
                            tvUserState.text = "状态：" + stateStr
                        } else {
                            tvUserState.text = "状态：JSON解析失败"
                        }

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
                } catch (e: Exception) {
                    android.util.Log.e("AI_DEBUG", "LLM parse failed: " + e.message + " json: " + respStr)
                    runOnUiThread { tvAiStatus.text = "✖ LLM 解析失败" }        
                    resetAI(1500)
                }
            }
        })
    }

    '''
    text = text[:idx1] + new_call_llm + text[idx2:]
    with codecs.open(path, 'w', 'utf-8') as f:
        f.write(text)
    print("Mega patch applied successfully!")
else:
    print("Could not find method bounds.")
