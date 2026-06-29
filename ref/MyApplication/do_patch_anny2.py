import re

with open('app/src/main/java/com/example/myapplication/MainActivity.kt', 'r', encoding='utf-8') as f:
    text = f.read()

# Just use string replace for a very specific line to find the block
chunk_start = text.find('tvAiStatus.text = " 正在全自动生成逼真语音(TTS)..."')
chunk_end = text.find('renderPool()', chunk_start)
print(f"Start: {chunk_start}, End: {chunk_end}")

if chunk_start != -1 and chunk_end != -1:
    chunk_to_replace = text[chunk_start:chunk_end]
    print("Found chunk:", repr(chunk_to_replace))
    
    new_chunk = """tvAiStatus.text = " 正在全自动生成逼真语音(TTS)..."

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
                            }
                            """
    text = text[:chunk_start] + new_chunk + text[chunk_end:]
    
    with open('app/src/main/java/com/example/myapplication/MainActivity.kt', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Successfully replaced chunk!")
else:
    print("Chunk not found!")
