import re
with open('app/src/main/java/com/example/myapplication/MainActivity.kt', 'r', encoding='utf-8') as f:
    text = f.read()

target = r"""                            tvAiStatus.text = " 正在全自动生成逼真语音(TTS)..."
                            val existingAnny = poolItems.find \{ it.userName == "Anny" \}
                            if \(existingAnny != null\) \{
                                existingAnny.userAction = "想要\$\{userTask\}，状态是\$\{userState\}"
                                existingAnny.timestamp = System.currentTimeMillis\(\)
                            \} else \{
                                poolItems.add\(0, HelpRequest\("Anny", "想要\$\{userTask\}，状态是\$\{userState\}"\)\)
                                if \(poolItems.size > 10\) poolItems.removeAt\(poolItems.size - 1\)
                            \}"""

replacement = """                            tvAiStatus.text = " 正在全自动生成逼真语音(TTS)..."

                            val extractedSteps = try {
                                val arr = parsedJson.getAsJsonArray("steps")
                                val list = mutableListOf<String>()
                                if (arr != null) {
                                    for (i in 0 until arr.size()) list.add(arr.get(i).asString)
                                }
                                list
                            } catch (e: Exception) {
                                emptyList<String>()
                            }

                            val actionText = "想要${userTask}，状态是${userState}"
                            val existingAnny = poolItems.find { it.userName == "Anny" }
                            if (existingAnny != null) {
                                existingAnny.userAction = actionText
                                existingAnny.timestamp = System.currentTimeMillis()
                                existingAnny.steps = extractedSteps
                            } else {
                                poolItems.add(0, HelpRequest("Anny", actionText, System.currentTimeMillis(), extractedSteps))
                                if (poolItems.size > 10) poolItems.removeAt(poolItems.size - 1)
                            }"""

text = re.sub(target, replacement, text)

with open('app/src/main/java/com/example/myapplication/MainActivity.kt', 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated!")
