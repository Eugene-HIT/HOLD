import requests
import json
import base64
import wave
import io
import struct

url = 'https://open.bigmodel.cn/api/paas/v4/chat/completions'
headers = {
    'Authorization': 'Bearer 6781c79d4db14ec2bb75853a91352491.opzn28MO3bY2dho1',
    'Content-Type': 'application/json'
}
data = {
    "model": "glm-4-voice",
    "messages": [{"role": "user", "content": [{"type": "text", "text": "这段声音听起来应该像是平滑的人声"}]}]
}
response = requests.post(url, headers=headers, json=data)
res_json = response.json()
audio_data = res_json['choices'][0]['message']['audio']['data']
raw_audio = base64.b64decode(audio_data)

idx = raw_audio.find(b'data')
pcm_bytes = raw_audio[idx+8:]
num_samples = len(pcm_bytes) // 2
shorts = struct.unpack('<' + 'h'*num_samples, pcm_bytes)

target_rate = 16000
in_rate = 22050
ratio = in_rate / target_rate
out_len = int(num_samples / ratio)

box_shorts = []
for i in range(out_len):
    start_idx = i * ratio
    end_idx = (i + 1) * ratio
    start_i = int(start_idx)
    end_i = int(end_idx + 0.999) # ceiling
    
    total = 0.0
    weight = 0.0
    for j in range(start_i, end_i):
        if j < num_samples:
            # calculate overlap weight
            w_start = max(start_idx, j)
            w_end = min(end_idx, j + 1)
            w = w_end - w_start
            
            total += shorts[j] * w
            weight += w
            
    val = total / weight if weight > 0 else 0
    val = int(val * 0.35)
    if val > 32767: val = 32767
    if val < -32768: val = -32768
    box_shorts.append(val)

with wave.open('box_test.wav', 'wb') as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(16000)
    w.writeframes(struct.pack('<' + 'h'*len(box_shorts), *box_shorts))
print("Done Boxcar test.")
