import re
with open('D:/ADHD/MyApplication/app/src/main/java/com/example/myapplication/MainActivity.kt', 'r', encoding='utf-8') as f:
    text = f.read()

pattern = r'if \(data\[0\]\.toInt\(\) == 0x02\) \{\s*android\.util\.Log\.i\("AI_DEBUG", "HARDWARE LONG PRESS INTERRUPT"\)'
replacement = 'if (data[0].toInt() == 0x02) {\n                        ++currentTurnId\n                        android.util.Log.i("AI_DEBUG", "HARDWARE LONG PRESS INTERRUPT")'

if re.search(pattern, text):
    text = re.sub(pattern, replacement, text)
    with open('D:/ADHD/MyApplication/app/src/main/java/com/example/myapplication/MainActivity.kt', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Fixed 0x02!")
else:
    print("Pattern not found!")
