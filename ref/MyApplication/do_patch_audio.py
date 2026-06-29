import re

file_path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Lowering the audio threshold
content = re.sub(r'if \(maxEnergy > 2000\)', 'if (maxEnergy > 800)', content)

# Updating the delay to 5 seconds.
content = re.sub(r'Log\.i\(\"AI_DEBUG\", \"Audio play complete\. Resetting AI\.\"\)[\s\r\n]*resetAI\(\d+\)', 'Log.i("AI_DEBUG", "Audio play complete. Resetting AI.")\n                        resetAI(5000)', content)

# Update resetAI after streamPcmToEsp32 finishes
content = re.sub(r'Log\.i\(\"BLE_DEBUG\", \"Sent PCM to ESP32\.\"\)[\s\r\n]*resetAI\(\d+\)', 'Log.i("BLE_DEBUG", "Sent PCM to ESP32.")\n                resetAI(5000)', content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
