import sys

xml_path = r'D:\ADHD\MyApplication\app\src\main\res\layout\activity_main.xml'
with open(xml_path, 'rb') as f:
    raw = f.read()

print('XML raw bytes of some text:')
print(raw[raw.find(b'android:text=') : raw.find(b'android:text=')+100])
