import sys

path = r'D:/ADHD/MyApplication/app/src/main/java/com/example/myapplication/MainActivity.kt'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.read().splitlines()

for i, line in enumerate(lines):
    if "callLLMForReply(\"系统指令" in line:
        if "currentInterruptSessionId" not in line:
            lines[i] = line.replace('")', '", currentInterruptSessionId)')

with open(path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print("Fixed line 481")
