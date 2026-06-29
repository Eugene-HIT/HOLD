kt_path = 'D:/ADHD/MyApplication/app/src/main/java/com/example/myapplication/MainActivity.kt'
with open(kt_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    
start = -1
for i, line in enumerate(lines):
    if 'private fun handleCharacteristicChange' in line:
        start = i
        break
if start != -1:
    print(''.join(lines[start:start+120]))