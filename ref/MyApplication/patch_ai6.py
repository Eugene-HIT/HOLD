import re

path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update resetAI with lastAIResetId
if "lastAIResetId" not in text:
    old_reset = r'private fun resetAI\(delayMs: Long = 0\) \{[ \t]*\n[ \t]*Handler\(Looper\.getMainLooper\(\)\)\.postDelayed\(\{[ \t]*\n[ \t]*isAIThinking = false'
    new_reset = r'''private var lastAIResetId = 0
    private fun resetAI(delayMs: Long = 0) {
        val currentId = ++lastAIResetId
        Handler(Looper.getMainLooper()).postDelayed({
            if (currentId == lastAIResetId) {
                isAIThinking = false'''
    text = re.sub(old_reset, new_reset, text)

    # Add closing brace
    # Find tvAiStatus.text = "xxAI 闲置就绪，等待听你讲话..."\n }, delayMs)
    # The text has broken unicode "?AI 闲置就绪，等待听你讲?.."
    # we can just match `(tvAiStatus\.text = ".*?AI 闲置就绪.*?")[ \t\n]*\}, delayMs\)`
    old_end = r'(tvAiStatus\.text = ".*?AI .*?")[ \t]*\n[ \t]*\}, delayMs\)'
    new_end = r'\1\n            }\n        }, delayMs)'
    text = re.sub(old_end, new_end, text)


# 2. Add pool addition in LLM Success
old_llm_success = r'(tvAiStatus\.text = " 正在全自动.*?")[ \t]*\n[ \t]*\}[ \t]*\n[ \t]*callTTSForAudio'
new_llm_success = r'''\1
                          poolItems.add(0, HelpRequest("Anny", "想要${userTask}，状态是${userState}"))
                          if (poolItems.size > 10) poolItems.removeAt(poolItems.size - 1)
                          renderPool()
                      }
                    callTTSForAudio'''
if "poolItems.add(0" not in text:
    text = re.sub(old_llm_success, new_llm_success, text)

# 3. Add resetAI inside streamPcmToEsp32
old_ble_debug = r'(android\.util\.Log\.i\("BLE_DEBUG", "Sent PCM to ESP32\."\))[ \t]*\n[ \t]*\}[ \t]*\n[ \t]*\}\.start\(\)'
new_ble_debug = r'''\1
                resetAI(1500)
            }
        }.start()'''
if 'resetAI(1500)\n            }\n        }.start()' not in text:
    text = re.sub(old_ble_debug, new_ble_debug, text)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
print("done!")
