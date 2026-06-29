import re

xml_path = r'D:\ADHD\MyApplication\app\src\main\res\layout\activity_main.xml'
with open(xml_path, 'r', encoding='utf-8', errors='ignore') as f:
    xml_content = f.read()

# Fix layout weight/width for the title to absolutely guarantee it shows
xml_content = xml_content.replace('android:layout_width="0dp"', 'android:layout_width="match_parent"').replace('android:layout_weight="1"', '')

with open(xml_path, 'w', encoding='utf-8') as f:
    f.write(xml_content)
