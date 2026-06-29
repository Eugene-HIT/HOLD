# -*- coding: utf-8 -*-
with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'r', encoding='utf-8') as f:
    t = f.read()

# Add TV variables
old_vars = '''    private lateinit var tvAiStatus: TextView
    private lateinit var tvUserVoice: TextView
    private lateinit var tvAiReply: TextView'''
new_vars = '''    private lateinit var tvAiStatus: TextView
    private lateinit var tvUserVoice: TextView
    private lateinit var tvAiReply: TextView
    private lateinit var tvUserTask: TextView
    private lateinit var tvUserState: TextView
    private lateinit var tvActionSteps: TextView'''
if old_vars in t:
    t = t.replace(old_vars, new_vars)

old_find = '''        tvAiStatus = findViewById(R.id.tvAiStatus)
        tvUserVoice = findViewById(R.id.tvUserVoice)
        tvAiReply = findViewById(R.id.tvAiReply)'''
new_find = '''        tvAiStatus = findViewById(R.id.tvAiStatus)
        tvUserVoice = findViewById(R.id.tvUserVoice)
        tvAiReply = findViewById(R.id.tvAiReply)
        tvUserTask = findViewById(R.id.tvUserTask)
        tvUserState = findViewById(R.id.tvUserState)
        tvActionSteps = findViewById(R.id.tvActionSteps)'''
if old_find in t:
    t = t.replace(old_find, new_find)

# Replace System Prompt and Parse Logic
old_llm = '''    private fun callLLMForReply(userText: String) {
        val sysContent = "你是一个贴心的任务拆解智能助手。当用户告诉你他们想做什么时，你需要把他们的任务拆解成可操作的具体步骤，一步一步指导他们怎么做。语言要求简短、直接、口语化。禁止使用任何客套、格式化或废话。"'''

new_llm = '''    private fun callLLMForReply(userText: String) {
        val sysContent = """你是一个贴心的任务拆解智能助手。请务必结合【前文语境】和当前用户回复来判断。
如果用户这次只补充了状态（如“起不来”），请保留前文已确认的目标（如“写论文”）；不要轻易标记为未知！
无论怎样，必须严格按以下JSON格式输出，绝对禁止输出其他任何文字或添加Markdown代码块标记：
{
  "target": "根据上下文综合推断的当前小目标或大目标",
  "state": "根据上下文综合推断的当前状态、情绪或所处情境",
  "steps": ["极其简短的动作1", "极其简短的动作2"],
  "reply": "结合目标与状态，给出只有一句话的口语化随和回应。"
}
说明：
target 用一句话概括最终目标；state 用一句话概括当前状态或情绪；steps 是推动的一小步动作数组，必须极简；reply 是口语化回应（不超过20字），要随和。"""'''
import re
if re.search(old_llm.replace('\n', '\r\n'), t):
    t = t.replace(old_llm.replace('\n', '\r\n'), new_llm.replace('\n', '\r\n'))
else:
    t = t.replace(old_llm, new_llm)

old_parse = '''                    val replyText = choices.getJSONObject(0).getJSONObject("message").getString("content")
                    
                    historyLog.add(Pair(userText, replyText))
                                if (historyLog.size > 10) historyLog.removeAt(0)
                                if (historyLog.size > 10) historyLog.removeAt(0)
                    if (historyLog.size > 10) historyLog.removeAt(0)
                    
                    Log.i("AI_DEBUG", "LLM Success: " + replyText)
                    runOnUiThread { tvAiReply.text = "AI: " + replyText; tvAiStatus.text = "🔊 正在全自动生成逼真语音(TTS)..." }
                    callTTSForAudio(replyText)'''

new_parse = '''                    var replyText = choices.getJSONObject(0).getJSONObject("message").getString("content")
                    replyText = replyText.trim()
                    if (replyText.startsWith("`json")) {
                        replyText = replyText.substring(7)
                    }
                    if (replyText.startsWith("`")) {
                        replyText = replyText.substring(3)
                    }
                    if (replyText.endsWith("`")) {
                        replyText = replyText.substring(0, replyText.length - 3)
                    }
                    replyText = replyText.trim()
                    
                    try {
                        val parsed = org.json.JSONObject(replyText)
                        val target = parsed.optString("target", "未知")
                        val state = parsed.optString("state", "未知")
                        val stepsArr = parsed.optJSONArray("steps")
                        val stepsList = mutableListOf<String>()
                        if (stepsArr != null) {
                            for (i in 0 until stepsArr.length()) {
                                stepsList.add(stepsArr.getString(i))
                            }
                        }
                        val finalReply = parsed.optString("reply", "好的")
                        
                        runOnUiThread {
                            tvUserTask.text = "【当前目标】：" + target
                            tvUserState.text = "【当前状态】：" + state
                            tvActionSteps.text = "【行动建议】：" + stepsList.joinToString(" ➔ ")
                            tvAiReply.text = "AI: " + finalReply
                            tvAiStatus.text = "🔊 正在生成声音(TTS)..."
                        }
                        
                        syncDialogueToCloud(userText, finalReply, stepsList)

                        historyLog.add(Pair(userText, "\{\\"target\":\"\\", \\"state\":\"\\", \\"reply\":\"\\"}"))
                        if (historyLog.size > 10) historyLog.removeAt(0)
                        
                        callTTSForAudio(finalReply)
                        
                    } catch (e: Exception) {
                        val errMsg = e.message ?: "Unknown"
                        android.util.Log.e("AI_DEBUG", "JSON Parse Fail: \. Raw: \")
                        runOnUiThread {
                            tvAiReply.text = "AI (Raw): " + replyText
                            tvAiStatus.text = "🔊 正在生成声音(TTS)..."
                        }
                        historyLog.add(Pair(userText, replyText))
                        if (historyLog.size > 10) historyLog.removeAt(0)
                        callTTSForAudio(replyText)
                    }'''
if re.search(old_parse.replace('\n', '\r\n'), t):
    t = t.replace(old_parse.replace('\n', '\r\n'), new_parse.replace('\n', '\r\n'))
else:
    t = t.replace(old_parse, new_parse)

# Inject syncDialogueToCloud dummy if not exists
if "private fun syncDialogueToCloud" not in t:
    t = t.replace("private fun callTTSForAudio", "    private fun syncDialogueToCloud(userText: String?, aiText: String?, steps: List<String>?) { android.util.Log.i(\"AI_DEBUG\", \"Sync dialogue to cloud: \\") }\n    private fun callTTSForAudio")

with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'w', encoding='utf-8') as f:
    f.write(t)
print("JSON logic restored")
