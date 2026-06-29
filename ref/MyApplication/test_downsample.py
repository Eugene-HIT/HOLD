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
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "这是一段测试长语言，看看半秒钟之后会不会出现爆音或者破音的问题"
                }
            ]
        }
    ]
}

response = requests.post(url, headers=headers, json=data)
res_json = response.json()
audio_data = res_json['choices'][0]['message']['audio']['data']
raw_audio = base64.b64decode(audio_data)

# Extract PCM
idx = raw_audio.find(b'data')
pcm_bytes = raw_audio[idx+8:]

# Parse shorts
num_samples = len(pcm_bytes) // 2
shorts = struct.unpack('<' + 'h'*num_samples, pcm_bytes)

# Downsample Nearest Neighbor
target_rate = 16000
in_rate = 22050
ratio = in_rate / target_rate
out_len = int(num_samples / ratio)

nn_shorts = []
for i in range(out_len):
    in_idx = int(i * ratio)
    if in_idx < num_samples:
        nn_shorts.append(shorts[in_idx])

with wave.open('nn_test.wav', 'wb') as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(16000)
    w.writeframes(struct.pack('<' + 'h'*len(nn_shorts), *nn_shorts))

# Downsample Linear Interpolation
li_shorts = []
for i in range(out_len):
    exact_idx = i * ratio
    left_idx = int(exact_idx)
    right_idx = min(left_idx + 1, num_samples - 1)
    fraction = exact_idx - left_idx
    
    left_val = shorts[left_idx]
    right_val = shorts[right_idx]
    
    interp = left_val + fraction * (right_val - left_val)
    val = int(interp)
    if val > 32767: val = 32767
    if val < -32768: val = -32768
    li_shorts.append(val)

with wave.open('li_test.wav', 'wb') as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(16000)
    w.writeframes(struct.pack('<' + 'h'*len(li_shorts), *li_shorts))
