import re
content = open(r'D:\ADHD\MyApplication\app\src\main\res\layout\activity_main.xml', encoding='utf-8').read()
match = re.search(r'(<ScrollView\s+android:id="@+id/debug_scroll".*?</ScrollView>)', content, re.DOTALL)
if match: 
    print(match.group(1)[:500])
    print('...\n')
    print(match.group(1)[-500:])
else:
    print("No match")