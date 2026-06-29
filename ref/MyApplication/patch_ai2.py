# -*- coding: utf-8 -*-
import re

file_path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Clean up multiple injections
content = re.sub(r'(\s*// Trigger auto greet when camera descriptor is configured\s*runOnUiThread \{ tvStatus\.text = "设备就绪！AI 准备中\.\.\." \}\s*isAIThinking = true\s*historyLog\.clear\(\)\s*callLLMForReply\("系统指令[^\)]+"\)\n)+', 
                 r'\n                // Trigger auto greet when camera descriptor is configured\n                runOnUiThread { tvStatus.text = "设备就绪！AI 准备中..." }\n                isAIThinking = true\n                historyLog.clear()\n                callLLMForReply("系统指令：新设备刚开机。请简短地向用户打招呼，并直接问他现在想要做什么任务。注意：收到这条指令请直接进入角色开口，不要回复\'好的\'、\'收到\'之类的话。")\n', content)

# 2. Add startScan to onCreate
if "startScan()" not in content.split("override fun onCreate")[1].split("}")[0]:
    content = re.sub(
        r'(btnScan\.setOnClickListener \{\s*)',
        r'// Auto scan on start\n        Handler(Looper.getMainLooper()).postDelayed({ startScan() }, 1000)\n\n        \1',
        content
    )

# 3. Disconnect trigger re-scan
content = content.replace(
    'runOnUiThread { tvStatus.text = "连接断开" }',
    'runOnUiThread { tvStatus.text = "连接断开，正在重新扫描..." }\n                Handler(Looper.getMainLooper()).postDelayed({ startScan() }, 2000)'
)

# 4. Auto connect on find
content = content.replace(
    '''if (name.contains("MBF") && !foundDevices.any { it.address == device.address }) {''',
    '''if (name.contains("MBF") && !foundDevices.any { it.address == device.address }) {
                // Auto connect to this device
                runOnUiThread { tvStatus.text = "发现 ，自动连接中..." }
                stopScan()
                connectToDevice(device)
'''
)


with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
