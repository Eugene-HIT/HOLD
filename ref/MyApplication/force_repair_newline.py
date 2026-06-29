kt_path = 'D:/ADHD/MyApplication/app/src/main/java/com/example/myapplication/MainActivity.kt'
with open(kt_path, 'r', encoding='utf-8') as f:
    kt_code = f.read()

import re
kt_code = re.sub(r'isInterrupted = false\\n.*?writeSemaphore\.release\(\) // Allow the first chunk to proceed immediately', 
                 'isInterrupted = false\n                writeSemaphore.release() // Allow the first chunk to proceed immediately', kt_code)

kt_code = re.sub(r'while \(offset < audioBytes\.size\) \{\\n.*?if \(isInterrupted\) break', 
                 'while (offset < audioBytes.size) {\n                    if (isInterrupted) break', kt_code)

with open(kt_path, 'w', encoding='utf-8') as f:
    f.write(kt_code)
print("Newlines fixed!")