import re

path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update resetAI with lastAIResetId
if "var lastAIResetId" not in text:
    old_reset = '''    private fun resetAI(delayMs: Long = 0) {
        Handler(Looper.getMainLooper()).postDelayed({
            isAIThinking = false
            isRecordingLocal = false
            audioBufferQueue.clear()
            playbackBuffer.reset()
            audioTrack?.pause()
            audioTrack?.flush()
            if (isPlayingAudio) audioTrack?.play()
            tvAiStatus.text = "🟢 AI 闲置就绪，等待听你讲话..."
        }, delayMs)
    }'''

    new_reset = '''    private var lastAIResetId = 0
    private fun resetAI(delayMs: Long = 0) {
        val currentId = ++lastAIResetId
        Handler(Looper.getMainLooper()).postDelayed({
            if (currentId == lastAIResetId) {
                isAIThinking = false
                isRecordingLocal = false
                audioBufferQueue.clear()
                playbackBuffer.reset()
                audioTrack?.pause()
                audioTrack?.flush()
                if (isPlayingAudio) audioTrack?.play()
                tvAiStatus.text = "🟢 AI 闲置就绪，等待听你讲话..."
            }
        }, delayMs)
    }'''
    text = text.replace(old_reset, new_reset)

# 2. Add pool addition in LLM Success
old_llm_success = '''                          tvActionSteps.text = " 拆解步骤：\\n" + stepsText
                          tvAiStatus.text = " 正在全自动生成逼真语音(TTS)..."
                      }
                    callTTSForAudio(replyText)'''

new_llm_success = '''                          tvActionSteps.text = " 拆解步骤：\\n" + stepsText
                          tvAiStatus.text = " 正在全自动生成逼真语音(TTS)..."
                          poolItems.add(0, HelpRequest("Anny", "想要${userTask}，状态是${userState}"))
                          if (poolItems.size > 10) poolItems.removeAt(poolItems.size - 1)
                          renderPool()
                      }
                    callTTSForAudio(replyText)'''
if "poolItems.add(0" not in text:
    text = text.replace(old_llm_success, new_llm_success)

# 3. Add resetAI inside streamPcmToEsp32
old_ble_debug = '''                android.util.Log.i("BLE_DEBUG", "Sent PCM to ESP32.")
            }
        }.start()'''
new_ble_debug = '''                android.util.Log.i("BLE_DEBUG", "Sent PCM to ESP32.")
                resetAI(1500)
            }
        }.start()'''
if 'resetAI(1500)' not in text and 'override fun onStart' not in text:
    text = text.replace(old_ble_debug, new_ble_debug)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
print("done!")
