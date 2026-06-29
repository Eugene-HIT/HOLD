import requests
import json
import base64

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
                    "text": "你好"
                }
            ]
        }
    ]
}

response = requests.post(url, headers=headers, json=data)
res_json = response.json()
if 'choices' in res_json:
    audio_data = res_json['choices'][0]['message']['audio']['data']
    raw_audio = base64.b64decode(audio_data)
    print("Total len:", len(raw_audio))
    # search for data chunk
    idx = raw_audio.find(b'data')
    if idx != -1:
        print("data chunk found at:", idx)
        size = raw_audio[idx+4] | (raw_audio[idx+5] << 8) | (raw_audio[idx+6] << 16) | (raw_audio[idx+7] << 24)
        print("data size:", size)
        print("diff:", len(raw_audio) - (idx + 8 + size))
