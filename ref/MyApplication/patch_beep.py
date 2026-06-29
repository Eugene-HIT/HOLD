# -*- coding: utf-8 -*-
import codecs
import re

path = r'D:\ADHD\Xiao_Sense_MVP\src\main.cpp'
with codecs.open(path, 'r', 'utf-8') as f:
    text = f.read()

pattern = r'void produce_beep\(\) \{.*?\}\s*\}'

replacement = '''#include <math.h>

void produce_beep() {
    int16_t beep_buf[320]; // 20ms of 16kHz audio
    // 设置较低的音量(振幅从8000降到1500)，不仅不刺耳，还能避免硬件在大电流下因电压骤降导致重启！
    float max_amplitude = 1500.0f;
    float total_duration = 0.2f; // 发声 0.2 秒 (200ms)

    // 播放 10 次 320 sample 的片段 = 3200 sample (16000Hz 下正好是 200ms)
    for(int loop=0; loop<10; loop++) {
        for(int i=0; i<320; i++) {
            // 计算当前对应的时间（秒）
            float t = (loop * 320.0f + i) / 16000.0f;
            
            // 生成 600Hz 的温柔正弦波（原来是高频率刺耳方波）
            float val = max_amplitude * sin(2.0f * (float)M_PI * 600.0f * t);
            
            // 音量包络：从 1.0 线性减弱到 0.0，形成如铃声般渐弱的听感
            float envelope = 1.0f - (t / total_duration);
            if (envelope < 0.0f) envelope = 0.0f;
            
            beep_buf[i] = (int16_t)(val * envelope);
        }
        xRingbufferSend(spkRingBuf, beep_buf, sizeof(beep_buf), pdMS_TO_TICKS(50));
    }
}'''

text = re.sub(pattern, replacement, text, flags=re.DOTALL)

with codecs.open(path, 'w', 'utf-8') as f:
    f.write(text)

print("Beep replaced successfully.")
