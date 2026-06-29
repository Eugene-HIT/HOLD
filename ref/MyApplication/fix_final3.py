import re

kt_path = r'D:\ADHD\MyApplication\app\src\main\java\com\example\myapplication\MainActivity.kt'
with open(kt_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Soften the AI volume to exactly match native microphone recording levels (approx 40% volume of pristine max wave), eliminating hardware amp crash/choppiness
old_code = '''                            val interp = leftVal + fraction * (rightVal - leftVal)
                            var v = interp.toInt()
                            if (v > 32767) v = 32767
                            if (v < -32768) v = -32768
                            outShorts[i] = v.toShort()'''

new_code = '''                            val interp = leftVal + fraction * (rightVal - leftVal)
                            // User's PTT (mic) is naturally very quiet (around 30-40% scale).
                            // Zhipu AI TTS generates audio at literal 100% full scale. When this full scale hits ESP32's * 2 multiplier, it completely destroys the I2S hardware buffer and becomes pure static/choppy noise.
                            // We MUST scale it down to match PTT levels!
                            var v = (interp * 0.35).toInt() 
                            if (v > 32767) v = 32767
                            if (v < -32768) v = -32768
                            outShorts[i] = v.toShort()'''

if old_code in text:
    text = text.replace(old_code, new_code)
    with open(kt_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print("Replaced volume scaling successfully!")
else:
    print("Old volume scaling code not found!")
