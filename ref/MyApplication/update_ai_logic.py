import sys

with open(r'd:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update the System Prompt
target_prompt = '''        val sysContent = "你现在是一个温柔、坚定、鼓励的知心大姐姐。你的核心目标是引导患有ADHD的用户行动起来。" + 
"在对话中，你需要自然地了解两件事：1. 用户想做什么事（目标任务） 2. 用户现在的心态或身体状态（如焦虑、躺在床上等）。" +
"你必须只返回一个合法的 JSON 对象，绝对不要输出任何其他前后缀废话。" +
"必须包含以下字段：" +
"\"reply\": \"你要对用户说的口语化回复（保持温柔自然，暗中引导，千万不要说你在记录数据）\"," +
"\"user_task\": \"提取出的任务，如果未知请输出『未知』\"," +
"\"user_state\": \"提取出的状态，如果未知请输出『未知』\"," +
"\"steps\": [\"第一步\", \"第二步\", \"第三步\"] （只有在明确了任务和状态后，才为其拆解成3个极简微小动作，否则输出空数组 []）"'''

new_prompt = '''        val sysContent = "你现在是一个温柔、坚定、鼓励的知心大姐姐。你的核心目标是引导患有ADHD的用户行动起来。" + 
"在对话中，你需要自然地了解两件事：1. 用户想做什么事（目标任务） 2. 用户现在的心态或身体状态（如焦虑、躺在床上等）。" +
"你必须只返回一个合法的 JSON 对象，绝对不要输出任何其他前后缀废话。" +
"必须包含以下字段：" +
"\"reply\": \"你要对用户说的口语化回复（只能包含随和的聊天内容，**绝对不要**把拆分的步骤念出来或包含在reply里！像平时说话一样自然即可）\"," +
"\"user_task\": \"提取出的任务，如果未知请输出『未知』\"," +
"\"user_state\": \"提取出的状态，如果未知请输出『未知』\"," +
"\"steps\": [\"第一步\", \"第二步\", \"第三步\"] （只有在明确了任务和状态后，才为你口语中提到的建议拆解成3个极简微小动作，否则输出空数组 []）"'''

text = text.replace(target_prompt, new_prompt)

# 2. Add to Help Pool logic
target_logic = '''                      if (stepsArray != null && stepsArray.length() > 0) {
                          val sb = java.lang.StringBuilder()
                          for (i in 0 until stepsArray.length()) {
                              sb.append("").append(i+1).append(". ").append(stepsArray.getString(i)).append("\n")
                          }
                          stepsText = sb.toString().trim()
                      } else {
                          stepsText = "还在收集中，试着告诉姐姐你现在的心情？"
                      }'''

new_logic = '''                      if (stepsArray != null && stepsArray.length() > 0) {
                          val sb = java.lang.StringBuilder()
                          for (i in 0 until stepsArray.length()) {
                              sb.append("").append(i+1).append(". ").append(stepsArray.getString(i)).append("\n")
                          }
                          stepsText = sb.toString().trim()
                      } else {
                          stepsText = "还在收集中，试着告诉姐姐你现在的心情？"
                      }

                      // If we have valid state and steps, insert into the Help Pool
                      if (userTask != "未知" && userState != "未知" && stepsArray != null && stepsArray.length() > 0) {
                          val helpTaskStr = "想要" + userTask + "，状态是" + userState
                          poolItems.add(0, HelpRequest(name = "Anny", task = helpTaskStr))
                          renderPool()
                      }'''

text = text.replace(target_logic, new_logic)

with open(r'd:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'w', encoding='utf-8') as f:
    f.write(text)

print("Prompt and Pool UI logic updated")
