# -*- coding: utf-8 -*-
with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'r', encoding='utf-8') as f:
    orig = f.read()

# I will fix the condition.
# Right now, if (descriptor.characteristic.uuid == MIC_AUDIO_CHAR_UUID) triggers the camera config AND the AI greeting.
# BUT WAIT.
# gatt.writeDescriptor(camDec) is called.
# And inside that SAME IF block, callLLMForReply is called. 
# BUT onDescriptorWrite is called for IMU, then MIC_AUDIO, then CAM_IMAGE !
# Ah !!
# onDescriptorWrite is a callback. 
# When IMU is written, it writes audioDec.
# When audioDec is written (its UUID is actually CCCD_UUID, the descriptor's UUID is the same!). 
# Wait! descriptor.characteristic.uuid == MIC_AUDIO_CHAR_UUID means the descriptor FOR MIC_AUDIO was written.
# So when MIC_AUDIO descriptor is written, we write CAM descriptor AND call LLM.
# Then when CAM descriptor is written, descriptor.characteristic.uuid == CAM_IMAGE_CHAR_UUID handles what?
# Currently there is NO handler for CAM descriptor write!
# BUT what if MIC_AUDIO is written twice?

# Wait! The reason we hear it twice is probably that playBase64Audio sends the PCM. And there might be some race conditions or retries.
# Let's check playBase64Audio.

# Let's change the prompt to avoid "新设备开机了" and fix the trigger logic.
# I will make sure the greeting is only called ONCE by using a flag hasGreeted.

import re

# Add a flag in the class
orig = re.sub(r'(private var isAIThinking = false)', r'\1\n    private var hasGreeted = false', orig)

# Set hasGreeted = false on connect
orig = re.sub(r'(if \(newState == BluetoothProfile\.STATE_CONNECTED\) \{)', r'\1\n                hasGreeted = false', orig)

# Update trigger logic
orig = orig.replace('''// Trigger auto greet when camera descriptor is configured
                runOnUiThread { tvStatus.text = "设备就绪！AI 准备中..." }
                isAIThinking = true
                historyLog.clear()
                callLLMForReply("系统指令：新设备刚开机。请简短地向用户打招呼，并直接问他现在想要做什么任务。注意：收到这条指令请直接进入角色开口，不要回复\\'好的\\'、\\'收到\\'之类的话。")''', 
                '''// Trigger auto greet when camera descriptor is configured
                if (!hasGreeted) {
                    hasGreeted = true
                    runOnUiThread { tvStatus.text = "设备就绪！AI 准备中..." }
                    isAIThinking = true
                    historyLog.clear()
                    callLLMForReply("系统指令：请向用户打招呼，并直接询问现在想要拆解什么任务。语言简短自然，禁止出现像'好的'这种系统性回复，不要提及'开机'、'设备'等字眼。")
                }''')

with open(r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt', 'w', encoding='utf-8') as f:
    f.write(orig)

