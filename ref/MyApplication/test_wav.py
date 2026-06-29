import requests
import json
import base64
import wave
import io

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
    
    with io.BytesIO(raw_audio) as f:
        with wave.open(f, 'rb') as w:
            print("Channels:", w.getnchannels())
            print("Sample width:", w.getsampwidth())
            print("Framerate:", w.getframerate())
            print("Nframes:", w.getnframes())
            print("Comptype:", w.getcomptype())
            print("Compname:", w.getcompname())
