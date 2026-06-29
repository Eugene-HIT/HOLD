import requests
import json
import base64

url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
headers = {"Authorization": "Bearer 6781c79d4db14ec2bb75853a91352491.opzn28MO3bY2dho1"}

payload = {
    "model": "glm-4-voice",
    "messages": [
        {
            "role": "user",
            "content": [{"type": "text", "text": "你好"}]
        }
    ]
}

res = requests.post(url, json=payload, headers=headers)
data = res.json()
audio_b64 = data['choices'][0]['message']['audio']['data']
audio_bytes = base64.b64decode(audio_b64)

with open('test_audio.wav', 'wb') as f:
    f.write(audio_bytes)

print("Size:", len(audio_bytes))
print("Header start:", audio_bytes[:12])
