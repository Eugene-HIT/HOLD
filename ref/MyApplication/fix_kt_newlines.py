kt_path = 'D:/ADHD/MyApplication/app/src/main/java/com/example/myapplication/MainActivity.kt'
with open(kt_path, 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace('\\\\n', '\\n')
with open(kt_path, 'w', encoding='utf-8') as f:
    f.write(code)
print('Fixed newlines')