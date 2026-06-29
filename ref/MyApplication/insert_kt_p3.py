import re

kt_path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(kt_path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add variable declarations
decl_pattern = r'private lateinit var tvAiReply: TextView'
decl_repl = '''private lateinit var tvAiReply: TextView
    private lateinit var tvUserTask: TextView
    private lateinit var tvUserState: TextView
    private lateinit var tvActionSteps: TextView'''
# replace exactly once
if "tvUserTask: TextView" not in text:
    text = text.replace('private lateinit var tvAiReply: TextView', decl_repl, 1)

# 2. Add findViewByIds
init_pattern = r'tvAiReply = findViewById\(R\.id\.tvAiReply\)'
init_repl = '''tvAiReply = findViewById(R.id.tvAiReply)
        tvUserTask = findViewById(R.id.tvUserTask)
        tvUserState = findViewById(R.id.tvUserState)
        tvActionSteps = findViewById(R.id.tvActionSteps)'''
if "tvUserTask = findViewById" not in text:
    text = text.replace('tvAiReply = findViewById(R.id.tvAiReply)', init_repl, 1)

# 3. Update sysContent
old_sys = 'val sysContent = "你是一个贴心的任务拆解智能助手。当用户告诉你他们想做什么时，你需要把他们的任务拆解成可操作的具体步骤，一步一步指导他们怎么做。语言要求简短、直接、口语化。禁止使用任何客套、格式化或废话。"'
new_sys = '''val sysContent = "你现在是一个温柔、坚定、鼓励的知心大姐姐。你的核心目标是引导患有ADHD的用户行动起来。" + 
"在对话中，你需要自然地了解两件事：1. 用户想做什么事（目标任务） 2. 用户现在的心态或身体状态（如焦虑、躺在床上等）。" +
"你必须只返回一个合法的 JSON 对象，绝对不要输出任何其他前后缀废话。" +
"必须包含以下字段：" +
"\\"reply\\": \\"你要对用户说的口语化回复（保持温柔自然，暗中引导，千万不要说你在记录数据）\\"," +
"\\"user_task\\": \\"提取出的任务，如果未知请输出『未知』\\"," +
"\\"user_state\\": \\"提取出的状态，如果未知请输出『未知』\\"," +
"\\"steps\\": [\\"第一步\\", \\"第二步\\", \\"第三步\\"] （只有在明确了任务和状态后，才为其拆解成3个极简微小动作，否则输出空数组 []）"'''
text = text.replace(old_sys, new_sys)

# 4. Update response_format injection
req_old = '''          val reqBodyJson = JsonObject().apply {
              addProperty("model", "glm-4-flash")
              add("messages", messagesArray)
          }'''
req_new = '''          val reqBodyJson = JsonObject().apply {
              addProperty("model", "glm-4-flash")
              add("messages", messagesArray)
              add("response_format", JsonObject().apply { addProperty("type", "json_object") })
          }'''
text = text.replace(req_old, req_new)

# 5. Update Response Parsing Logic safely
cb_pattern = r'val jsonObj = JSONObject\(respStr\)\s*val choices = jsonObj\.getJSONArray\("choices"\).*?runOnUiThread \{ tvAiReply\.text = "AI: " \+ replyText; tvAiStatus\.text = ".*? 正在全自动生成逼真语音\(TTS\)\.\.\." \}'
cb_repl = '''val jsonObj = JSONObject(respStr)
                      val choices = jsonObj.getJSONArray("choices")
                      val contentStr = choices.getJSONObject(0).getJSONObject("message").getString("content")
                      
                      val contentObj = JSONObject(contentStr)
                      val replyText = contentObj.optString("reply", "姐姐收到啦，你想做点什么呢？")
                      val userTask = contentObj.optString("user_task", "未知")
                      val userState = contentObj.optString("user_state", "未知")
                      val stepsArray = contentObj.optJSONArray("steps")
                      var stepsText = "等待识别..."
                      if (stepsArray != null && stepsArray.length() > 0) {
                          val sb = java.lang.StringBuilder()
                          for (i in 0 until stepsArray.length()) {
                              sb.append("").append(i+1).append(". ").append(stepsArray.getString(i)).append("\\n")
                          }
                          stepsText = sb.toString().trim()
                      } else {
                          stepsText = "还在收集中，试着告诉姐姐你现在的心情？"
                      }

                      historyLog.add(Pair(userText, replyText))
                      if (historyLog.size > 10) historyLog.removeAt(0)

                      android.util.Log.i("AI_DEBUG", "LLM Success: " + replyText)
                      runOnUiThread { 
                          tvAiReply.text = "AI: " + replyText
                          tvUserTask.text = " 目标任务：" + userTask
                          tvUserState.text = " 当前状态：" + userState
                          tvActionSteps.text = " 拆解步骤：\\n" + stepsText
                          tvAiStatus.text = " 正在全自动生成逼真语音(TTS)..." 
                      }'''

text = re.sub(cb_pattern, cb_repl, text, flags=re.DOTALL)

with open(kt_path, 'w', encoding='utf-8') as f:
    f.write(text)

print("Kotlin updated carefully!")
